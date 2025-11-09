"""
FastMCP Server for BacklineMD AI Agents
Provides tools for patient management, appointments, claims, documents, consent forms, and tasks
"""

import asyncio
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("BacklineMD Agent Tools")

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.backlinemd

# Default tenant for demo
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "hackathon-demo")

# Tool permissions for agents
TOOL_PERMISSIONS = {
    "intake": [
        "find_or_create_patient",
        "update_patient",
        "get_patient",
        "create_document",
        "get_documents",
        "update_document",
        "create_consent_form",
        "get_consent_forms",
        "update_consent_form",
        "send_consent_forms",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "doc_extraction": [
        "get_patient",
        "update_patient",
        "get_documents",
        "update_document",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "care_taker": [
        "get_patient",
        "update_patient",
        "get_appointments",
        "create_appointment",
        "update_appointment",
        "delete_appointment",
        "get_documents",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "insurance": [
        "get_patient",
        "get_insurance_claims",
        "create_insurance_claim",
        "update_insurance_claim",
        "get_documents",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "admin": [
        "get_patients",
        "find_or_create_patient",
        "update_patient",
        "get_patient",
        "create_task",
        "update_task",
        "get_tasks",
        "get_appointments",
        "create_appointment",
        "update_appointment",
        "delete_appointment",
        "get_insurance_claims",
    ],
    "voice_agent": [
        "find_or_create_patient",
        "update_patient",
        "get_appointments",
        "create_appointment",
        "update_appointment",
        "delete_appointment",
    ],
}


# ==================== PATIENT TOOLS ====================

@mcp.tool()
async def get_patients() -> List[Dict[str, Any]]:
    """
    Get all patients in the system.
    """
    patients = await db.patients.find({"tenant_id": DEFAULT_TENANT}).to_list(length=100)
    return [
        {
            "patient_id": patient["_id"],
            "first_name": patient["first_name"],
            "last_name": patient["last_name"],
        }
        for patient in patients
    ]

@mcp.tool()
async def find_or_create_patient(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    dob: Optional[str] = None,
    gender: Optional[str] = None,
    insurance_company: Optional[str] = None,
    insurance_policy_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Find an existing patient or create a new one.

    Args:
        name: Full name (will be split into first_name and last_name if provided)
        email: Patient email address
        phone: Patient phone number
        first_name: Patient first name (overrides name if provided)
        last_name: Patient last name (overrides name if provided)
        dob: Date of birth in YYYY-MM-DD format
        gender: Patient gender (Male, Female, Other)
        insurance_company: Insurance company name
        insurance_policy_number: Insurance policy number

    Returns:
        Dict with patient_id and patient details
    """
    # Try to find existing patient
    query = {"tenant_id": DEFAULT_TENANT}

    if email:
        query["contact.email"] = email
    elif phone:
        query["contact.phone"] = phone

    existing = await db.patients.find_one(query)

    if existing:
        return {
            "patient_id": existing["_id"],
            "name": f"{existing.get('first_name', '')} {existing.get('last_name', '')}".strip() or existing.get("name", ""),
            "email": existing["contact"]["email"],
            "phone": existing["contact"]["phone"],
            "mrn": existing["mrn"],
            "status": "existing",
        }

    # Create new patient
    if not name:
        return {"error": "name is required to create a patient"}

    patient_id = str(uuid.uuid4())
    mrn = f"MRN{random.randint(100000, 999999)}"

    # Parse name into first_name and last_name
    name_parts = name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
    full_name = f"{first_name} {last_name}".strip()

    # Generate search n-grams
    ngrams = [
        full_name.lower().replace(" ", "")[i : i + 3]
        for i in range(len(full_name.replace(" ", "")) - 2)
    ]

    # Initialize treatment timeline to first stage
    treatment_timeline = [
        {
            "title": "Initial Consultation",
            "status": "pending",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "description": "Initial consultation pending"
        }
    ]

    # Calculate age from DOB if provided
    age = None
    if dob:
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        except:
            pass

    patient = {
        "_id": patient_id,
        "tenant_id": DEFAULT_TENANT,
        "mrn": mrn,
        "first_name": first_name,
        "last_name": last_name,
        "name": full_name,
        "dob": dob or "1990-01-01",
        "age": age,  # Store calculated age
        "gender": gender or "Unknown",
        "contact": {
            "email": email or f"{first_name.lower()}@example.com",
            "phone": phone or "555-0000",
            "address": {},
        },
        "insurance": {
            "company": insurance_company,
            "policy_number": insurance_policy_number,
        },
        "preconditions": [],
        "flags": [],
        "latest_vitals": {},
        "height": None,  # Will be set when available
        "weight": None,  # Will be set when available
        "blood_type": None,  # Will be set when available
        "profile_image": None,
        "status": "Intake In Progress",
        "treatment_timeline": treatment_timeline,
        "ai_summary": None,  # Empty initially, will be generated on demand
        "tasks_count": 0,
        "appointments_count": 0,
        "flagged_count": 0,
        "search": {"ngrams": ngrams},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }

    await db.patients.insert_one(patient)

    # Step 1: Patient is created ✓ (done above)

    # Step 2: Generate AI summary for the patient
    try:
        # Generate a simple summary for new patient
        preconditions_text = ", ".join(patient.get("preconditions", [])) if patient.get("preconditions") else "no documented preconditions"
        age_text = f"{age}-year-old" if age else "patient"
        summary_text = f"{age_text} {patient.get('gender', 'Unknown').lower()} patient with {preconditions_text}. Currently in intake process. Initial consultation pending. Medical records collection in progress."
        
        # Store summary in patient document
        await db.patients.update_one(
            {"_id": patient_id, "tenant_id": DEFAULT_TENANT},
            {
                "$set": {
                    "ai_summary": summary_text,
                    "ai_summary_generated_at": datetime.now(timezone.utc),
                }
            }
        )
    except Exception as e:
        print(f"Warning: Failed to generate AI summary: {e}")

    # Get form templates to create default consent forms
    form_templates = await db.form_templates.find({"tenant_id": DEFAULT_TENANT}).to_list(length=10)
    
    # Default 4 consent forms if no templates exist
    default_forms = [
        {"name": "Insurance Information Release", "description": "Authorization to release medical information to insurance provider"},
        {"name": "Medical Records Request - Lab", "description": "Request medical records from external laboratory"},
        {"name": "HIPAA Authorization Form", "description": "HIPAA compliant authorization for information disclosure"},
        {"name": "Consent for Treatment", "description": "Patient consent for proposed treatment plan"},
    ]
    
    # Use templates if available, otherwise use default forms
    forms_to_create = form_templates if form_templates else default_forms
    
    # Create default consent forms with "to_do" status (always create 4 forms)
    created_forms = []
    for i, template in enumerate(forms_to_create[:4]):  # Always create exactly 4 forms
        consent_form_id = str(uuid.uuid4())
        consent_form = {
            "_id": consent_form_id,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "patient_name": full_name,
            "template_id": template.get("_id") or f"template-{i}",
            "form_type": template.get("name", "consent"),
            "title": template.get("name", "Consent Form"),
            "status": "to_do",
            "sent_via": None,
            "sent_at": None,
            "signed_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await db.consent_forms.insert_one(consent_form)
        created_forms.append(consent_form_id)

    # Create AI tasks for document extraction, care taker, and intake agents
    tasks_created = []
    
    # Task 1: Document extraction AI agent - set to TODO (open)
    doc_extraction_task_id = str(uuid.uuid4())
    doc_extraction_task = {
        "_id": doc_extraction_task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": DEFAULT_TENANT,
        "source": "agent",
        "kind": "document_review",
        "title": f"Extract and Review Patient Documents - {full_name}",
        "description": f"New patient {full_name} has been created. Please review and extract information from any uploaded documents. Ensure all medical records are properly processed and indexed.",
        "patient_id": patient_id,
        "patient_name": full_name,
        "assigned_to": "AI - Document Extractor",
        "agent_type": "doc_extraction",
        "priority": "medium",
        "state": "open",  # TODO state
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }
    await db.tasks.insert_one(doc_extraction_task)
    tasks_created.append(doc_extraction_task_id)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})

    # Task 2: Care taker agent - send consent forms
    care_taker_task_id = str(uuid.uuid4())
    care_taker_task = {
        "_id": care_taker_task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": DEFAULT_TENANT,
        "source": "agent",
        "kind": "consent_forms",
        "title": f"Send Consent Forms to Patient - {full_name}",
        "description": f"New patient {full_name} has been created. Please send consent forms (Insurance Information Release, Medical Records Request, HIPAA Authorization, and Consent for Treatment) to the patient via email or DocuSign.",
        "patient_id": patient_id,
        "patient_name": full_name,
        "assigned_to": "Dr. James O'Brien",
        "agent_type": "care_taker",
        "priority": "medium",
        "state": "open",  # TODO state
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }
    await db.tasks.insert_one(care_taker_task)
    tasks_created.append(care_taker_task_id)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})

    # Task 3: Intake agent - collect medical records (set to in_progress)
    intake_task_id = str(uuid.uuid4())
    intake_task = {
        "_id": intake_task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": DEFAULT_TENANT,
        "source": "agent",
        "kind": "medical_records_collection",
        "title": f"Collect Medical Records - {full_name}",
        "description": f"New patient {full_name} has been created. Please collect and review medical records including medical history, lab results, imaging reports, and any previous treatment documentation.",
        "patient_id": patient_id,
        "patient_name": full_name,
        "assigned_to": "AI - Intake Agent",
        "agent_type": "intake",
        "priority": "high",
        "state": "in_progress",  # Set to in_progress as requested
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }
    await db.tasks.insert_one(intake_task)
    tasks_created.append(intake_task_id)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})

    # Step 3: Tasks are created ✓ (done above)

    # Step 4: Send welcome email synchronously (hardcoded email for now)
    email_result = None
    try:
        from composio_integration import send_email_via_composio
        # Hardcode email for now as requested
        patient_email = "mnvsk97@gmail.com"  # Hardcoded email
        welcome_subject = "Welcome to BacklineMD - Your Healthcare Journey Begins"
        welcome_body = f"""
Dear {first_name},

Welcome to BacklineMD! We're excited to have you as part of our healthcare family.

Your patient record has been created successfully:
- Patient ID: {mrn}
- Name: {full_name}
- Email: {patient["contact"]["email"]}
- Phone: {patient["contact"]["phone"]}

Our team is here to support you throughout your healthcare journey. You can expect:
- Personalized care from our experienced medical team
- Easy access to your medical records and appointments
- Secure communication through our patient portal

If you have any questions or need assistance, please don't hesitate to reach out to us.

Best regards,
The BacklineMD Team
        """
        # Send email synchronously (wait for it)
        email_result = await send_email_via_composio(
            to_email=patient_email,
            subject=welcome_subject,
            body=welcome_body,
            user_id="backlinemd-system"
        )
        print(f"Email sent result: {email_result}")
    except Exception as e:
        # Log error but don't fail patient creation
        print(f"Warning: Failed to send welcome email: {e}")
        email_result = {"success": False, "error": str(e)}

    return {
        "patient_id": patient_id,
        "name": full_name,
        "first_name": first_name,
        "last_name": last_name,
        "email": patient["contact"]["email"],
        "phone": patient["contact"]["phone"],
        "mrn": mrn,
        "status": "created",
        "insurance_company": insurance_company,
        "insurance_policy_number": insurance_policy_number,
        "consent_forms_created": len(created_forms),
        "tasks_created": len(tasks_created),
        "email_sent": email_result.get("success", False) if email_result else False,
    }


@mcp.tool()
async def update_patient(
    patient_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    dob: Optional[str] = None,
    gender: Optional[str] = None,
    address: Optional[Dict[str, str]] = None,
    preconditions: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update patient information.

    Args:
        patient_id: Patient ID to update
        first_name: New first name
        last_name: New last name
        email: New email
        phone: New phone number
        dob: New date of birth
        gender: New gender
        address: New address dict
        preconditions: List of medical preconditions
        status: Patient status (Active, Inactive, etc.)

    Returns:
        Dict with success status and updated patient info
    """
    update_fields = {}

    if first_name:
        update_fields["first_name"] = first_name
    if last_name:
        update_fields["last_name"] = last_name
    if email:
        update_fields["contact.email"] = email
    if phone:
        update_fields["contact.phone"] = phone
    if dob:
        update_fields["dob"] = dob
    if gender:
        update_fields["gender"] = gender
    if address:
        update_fields["contact.address"] = address
    if preconditions is not None:
        update_fields["preconditions"] = preconditions
    if status:
        update_fields["status"] = status

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.patients.update_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Patient not found"}

    patient = await db.patients.find_one({"_id": patient_id})

    return {
        "success": True,
        "patient_id": patient_id,
        "updated_fields": list(update_fields.keys()),
        "patient": {
            "first_name": patient["first_name"],
            "last_name": patient["last_name"],
            "email": patient["contact"]["email"],
            "phone": patient["contact"]["phone"],
            "status": patient.get("status", "Active"),
        },
    }


# ==================== APPOINTMENT TOOLS ====================


@mcp.tool()
async def get_appointments(
    patient_id: Optional[str] = None,
    date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get appointments for a patient or date range.

    Args:
        patient_id: Filter by patient ID
        date: Filter by date (YYYY-MM-DD) or 'today'
        status: Filter by status (scheduled, completed, cancelled)
        limit: Maximum number of results

    Returns:
        List of appointment dicts
    """
    query = {"tenant_id": DEFAULT_TENANT}

    if patient_id:
        query["patient_id"] = patient_id

    if status:
        query["status"] = status

    if date == "today":
        today = datetime.now(timezone.utc).date()
        query["starts_at"] = {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()),
        }
    elif date:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        query["starts_at"] = {
            "$gte": datetime.combine(date_obj, datetime.min.time()),
            "$lt": datetime.combine(date_obj + timedelta(days=1), datetime.min.time()),
        }

    cursor = db.appointments.find(query).sort("starts_at", 1).limit(limit)
    appointments = await cursor.to_list(length=limit)

    # Batch fetch patients
    patient_ids = list(set(apt["patient_id"] for apt in appointments))
    patients_cursor = db.patients.find({"_id": {"$in": patient_ids}})
    patients_list = await patients_cursor.to_list(length=len(patient_ids))
    patients_map = {p["_id"]: p for p in patients_list}

    result = []
    for apt in appointments:
        patient = patients_map.get(apt["patient_id"])
        result.append(
            {
                "appointment_id": apt["_id"],
                "patient_id": apt["patient_id"],
                "patient_name": (
                    f"{patient['first_name']} {patient['last_name']}"
                    if patient
                    else "Unknown"
                ),
                "type": apt["type"],
                "starts_at": apt["starts_at"].isoformat(),
                "ends_at": apt["ends_at"].isoformat(),
                "status": apt["status"],
                "location": apt.get("location"),
                "title": apt.get("title"),
            }
        )

    return result


@mcp.tool()
async def create_appointment(
    patient_id: str,
    type: str,
    starts_at: str,
    ends_at: str,
    title: Optional[str] = None,
    location: Optional[str] = None,
    provider_id: Optional[str] = "default-provider",
) -> Dict[str, Any]:
    """
    Create a new appointment.

    Args:
        patient_id: Patient ID
        type: Appointment type (checkup, consultation, follow-up, etc.)
        starts_at: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        ends_at: End time in ISO format
        title: Appointment title
        location: Appointment location
        provider_id: Provider/doctor ID

    Returns:
        Dict with appointment_id and details
    """
    # Verify patient exists
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )
    if not patient:
        return {"error": "Patient not found"}

    appointment_id = str(uuid.uuid4())

    appointment = {
        "_id": appointment_id,
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "provider_id": provider_id,
        "type": type,
        "title": title or f"{type.title()} Appointment",
        "starts_at": datetime.fromisoformat(starts_at.replace("Z", "+00:00")),
        "ends_at": datetime.fromisoformat(ends_at.replace("Z", "+00:00")),
        "location": location or "Main Office",
        "status": "scheduled",
        "google_calendar": {
            "event_id": f"mock-event-{appointment_id[:8]}",
            "calendar_id": "primary",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Use transaction
    if client:
        async with client.start_session() as session:
            async with session.start_transaction():
                await db.appointments.insert_one(appointment, session=session)
                await db.patients.update_one(
                    {"_id": patient_id},
                    {"$inc": {"appointments_count": 1}},
                    session=session,
                )
    else:
        await db.appointments.insert_one(appointment)
        await db.patients.update_one(
            {"_id": patient_id}, {"$inc": {"appointments_count": 1}}
        )

    return {
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "type": type,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "status": "scheduled",
        "message": "Appointment created successfully",
    }


@mcp.tool()
async def update_appointment(
    appointment_id: str,
    status: Optional[str] = None,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    location: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an existing appointment.

    Args:
        appointment_id: Appointment ID to update
        status: New status (scheduled, completed, cancelled, no-show)
        starts_at: New start time in ISO format
        ends_at: New end time in ISO format
        location: New location
        title: New title

    Returns:
        Dict with success status
    """
    update_fields = {}

    if status:
        update_fields["status"] = status
    if starts_at:
        update_fields["starts_at"] = datetime.fromisoformat(
            starts_at.replace("Z", "+00:00")
        )
    if ends_at:
        update_fields["ends_at"] = datetime.fromisoformat(
            ends_at.replace("Z", "+00:00")
        )
    if location:
        update_fields["location"] = location
    if title:
        update_fields["title"] = title

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.appointments.update_one(
        {"_id": appointment_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Appointment not found"}

    return {
        "success": True,
        "appointment_id": appointment_id,
        "updated_fields": list(update_fields.keys()),
    }


@mcp.tool()
async def delete_appointment(appointment_id: str) -> Dict[str, Any]:
    """
    Delete/cancel an appointment.

    Args:
        appointment_id: Appointment ID to delete

    Returns:
        Dict with success status
    """
    # Get appointment to find patient
    appointment = await db.appointments.find_one(
        {"_id": appointment_id, "tenant_id": DEFAULT_TENANT}
    )

    if not appointment:
        return {"error": "Appointment not found"}

    # Use transaction
    if client:
        async with client.start_session() as session:
            async with session.start_transaction():
                await db.appointments.delete_one({"_id": appointment_id}, session=session)
                await db.patients.update_one(
                    {"_id": appointment["patient_id"]},
                    {"$inc": {"appointments_count": -1}},
                    session=session,
                )
    else:
        await db.appointments.delete_one({"_id": appointment_id})
        await db.patients.update_one(
            {"_id": appointment["patient_id"]}, {"$inc": {"appointments_count": -1}}
        )

    return {
        "success": True,
        "appointment_id": appointment_id,
        "message": "Appointment deleted",
    }


# ==================== INSURANCE CLAIM TOOLS ====================


@mcp.tool()
async def get_insurance_claims(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get insurance claims.

    Args:
        patient_id: Filter by patient ID
        status: Filter by status (pending, submitted, approved, denied)
        limit: Maximum number of results

    Returns:
        List of claim dicts
    """
    query = {"tenant_id": DEFAULT_TENANT}

    if patient_id:
        query["patient_id"] = patient_id
    if status:
        query["status"] = status

    cursor = db.claims.find(query).sort("last_event_at", -1).limit(limit)
    claims = await cursor.to_list(length=limit)

    return [
        {
            "claim_id": claim["_id"],
            "claim_id_display": claim["claim_id"],
            "patient_id": claim["patient_id"],
            "patient_name": claim["patient_name"],
            "insurance_provider": claim["insurance_provider"],
            "amount": claim["amount_display"],
            "status": claim["status"],
            "submitted_date": claim["submitted_date"],
            "procedure_code": claim.get("procedure_code"),
            "diagnosis_code": claim.get("diagnosis_code"),
            "description": claim.get("description"),
        }
        for claim in claims
    ]


@mcp.tool()
async def create_insurance_claim(
    patient_id: str,
    amount: float,
    insurance_provider: str,
    procedure_code: str,
    diagnosis_code: str,
    service_date: str,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new insurance claim.

    Args:
        patient_id: Patient ID
        amount: Claim amount in dollars
        insurance_provider: Insurance provider name
        procedure_code: CPT/procedure code
        diagnosis_code: ICD diagnosis code
        service_date: Service date (YYYY-MM-DD)
        description: Claim description

    Returns:
        Dict with claim_id and details
    """
    # Verify patient exists
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )
    if not patient:
        return {"error": "Patient not found"}

    claim_id = str(uuid.uuid4())
    claim_id_display = f"C{random.randint(10000, 99999)}"

    claim = {
        "_id": claim_id,
        "claim_id": claim_id_display,
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "insurance_provider": insurance_provider,
        "amount": int(amount * 100),  # Store in cents
        "amount_display": amount,
        "procedure_code": procedure_code,
        "diagnosis_code": diagnosis_code,
        "service_date": service_date,
        "submitted_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": description or f"Claim for {procedure_code}",
        "status": "pending",
        "last_event_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.claims.insert_one(claim)

    # Create initial event
    event = {
        "_id": str(uuid.uuid4()),
        "tenant_id": DEFAULT_TENANT,
        "claim_id": claim_id,
        "event_type": "submitted",
        "description": f"Claim submitted to {insurance_provider} for ${amount:.2f}",
        "at": datetime.now(timezone.utc),
        "time": datetime.now(timezone.utc).strftime("%I:%M %p"),
        "created_at": datetime.now(timezone.utc),
    }

    await db.claim_events.insert_one(event)

    return {
        "claim_id": claim_id,
        "claim_id_display": claim_id_display,
        "patient_id": patient_id,
        "amount": amount,
        "status": "pending",
        "message": "Claim created successfully",
    }


@mcp.tool()
async def update_insurance_claim(
    claim_id: str,
    amount: Optional[float] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update an insurance claim.

    Args:
        claim_id: Claim ID to update
        amount: New claim amount
        status: New status (pending, submitted, approved, denied)
        reason: Reason for update (will create event)

    Returns:
        Dict with success status
    """
    update_fields = {}

    if amount is not None:
        update_fields["amount"] = int(amount * 100)
        update_fields["amount_display"] = amount
    if status:
        update_fields["status"] = status
        update_fields["last_event_at"] = datetime.now(timezone.utc)

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.claims.update_one(
        {"_id": claim_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Claim not found"}

    # Create event if status changed
    if status:
        event = {
            "_id": str(uuid.uuid4()),
            "tenant_id": DEFAULT_TENANT,
            "claim_id": claim_id,
            "event_type": status,
            "description": reason or f"Claim status changed to {status}",
            "at": datetime.now(timezone.utc),
            "time": datetime.now(timezone.utc).strftime("%I:%M %p"),
            "created_at": datetime.now(timezone.utc),
        }
        await db.claim_events.insert_one(event)

    return {
        "success": True,
        "claim_id": claim_id,
        "updated_fields": list(update_fields.keys()),
    }


# ==================== DOCUMENT TOOLS ====================


@mcp.tool()
async def create_document(
    patient_id: str,
    kind: str,
    filename: str,
    mime_type: str,
    file_url: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a document record for a patient.

    Args:
        patient_id: Patient ID
        kind: Document kind (lab, imaging, medical_history, summary, consent_form)
        filename: Original filename
        mime_type: MIME type (application/pdf, image/png, etc.)
        file_url: URL to the file (optional, can be generated)
        extracted_data: Pre-extracted data from the document

    Returns:
        Dict with document_id and details
    """
    # Verify patient exists
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )
    if not patient:
        return {"error": "Patient not found"}

    document_id = str(uuid.uuid4())

    document = {
        "_id": document_id,
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "kind": kind,
        "file": {
            "url": file_url or f"/uploads/{document_id}/{filename}",
            "name": filename,
            "mime": mime_type,
            "size": 0,
            "sha256": f"mock-hash-{document_id[:8]}",
        },
        "ocr": {"done": False, "engine": None},
        "extracted": extracted_data or {},
        "status": "uploaded" if not extracted_data else "ingested",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.documents.insert_one(document)

    return {
        "document_id": document_id,
        "patient_id": patient_id,
        "kind": kind,
        "status": document["status"],
        "message": "Document created successfully",
    }


@mcp.tool()
async def update_document(
    document_id: str,
    status: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update a document's status or extracted data.

    Args:
        document_id: Document ID to update
        status: New status (uploaded, ingesting, ingested, not_ingested, approved, rejected)
        extracted_data: Extracted data to add/update

    Returns:
        Dict with success status
    """
    update_fields = {}

    if status:
        update_fields["status"] = status
    if extracted_data:
        update_fields["extracted"] = extracted_data

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.documents.update_one(
        {"_id": document_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Document not found"}

    return {
        "success": True,
        "document_id": document_id,
        "updated_fields": list(update_fields.keys()),
    }


@mcp.tool()
async def get_documents(
    patient_id: Optional[str] = None,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get documents filtered by patient, kind, or status.

    Args:
        patient_id: Filter by patient ID
        kind: Filter by document kind
        status: Filter by status
        limit: Maximum number of results

    Returns:
        List of document dicts
    """
    query = {"tenant_id": DEFAULT_TENANT}

    if patient_id:
        query["patient_id"] = patient_id
    if kind:
        query["kind"] = kind
    if status:
        query["status"] = status

    cursor = db.documents.find(query).sort("created_at", -1).limit(limit)
    documents = await cursor.to_list(length=limit)

    return [
        {
            "document_id": doc["_id"],
            "patient_id": doc["patient_id"],
            "kind": doc["kind"],
            "filename": doc["file"]["name"],
            "file_url": doc["file"]["url"],
            "status": doc["status"],
            "extracted": doc.get("extracted", {}),
            "created_at": doc["created_at"].isoformat(),
        }
        for doc in documents
    ]


# ==================== CONSENT FORM TOOLS ====================


@mcp.tool()
async def create_consent_form(
    patient_id: str,
    template_id: str,
    form_type: str,
    title: str,
    send_method: Optional[str] = "email",
) -> Dict[str, Any]:
    """
    Create and optionally send a consent form to a patient.

    Args:
        patient_id: Patient ID
        template_id: Form template ID
        form_type: Type of consent form
        title: Form title
        send_method: How to send (email, sms, portal)

    Returns:
        Dict with consent_form_id and details
    """
    # Verify patient exists
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )
    if not patient:
        return {"error": "Patient not found"}

    consent_form_id = str(uuid.uuid4())

    consent_form = {
        "_id": consent_form_id,
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "template_id": template_id,
        "form_type": form_type,
        "title": title,
        "status": "sent" if send_method else "to_do",
        "sent_via": send_method if send_method else None,
        "sent_at": datetime.now(timezone.utc) if send_method else None,
        "signed_at": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.consent_forms.insert_one(consent_form)

    return {
        "consent_form_id": consent_form_id,
        "patient_id": patient_id,
        "form_type": form_type,
        "status": consent_form["status"],
        "message": f"Consent form created and {'sent' if send_method else 'saved'}",
    }


@mcp.tool()
async def get_patient(patient_id: str) -> Dict[str, Any]:
    """
    Get patient details by ID.

    Args:
        patient_id: Patient ID to fetch

    Returns:
        Dict with patient details
    """
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )

    if not patient:
        return {"error": "Patient not found"}

    return {
        "patient_id": patient["_id"],
        "mrn": patient["mrn"],
        "first_name": patient["first_name"],
        "last_name": patient["last_name"],
        "dob": patient.get("dob"),
        "gender": patient.get("gender"),
        "email": patient["contact"]["email"],
        "phone": patient["contact"]["phone"],
        "address": patient["contact"].get("address"),
        "preconditions": patient.get("preconditions", []),
        "status": patient.get("status", "Active"),
        "tasks_count": patient.get("tasks_count", 0),
        "appointments_count": patient.get("appointments_count", 0),
        "flagged_count": patient.get("flagged_count", 0),
    }


@mcp.tool()
async def send_consent_forms(
    patient_id: str, form_template_ids: List[str], send_method: str = "email"
) -> Dict[str, Any]:
    """
    Send consent forms to a patient via DocuSign or email.

    Args:
        patient_id: Patient ID
        form_template_ids: List of form template IDs to send
        send_method: How to send (email, sms, portal)

    Returns:
        Dict with consent form IDs and details
    """
    # Verify patient exists
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )
    if not patient:
        return {"error": "Patient not found"}

    # Get form templates
    templates_cursor = db.form_templates.find(
        {"_id": {"$in": form_template_ids}, "tenant_id": DEFAULT_TENANT}
    )
    templates = await templates_cursor.to_list(length=len(form_template_ids))

    if not templates:
        return {"error": "No form templates found"}

    created_forms = []

    for template in templates:
        consent_form_id = str(uuid.uuid4())

        consent_form = {
            "_id": consent_form_id,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "template_id": template["_id"],
            "form_type": template.get("name", "consent"),
            "title": template.get("name", "Consent Form"),
            "status": "sent",
            "sent_via": send_method,
            "sent_at": datetime.now(timezone.utc),
            "signed_at": None,
            "docusign": {
                "envelope_id": f"env-{consent_form_id[:8]}",
                "status": "sent",
                "envelope_url": f"https://demo.docusign.com/envelope/{consent_form_id[:8]}",
            },
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        await db.consent_forms.insert_one(consent_form)
        created_forms.append(
            {
                "consent_form_id": consent_form_id,
                "template_id": template["_id"],
                "title": template.get("name"),
                "status": "sent",
            }
        )

    return {
        "success": True,
        "patient_id": patient_id,
        "forms_sent": len(created_forms),
        "forms": created_forms,
        "message": f"Sent {len(created_forms)} consent form(s) via {send_method}",
    }


@mcp.tool()
async def update_consent_form(
    consent_form_id: str, status: Optional[str] = None, signed_at: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update consent form status.

    Args:
        consent_form_id: Consent form ID to update
        status: New status (to_do, sent, in_progress, signed)
        signed_at: Signature timestamp in ISO format

    Returns:
        Dict with success status
    """
    update_fields = {}

    if status:
        update_fields["status"] = status
    if signed_at:
        update_fields["signed_at"] = datetime.fromisoformat(
            signed_at.replace("Z", "+00:00")
        )

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.consent_forms.update_one(
        {"_id": consent_form_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Consent form not found"}

    return {
        "success": True,
        "consent_form_id": consent_form_id,
        "updated_fields": list(update_fields.keys()),
    }


@mcp.tool()
async def get_consent_forms(
    patient_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get consent forms filtered by patient or status.

    Args:
        patient_id: Filter by patient ID
        status: Filter by status
        limit: Maximum number of results

    Returns:
        List of consent form dicts
    """
    query = {"tenant_id": DEFAULT_TENANT}

    if patient_id:
        query["patient_id"] = patient_id
    if status:
        query["status"] = status

    cursor = db.consent_forms.find(query).sort("created_at", -1).limit(limit)
    forms = await cursor.to_list(length=limit)

    return [
        {
            "consent_form_id": form["_id"],
            "patient_id": form["patient_id"],
            "patient_name": form["patient_name"],
            "form_type": form["form_type"],
            "title": form["title"],
            "status": form["status"],
            "sent_at": form["sent_at"].isoformat() if form.get("sent_at") else None,
            "signed_at": (
                form["signed_at"].isoformat() if form.get("signed_at") else None
            ),
        }
        for form in forms
    ]


# ==================== TASK TOOLS ====================


@mcp.tool()
async def create_task(
    patient_id: str,
    title: str,
    description: str,
    priority: str = "medium",
    kind: str = "general",
    assigned_to: str = "Dr. James O'Brien",
    agent_type: str = "ai_agent",
) -> Dict[str, Any]:
    """
    Create a new task.

    Args:
        patient_id: Patient ID
        title: Task title
        description: Task description
        priority: Priority (urgent, high, medium, low)
        kind: Task kind (general, document_review, insurance_verification, etc.)
        assigned_to: Who the task is assigned to
        agent_type: Type of agent creating the task

    Returns:
        Dict with task_id and details
    """
    # Verify patient exists
    patient = await db.patients.find_one(
        {"_id": patient_id, "tenant_id": DEFAULT_TENANT}
    )
    if not patient:
        return {"error": "Patient not found"}

    task_id = str(uuid.uuid4())
    task_id_display = f"T{random.randint(10000, 99999)}"

    task = {
        "_id": task_id,
        "task_id": task_id_display,
        "tenant_id": DEFAULT_TENANT,
        "source": "agent",
        "kind": kind,
        "title": title,
        "description": description,
        "patient_id": patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "assigned_to": assigned_to,
        "agent_type": agent_type,
        "priority": priority,
        "state": "open",
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }

    # Use transaction
    if client:
        async with client.start_session() as session:
            async with session.start_transaction():
                await db.tasks.insert_one(task, session=session)
                await db.patients.update_one(
                    {"_id": patient_id}, {"$inc": {"tasks_count": 1}}, session=session
                )
    else:
        await db.tasks.insert_one(task)
        await db.patients.update_one(
            {"_id": patient_id}, {"$inc": {"tasks_count": 1}}
        )

    return {
        "task_id": task_id,
        "task_id_display": task_id_display,
        "patient_id": patient_id,
        "title": title,
        "priority": priority,
        "state": "open",
        "message": "Task created successfully",
    }


@mcp.tool()
async def update_task(
    task_id: str,
    state: Optional[str] = None,
    priority: Optional[str] = None,
    comment: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update a task's state, priority, or add a comment.

    Args:
        task_id: Task ID to update
        state: New state (open, in_progress, done, cancelled)
        priority: New priority (urgent, high, medium, low)
        comment: Comment to add to the task

    Returns:
        Dict with success status
    """
    update_fields = {}

    if state:
        update_fields["state"] = state
    if priority:
        update_fields["priority"] = priority
    if comment:
        update_fields["$push"] = {
            "comments": {
                "user_id": "ai_agent",
                "text": comment,
                "created_at": datetime.now(timezone.utc),
            }
        }

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.tasks.update_one(
        {"_id": task_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        return {"error": "Task not found"}

    return {
        "success": True,
        "task_id": task_id,
        "updated_fields": list(update_fields.keys()),
    }


@mcp.tool()
async def get_tasks(
    patient_id: Optional[str] = None,
    state: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get tasks filtered by patient, state, or priority.

    Args:
        patient_id: Filter by patient ID
        state: Filter by state (open, in_progress, done, cancelled)
        priority: Filter by priority (urgent, high, medium, low)
        limit: Maximum number of results

    Returns:
        List of task dicts
    """
    query = {"tenant_id": DEFAULT_TENANT}

    if patient_id:
        query["patient_id"] = patient_id
    if state:
        query["state"] = state
    if priority:
        query["priority"] = priority

    cursor = db.tasks.find(query).sort("created_at", -1).limit(limit)
    tasks = await cursor.to_list(length=limit)

    return [
        {
            "task_id": task["_id"],
            "task_id_display": task["task_id"],
            "patient_id": task["patient_id"],
            "patient_name": task.get("patient_name"),
            "title": task["title"],
            "description": task["description"],
            "priority": task["priority"],
            "state": task["state"],
            "assigned_to": task["assigned_to"],
            "agent_type": task["agent_type"],
            "confidence_score": task.get("confidence_score"),
            "created_at": task["created_at"].isoformat(),
        }
        for task in tasks
    ]


def main():
    """Run the MCP server as a separate process"""
    # FastMCP runs via stdio by default
    # This is meant to be run as a separate server process
    try:
        mcp.run(transport="streamable-http", port=8002)
    except Exception as e:
        print(f"Error running MCP server: {e}")


if __name__ == "__main__":
    main()
