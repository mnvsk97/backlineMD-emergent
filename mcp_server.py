"""
FastMCP Server for BacklineMD AI Agents
"""

import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

mcp = FastMCP("BacklineMD Agent Tools")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.backlinemd
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "hackathon-demo")

TOOL_PERMISSIONS = {
    "intake": ["find_or_create_patient", "update_patient", "get_patient", "create_document", "get_documents", "update_document", "create_consent_form", "get_consent_forms", "update_consent_form", "send_consent_forms", "create_task", "update_task", "get_tasks", "send_email", "send_welcome_email_to_patient"],
    "doc_extraction": ["get_patient", "update_patient", "get_documents", "update_document", "create_task", "update_task", "get_tasks", "send_email", "send_document_confirmation_email"],
    "care_taker": ["get_patient", "update_patient", "get_appointments", "create_appointment", "update_appointment", "delete_appointment", "get_documents", "create_task", "update_task", "get_tasks", "send_email", "call_patient_to_schedule_appointment"],
    "insurance": ["get_patient", "get_insurance_claims", "create_insurance_claim", "update_insurance_claim", "get_documents", "create_task", "update_task", "get_tasks", "send_email"],
    "admin": ["get_all_patients"],
}


# PATIENT TOOLS

@mcp.tool()
async def get_all_patients(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all patients."""
    return await db.patients.find().limit(limit).to_list(length=limit)


@mcp.tool()
async def get_patient(patient_id: str) -> Dict[str, Any]:
    """Get patient details by ID."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
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
    }


@mcp.tool()
async def find_or_create_patient(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    dob: Optional[str] = None,
    gender: Optional[str] = None,
) -> Dict[str, Any]:
    """Find existing patient or create new one."""
    query = {"tenant_id": DEFAULT_TENANT}
    if email:
        query["contact.email"] = email
    elif phone:
        query["contact.phone"] = phone

    existing = await db.patients.find_one(query)
    if existing:
        return {
            "patient_id": existing["_id"],
            "first_name": existing["first_name"],
            "last_name": existing["last_name"],
            "email": existing["contact"]["email"],
            "phone": existing["contact"]["phone"],
            "mrn": existing["mrn"],
            "status": "existing",
        }

    if name and not (first_name and last_name):
        parts = name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    if not first_name:
        return {"error": "first_name or name required"}

    patient_id = str(uuid.uuid4())
    full_name = f"{first_name} {last_name or ''}".strip()
    ngrams = [full_name.lower().replace(" ", "")[i : i + 3] for i in range(len(full_name.replace(" ", "")) - 2)]

    patient = {
        "_id": patient_id,
        "tenant_id": DEFAULT_TENANT,
        "mrn": f"MRN{random.randint(100000, 999999)}",
        "first_name": first_name,
        "last_name": last_name or "",
        "dob": dob or "1990-01-01",
        "gender": gender or "Unknown",
        "contact": {"email": email or f"{first_name.lower()}@example.com", "phone": phone or "555-0000", "address": {}},
        "preconditions": [],
        "flags": [],
        "latest_vitals": {},
        "profile_image": None,
        "status": "Active",
        "tasks_count": 0,
        "appointments_count": 0,
        "flagged_count": 0,
        "search": {"ngrams": ngrams},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }

    await db.patients.insert_one(patient)
    return {
        "patient_id": patient_id,
        "first_name": first_name,
        "last_name": last_name or "",
        "email": patient["contact"]["email"],
        "phone": patient["contact"]["phone"],
        "mrn": patient["mrn"],
        "status": "created",
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
    """Update patient information."""
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

    result = await db.patients.update_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": "Patient not found"}
    return {"success": True, "patient_id": patient_id}


# APPOINTMENT TOOLS

@mcp.tool()
async def get_appointments(
    patient_id: Optional[str] = None,
    date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get appointments."""
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

    appointments = await db.appointments.find(query).sort("starts_at", 1).limit(limit).to_list(length=limit)
    patient_ids = list(set(apt["patient_id"] for apt in appointments))
    patients = {p["_id"]: p for p in await db.patients.find({"_id": {"$in": patient_ids}}).to_list(length=len(patient_ids))}

    return [
        {
            "appointment_id": apt["_id"],
            "patient_id": apt["patient_id"],
            "patient_name": f"{patients[apt['patient_id']]['first_name']} {patients[apt['patient_id']]['last_name']}" if apt["patient_id"] in patients else "Unknown",
            "type": apt["type"],
            "starts_at": apt["starts_at"].isoformat(),
            "ends_at": apt["ends_at"].isoformat(),
            "status": apt["status"],
            "location": apt.get("location"),
            "title": apt.get("title"),
        }
        for apt in appointments
    ]


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
    """Create a new appointment."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
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
        "google_calendar": {"event_id": f"mock-event-{appointment_id[:8]}", "calendar_id": "primary"},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.appointments.insert_one(appointment)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"appointments_count": 1}})
    return {"appointment_id": appointment_id, "patient_id": patient_id, "status": "scheduled"}


@mcp.tool()
async def update_appointment(
    appointment_id: str,
    status: Optional[str] = None,
    starts_at: Optional[str] = None,
    ends_at: Optional[str] = None,
    location: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an appointment."""
    update_fields = {}
    if status:
        update_fields["status"] = status
    if starts_at:
        update_fields["starts_at"] = datetime.fromisoformat(starts_at.replace("Z", "+00:00"))
    if ends_at:
        update_fields["ends_at"] = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
    if location:
        update_fields["location"] = location
    if title:
        update_fields["title"] = title
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.appointments.update_one({"_id": appointment_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": "Appointment not found"}
    return {"success": True, "appointment_id": appointment_id}


@mcp.tool()
async def delete_appointment(appointment_id: str) -> Dict[str, Any]:
    """Delete an appointment."""
    appointment = await db.appointments.find_one({"_id": appointment_id, "tenant_id": DEFAULT_TENANT})
    if not appointment:
        return {"error": "Appointment not found"}

    await db.appointments.delete_one({"_id": appointment_id})
    await db.patients.update_one({"_id": appointment["patient_id"]}, {"$inc": {"appointments_count": -1}})
    return {"success": True, "appointment_id": appointment_id}


# INSURANCE CLAIM TOOLS

@mcp.tool()
async def get_insurance_claims(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get insurance claims."""
    query = {"tenant_id": DEFAULT_TENANT}
    if patient_id:
        query["patient_id"] = patient_id
    if status:
        query["status"] = status

    claims = await db.claims.find(query).sort("last_event_at", -1).limit(limit).to_list(length=limit)
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
    """Create a new insurance claim."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}

    claim_id = str(uuid.uuid4())
    claim = {
        "_id": claim_id,
        "claim_id": f"C{random.randint(10000, 99999)}",
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "insurance_provider": insurance_provider,
        "amount": int(amount * 100),
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
    return {"claim_id": claim_id, "patient_id": patient_id, "status": "pending"}


@mcp.tool()
async def update_insurance_claim(
    claim_id: str,
    amount: Optional[float] = None,
    status: Optional[str] = None,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an insurance claim."""
    update_fields = {}
    if amount is not None:
        update_fields["amount"] = int(amount * 100)
        update_fields["amount_display"] = amount
    if status:
        update_fields["status"] = status
        update_fields["last_event_at"] = datetime.now(timezone.utc)
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.claims.update_one({"_id": claim_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": "Claim not found"}

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
    return {"success": True, "claim_id": claim_id}


# DOCUMENT TOOLS

@mcp.tool()
async def create_document(
    patient_id: str,
    kind: str,
    filename: str,
    mime_type: str,
    file_url: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a document record."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}

    document_id = str(uuid.uuid4())
    document = {
        "_id": document_id,
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "kind": kind,
        "file": {"url": file_url or f"/uploads/{document_id}/{filename}", "name": filename, "mime": mime_type, "size": 0, "sha256": f"mock-hash-{document_id[:8]}"},
        "ocr": {"done": False, "engine": None},
        "extracted": extracted_data or {},
        "status": "uploaded" if not extracted_data else "ingested",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.documents.insert_one(document)
    return {"document_id": document_id, "patient_id": patient_id, "kind": kind, "status": document["status"]}


@mcp.tool()
async def update_document(
    document_id: str,
    status: Optional[str] = None,
    extracted_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update a document."""
    update_fields = {}
    if status:
        update_fields["status"] = status
    if extracted_data:
        update_fields["extracted"] = extracted_data
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.documents.update_one({"_id": document_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": "Document not found"}
    return {"success": True, "document_id": document_id}


@mcp.tool()
async def get_documents(
    patient_id: Optional[str] = None,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Get documents."""
    query = {"tenant_id": DEFAULT_TENANT}
    if patient_id:
        query["patient_id"] = patient_id
    if kind:
        query["kind"] = kind
    if status:
        query["status"] = status

    documents = await db.documents.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
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


# CONSENT FORM TOOLS

@mcp.tool()
async def create_consent_form(
    patient_id: str,
    template_id: str,
    form_type: str,
    title: str,
    send_method: Optional[str] = "email",
) -> Dict[str, Any]:
    """Create a consent form."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
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
    return {"consent_form_id": consent_form_id, "patient_id": patient_id, "status": consent_form["status"]}


@mcp.tool()
async def send_consent_forms(patient_id: str, form_template_ids: List[str], send_method: str = "email") -> Dict[str, Any]:
    """Send consent forms to a patient."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}

    templates = await db.form_templates.find({"_id": {"$in": form_template_ids}, "tenant_id": DEFAULT_TENANT}).to_list(length=len(form_template_ids))
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
            "docusign": {"envelope_id": f"env-{consent_form_id[:8]}", "status": "sent", "envelope_url": f"https://demo.docusign.com/envelope/{consent_form_id[:8]}"},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await db.consent_forms.insert_one(consent_form)
        created_forms.append({"consent_form_id": consent_form_id, "template_id": template["_id"], "title": template.get("name"), "status": "sent"})

    return {"success": True, "patient_id": patient_id, "forms_sent": len(created_forms), "forms": created_forms}


@mcp.tool()
async def update_consent_form(consent_form_id: str, status: Optional[str] = None, signed_at: Optional[str] = None) -> Dict[str, Any]:
    """Update consent form status."""
    update_fields = {}
    if status:
        update_fields["status"] = status
    if signed_at:
        update_fields["signed_at"] = datetime.fromisoformat(signed_at.replace("Z", "+00:00"))
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.consent_forms.update_one({"_id": consent_form_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": "Consent form not found"}
    return {"success": True, "consent_form_id": consent_form_id}


@mcp.tool()
async def get_consent_forms(patient_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get consent forms."""
    query = {"tenant_id": DEFAULT_TENANT}
    if patient_id:
        query["patient_id"] = patient_id
    if status:
        query["status"] = status

    forms = await db.consent_forms.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
    return [
        {
            "consent_form_id": form["_id"],
            "patient_id": form["patient_id"],
            "patient_name": form["patient_name"],
            "form_type": form["form_type"],
            "title": form["title"],
            "status": form["status"],
            "sent_at": form["sent_at"].isoformat() if form.get("sent_at") else None,
            "signed_at": form["signed_at"].isoformat() if form.get("signed_at") else None,
        }
        for form in forms
    ]


# TASK TOOLS

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
    """Create a new task."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}

    task_id = str(uuid.uuid4())
    task = {
        "_id": task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
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

    await db.tasks.insert_one(task)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    return {"task_id": task_id, "patient_id": patient_id, "title": title, "priority": priority, "state": "open"}


@mcp.tool()
async def update_task(task_id: str, state: Optional[str] = None, priority: Optional[str] = None, comment: Optional[str] = None) -> Dict[str, Any]:
    """Update a task."""
    update_fields = {}
    if state:
        update_fields["state"] = state
    if priority:
        update_fields["priority"] = priority
    if comment:
        update_fields["$push"] = {"comments": {"user_id": "ai_agent", "text": comment, "created_at": datetime.now(timezone.utc)}}
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.tasks.update_one({"_id": task_id, "tenant_id": DEFAULT_TENANT}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": "Task not found"}
    return {"success": True, "task_id": task_id}


@mcp.tool()
async def get_tasks(patient_id: Optional[str] = None, state: Optional[str] = None, priority: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Get tasks."""
    query = {"tenant_id": DEFAULT_TENANT}
    if patient_id:
        query["patient_id"] = patient_id
    if state:
        query["state"] = state
    if priority:
        query["priority"] = priority

    tasks = await db.tasks.find(query).sort("created_at", -1).limit(limit).to_list(length=limit)
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


# EMAIL TOOLS

@mcp.tool()
async def send_email(patient_id: str, subject: str, body: str, html_body: Optional[str] = None) -> Dict[str, Any]:
    """Send an email to a patient via Gmail using Composio."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}
    if not patient["contact"]["email"]:
        return {"error": "Patient email not found"}

    from composio_email_service import get_email_service

    service = await get_email_service()
    result = await service.send_email(to_email=patient["contact"]["email"], subject=subject, body=body, html_body=html_body)
    return {"success": result.get("success", False), "patient_id": patient_id, "message_id": result.get("message_id"), "error": result.get("error")}


@mcp.tool()
async def send_welcome_email_to_patient(patient_id: str) -> Dict[str, Any]:
    """Send a welcome email to a new patient."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}
    if not patient["contact"]["email"]:
        return {"error": "Patient email not found"}

    from composio_email_service import send_welcome_email

    result = await send_welcome_email(patient_email=patient["contact"]["email"], patient_name=f"{patient['first_name']} {patient['last_name']}")
    return {"success": result.get("success", False), "patient_id": patient_id, "error": result.get("error")}


@mcp.tool()
async def send_document_confirmation_email(patient_id: str) -> Dict[str, Any]:
    """Send a confirmation email when documents are received."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}
    if not patient["contact"]["email"]:
        return {"error": "Patient email not found"}

    from composio_email_service import send_document_received_email

    result = await send_document_received_email(patient_email=patient["contact"]["email"], patient_name=f"{patient['first_name']} {patient['last_name']}")
    return {"success": result.get("success", False), "patient_id": patient_id, "error": result.get("error")}


# PHONE TOOLS

@mcp.tool()
async def call_patient_to_schedule_appointment(patient_id: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Call a patient to schedule an appointment using Vapi AI."""
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": DEFAULT_TENANT})
    if not patient:
        return {"error": "Patient not found"}
    if not patient["contact"]["phone"]:
        return {"error": "Patient phone number not found"}

    patient_phone = patient["contact"]["phone"]
    if not patient_phone.startswith("+"):
        patient_phone = patient_phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        if len(patient_phone) == 10:
            patient_phone = f"+1{patient_phone}"
        else:
            patient_phone = f"+{patient_phone}"

    from vapi_phone_service import call_patient_for_appointment

    result = await call_patient_for_appointment(patient_phone=patient_phone, patient_name=f"{patient['first_name']} {patient['last_name']}", patient_id=patient_id, context=context)
    return {"success": result.get("success", False), "patient_id": patient_id, "call_id": result.get("call_id"), "error": result.get("error")}


def main():
    """Run the MCP server."""
    mcp.run(transport="sse", port=8002)


if __name__ == "__main__":
    main()
