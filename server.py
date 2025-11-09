import asyncio
import os
import random
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Import our modules
from database import close_db, connect_db, get_db
from logger import get_logger
from models import *

# Composio email integration (temporarily disabled due to import issues)
# from composio_integration import send_patient_notification_email, send_email_via_composio


# Initialize logger
logger = get_logger(__name__)


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()

    logger.info("BacklineMD API started successfully")
    yield
    # Shutdown
    await close_db()
    logger.info("BacklineMD API stopped")


# Create FastAPI app with lifespan
app = FastAPI(title="BacklineMD API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CopilotKit integration will be registered in lifespan handler
# (moved there because graph initialization is async)


# ==================== HELPER FUNCTIONS ====================

# Default tenant for hackathon/demo mode
DEFAULT_TENANT = "hackathon-demo"


def generate_ngrams(text: str, n: int = 3) -> List[str]:
    """Generate n-grams for fuzzy search"""
    text = text.lower().replace(" ", "")
    return [text[i : i + n] for i in range(len(text) - n + 1)]


# ==================== PATIENT ROUTES ====================


@app.get("/api/patients")
async def list_patients(
    q: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    query = {"tenant_id": tenant_id}
    if q:
        # Search using n-grams
        ngrams = generate_ngrams(q)
        query["search.ngrams"] = {"$in": ngrams}

    cursor = db.patients.find(query).skip(skip).limit(limit).sort("created_at", -1)
    patients = await cursor.to_list(length=limit)

    result = []
    for p in patients:
        result.append(
            {
                "patient_id": p["_id"],
                "first_name": p["first_name"],
                "last_name": p["last_name"],
                "email": p["contact"]["email"],
                "phone": p["contact"]["phone"],
                "status": p.get("status", "Active"),
                "tasks_count": p.get("tasks_count", 0),
                "appointments_count": p.get("appointments_count", 0),
                "flagged_count": p.get("flagged_count", 0),
                "profile_image": p.get("profile_image"),
            }
        )

    return result


@app.post("/api/patients")
async def create_patient(patient_data: PatientCreate):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    patient_id = str(uuid.uuid4())
    mrn = f"MRN{random.randint(100000, 999999)}"

    # Generate search n-grams
    full_name = f"{patient_data.first_name} {patient_data.last_name}"
    ngrams = generate_ngrams(full_name)

    # Calculate age from DOB
    age = None
    if patient_data.dob:
        try:
            dob_date = datetime.strptime(patient_data.dob, "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            age = (
                today.year
                - dob_date.year
                - ((today.month, today.day) < (dob_date.month, dob_date.day))
            )
        except:
            pass

    # Initialize treatment timeline
    treatment_timeline = [
        {
            "stage": "Initial Consultation",
            "status": "pending",
            "date": datetime.now(timezone.utc).isoformat(),
            "notes": "Patient intake in progress",
        }
    ]

    patient = {
        "_id": patient_id,
        "tenant_id": tenant_id,
        "mrn": mrn,
        "first_name": patient_data.first_name,
        "last_name": patient_data.last_name,
        "name": full_name,
        "dob": patient_data.dob,
        "age": age,
        "gender": patient_data.gender,
        "contact": {
            "email": patient_data.email,
            "phone": patient_data.phone,
            "address": patient_data.address or {},
        },
        "preconditions": patient_data.preconditions or [],
        "flags": [],
        "latest_vitals": {},
        "height": None,
        "weight": None,
        "blood_type": None,
        "profile_image": patient_data.profile_image,
        "status": "Intake In Progress",
        "treatment_timeline": treatment_timeline,
        "ai_summary": None,
        "insurance": {},
        "tasks_count": 0,
        "appointments_count": 0,
        "flagged_count": 0,
        "search": {"ngrams": ngrams},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "demo-user",
    }

    await db.patients.insert_one(patient)

    # Generate AI summary for the patient
    try:
        preconditions_text = (
            ", ".join(patient_data.preconditions)
            if patient_data.preconditions
            else "no documented preconditions"
        )
        age_text = f"{age}-year-old" if age else "patient"
        summary_text = f"{age_text} {patient_data.gender.lower()} patient with {preconditions_text}. Currently in intake process. Initial consultation pending. Medical records collection in progress."

        await db.patients.update_one(
            {"_id": patient_id, "tenant_id": tenant_id},
            {
                "$set": {
                    "ai_summary": summary_text,
                    "ai_summary_generated_at": datetime.now(timezone.utc),
                }
            },
        )
    except Exception as e:
        print(f"Warning: Failed to generate AI summary: {e}")

    # Create default consent forms (4 forms)
    default_forms = [
        {
            "name": "Insurance Information Release",
            "description": "Authorization to release medical information to insurance provider",
        },
        {
            "name": "Medical Records Request - Lab",
            "description": "Request medical records from external laboratory",
        },
        {
            "name": "HIPAA Authorization Form",
            "description": "HIPAA compliant authorization for information disclosure",
        },
        {
            "name": "Consent for Treatment",
            "description": "Patient consent for proposed treatment plan",
        },
    ]

    created_forms = []
    for i, form_template in enumerate(default_forms):
        consent_form_id = str(uuid.uuid4())
        consent_form = {
            "_id": consent_form_id,
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "patient_name": full_name,
            "template_id": f"template-{i}",
            "form_type": form_template.get("name", "consent"),
            "title": form_template.get("name", "Consent Form"),
            "status": "to_do",
            "sent_via": None,
            "sent_at": None,
            "signed_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        await db.consent_forms.insert_one(consent_form)
        created_forms.append(consent_form_id)

    # Create tasks for the patient
    tasks_created = []

    # Task 1: Send consent email - TODO (open)
    consent_email_task_id = str(uuid.uuid4())
    consent_email_task = {
        "_id": consent_email_task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": tenant_id,
        "source": "agent",
        "kind": "consent_forms",
        "title": f"Send Consent Email to Patient - {full_name}",
        "description": f"New patient {full_name} has been created. Please send consent forms email to the patient.",
        "patient_id": patient_id,
        "patient_name": full_name,
        "assigned_to": "Dr. James O'Brien",
        "agent_type": "care_taker",
        "priority": "medium",
        "state": "open",
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }
    await db.tasks.insert_one(consent_email_task)
    tasks_created.append(consent_email_task_id)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})

    # Task 2: Document extraction - TODO (open)
    doc_extraction_task_id = str(uuid.uuid4())
    doc_extraction_task = {
        "_id": doc_extraction_task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": tenant_id,
        "source": "agent",
        "kind": "document_review",
        "title": f"Extract and Review Patient Documents - {full_name}",
        "description": f"New patient {full_name} has been created. Please review and extract information from any uploaded documents. Ensure all medical records are properly processed and indexed.",
        "patient_id": patient_id,
        "patient_name": full_name,
        "assigned_to": "AI - Document Extractor",
        "agent_type": "doc_extraction",
        "priority": "medium",
        "state": "open",
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }
    await db.tasks.insert_one(doc_extraction_task)
    tasks_created.append(doc_extraction_task_id)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})

    # Task 3: Intake agent - send welcome email asking for medical records (in_progress)
    welcome_email_task_id = str(uuid.uuid4())
    welcome_email_task = {
        "_id": welcome_email_task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": tenant_id,
        "source": "agent",
        "kind": "welcome_email",
        "title": f"Send Welcome Email and Request Medical Records - {full_name}",
        "description": f"New patient {full_name} has been created. Send welcome email and request medical records from the patient.",
        "patient_id": patient_id,
        "patient_name": full_name,
        "assigned_to": "AI - Intake Agent",
        "agent_type": "intake",
        "priority": "high",
        "state": "in_progress",
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "ai_agent",
    }
    await db.tasks.insert_one(welcome_email_task)
    tasks_created.append(welcome_email_task_id)
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})

    # Send welcome email
    email_result = None
    try:
        from composio_integration import send_welcome_email

        email_result = await send_welcome_email(
            patient_email=patient_data.email, patient_name=full_name
        )
        print(f"Welcome email sent result: {email_result}")

        # Mark welcome email task as done if email was sent successfully
        if email_result.get("success"):
            await db.tasks.update_one(
                {"_id": welcome_email_task_id, "tenant_id": tenant_id},
                {"$set": {"state": "done", "updated_at": datetime.now(timezone.utc)}},
            )
            print(f"Welcome email task marked as done")
    except Exception as e:
        print(f"Warning: Failed to send welcome email: {e}")
        email_result = {"success": False, "error": str(e)}

    return {
        "patient_id": patient_id,
        "message": "Patient created successfully",
        "tasks_created": len(tasks_created),
        "email_sent": email_result.get("success", False) if email_result else False,
    }


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get patient notes (empty for new patients)
    notes_cursor = (
        db.patient_notes.find({"patient_id": patient_id, "tenant_id": tenant_id})
        .sort("created_at", -1)
        .limit(50)
    )
    notes = await notes_cursor.to_list(length=50)

    # Get tasks for this patient (exclude tasks marked as "done")
    tasks_cursor = (
        db.tasks.find(
            {
                "patient_id": patient_id,
                "tenant_id": tenant_id,
                "state": {"$ne": "done"},  # Exclude tasks with state "done"
            }
        )
        .sort("created_at", -1)
        .limit(50)
    )
    tasks = await tasks_cursor.to_list(length=50)

    # Debug logging
    print(f"DEBUG: Fetching tasks for patient_id: {patient_id}, tenant_id: {tenant_id}")
    print(
        f"DEBUG: Found {len(tasks)} active tasks for patient {patient_id} (excluding done tasks)"
    )
    if tasks:
        for task in tasks:
            print(
                f"  - Task: {task.get('title')}, patient_id: {task.get('patient_id')}, state: {task.get('state')}"
            )

    # Get AI summary from patient document (no caching)
    ai_summary = patient.get("ai_summary")

    # Calculate age from DOB if available
    age = patient.get("age")
    if not age and patient.get("dob"):
        try:
            dob_date = datetime.strptime(patient["dob"], "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            age = (
                today.year
                - dob_date.year
                - ((today.month, today.day) < (dob_date.month, dob_date.day))
            )
        except:
            age = None

    # Get vitals and physical details
    latest_vitals = patient.get("latest_vitals", {})

    return {
        "patient_id": patient["_id"],
        "mrn": patient["mrn"],
        "first_name": patient.get("first_name", ""),
        "last_name": patient.get("last_name", ""),
        "dob": patient.get("dob"),
        "gender": patient.get("gender"),
        "email": patient["contact"]["email"],
        "phone": patient["contact"]["phone"],
        "address": patient["contact"].get("address"),
        "preconditions": patient.get("preconditions", []),
        "latest_vitals": latest_vitals,
        "height": latest_vitals.get("height") or patient.get("height"),
        "weight": latest_vitals.get("weight") or patient.get("weight"),
        "blood_type": latest_vitals.get("blood_type") or patient.get("blood_type"),
        "profile_image": patient.get("profile_image"),
        "status": patient.get("status"),
        "tasks_count": patient.get("tasks_count", 0),
        "appointments_count": patient.get("appointments_count", 0),
        "flagged_count": patient.get("flagged_count", 0),
        "age": age,
        "insurance": patient.get("insurance", {}),
        "treatment_timeline": patient.get("treatment_timeline", []),
        "ai_summary": ai_summary,
        "notes": [
            {
                "note_id": note["_id"],
                "date": note.get("created_at", datetime.now(timezone.utc)).strftime(
                    "%Y-%m-%d"
                ),
                "author": note.get("author", "Unknown"),
                "content": note.get("content", ""),
                "created_at": note.get(
                    "created_at", datetime.now(timezone.utc)
                ).isoformat(),
            }
            for note in notes
        ],
        "tasks": [
            {
                "task_id": task["_id"],
                "title": task.get("title", ""),
                "description": task.get("description", ""),
                "patient_name": task.get("patient_name"),
                "assigned_to": task.get("assigned_to"),
                "agent_type": task.get("agent_type"),
                "priority": task.get("priority"),
                "state": task.get("state"),
                "confidence_score": task.get("confidence_score"),
                "waiting_minutes": task.get("waiting_minutes", 0),
                "created_at": (
                    task.get("created_at", datetime.now(timezone.utc)).isoformat()
                    if isinstance(task.get("created_at"), datetime)
                    else task.get("created_at")
                ),
            }
            for task in tasks
        ],
    }


@app.get("/api/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    """Generate and return patient summary - always generates a new summary on request"""
    db = get_db()
    tenant_id = DEFAULT_TENANT

    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Calculate age from DOB if available
    age = patient.get("age")
    if not age and patient.get("dob"):
        try:
            dob_date = datetime.strptime(patient["dob"], "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            age = (
                today.year
                - dob_date.year
                - ((today.month, today.day) < (dob_date.month, dob_date.day))
            )
        except:
            age = None

    # Always generate summary (mock for now, in production would use AI)
    preconditions = patient.get("preconditions", [])
    preconditions_text = (
        ", ".join(preconditions) if preconditions else "no documented preconditions"
    )
    age_text = f"{age}-year-old" if age else "patient"

    # Generate a concise, 2-line high-quality clinical summary using OpenAI (GPT-4)

    from openai import AsyncOpenAI

    openai_client = AsyncOpenAI()

    # Gather relevant info
    # (already collected: age, gender, preconditions, status)
    latest_appointment = await db.appointments.find_one(
        {"patient_id": patient_id, "tenant_id": tenant_id}, sort=[("date", -1)]
    )
    latest_task = await db.tasks.find_one(
        {"patient_id": patient_id, "tenant_id": tenant_id}, sort=[("created_at", -1)]
    )

    is_new_patient = patient.get("status", "").lower() in ["intake in progress", "new"]

    stage = None
    if is_new_patient or patient.get("status", "").lower() in [
        "intake in progress",
        "new",
    ]:
        stage = "intake"
    elif latest_appointment:
        stage = latest_appointment.get("type", "consultation")
    elif latest_task:
        stage = latest_task.get("title", "pending task").lower()
    else:
        stage = patient.get("status", "Active").lower()

    gender = patient.get("gender", "Unknown")
    condition = (
        ", ".join(preconditions) if preconditions else "no documented conditions"
    )
    status = patient.get("status", "Active").lower()
    first_name = patient.get("first_name", "")
    last_name = patient.get("last_name", "")

    # Compose prompt for short summary
    summary_prompt = f"""Create a SHORT, high-quality, 2-line clinical summary for this patient, suitable for a busy medical team. Include age, gender, any relevant conditions, and their current consultation or intake stage, in clean natural language. If the patient is new, make it explicit.

Name: {first_name} {last_name}
Age: {age if age else "N/A"}
Gender: {gender}
Conditions: {condition}
Stage: {stage}
Status: {status}
"""

    if is_new_patient:
        summary_prompt += (
            "The patient is new and currently undergoing the intake process.\n"
        )

    summary_prompt += "Summary (2 lines with important details that are needed for a doctor consultion):"

    summary_resp = await openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a world-class clinical summarizer. Your summaries are concise, accurate, always ≤2 lines, and highlight age, gender, key conditions, and the current stage.",
            },
            {"role": "user", "content": summary_prompt},
        ],
        max_tokens=82,
        temperature=0.3,
    )
    summary_text = summary_resp.choices[0].message.content.strip()

    # Store summary in patient document
    await db.patients.update_one(
        {"_id": patient_id, "tenant_id": tenant_id},
        {
            "$set": {
                "ai_summary": summary_text,
                "ai_summary_generated_at": datetime.now(timezone.utc),
            }
        },
    )

    payload = {
        "summary": summary_text,
        "citations": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "gpt-4",
    }

    return payload


@app.post("/api/patients/{patient_id}/notes")
async def create_patient_note(patient_id: str, note_data: dict):
    """Create a new patient note"""
    db = get_db()
    tenant_id = DEFAULT_TENANT

    # Verify patient exists
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    note_id = str(uuid.uuid4())
    note = {
        "_id": note_id,
        "tenant_id": tenant_id,
        "patient_id": patient_id,
        "content": note_data.get("content", ""),
        "author": note_data.get("author", "Unknown"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.patient_notes.insert_one(note)

    return {
        "note_id": note_id,
        "message": "Note created successfully",
    }


# ==================== DOCUMENT ROUTES ====================


@app.get("/api/documents")
async def list_documents(
    patient_id: Optional[str] = None,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    query = {"tenant_id": tenant_id}
    if patient_id:
        query["patient_id"] = patient_id
    if kind:
        query["kind"] = kind
    if status:
        query["status"] = status

    cursor = db.documents.find(query).skip(skip).limit(limit).sort("created_at", -1)
    documents = await cursor.to_list(length=limit)

    return [
        {
            "document_id": doc["_id"],
            "patient_id": doc["patient_id"],
            "kind": doc["kind"],
            "file": doc["file"],
            "status": doc["status"],
            "extracted": doc.get("extracted"),
            "created_at": doc["created_at"],
        }
        for doc in documents
    ]


@app.post("/api/documents/upload")
async def upload_document(
    patient_id: str,
    kind: str,
    file: UploadFile = File(...),
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    # In production, upload to S3. For now, just store metadata
    document_id = str(uuid.uuid4())

    document = {
        "_id": document_id,
        "tenant_id": tenant_id,
        "patient_id": patient_id,
        "kind": kind,
        "file": {
            "url": f"/uploads/{document_id}/{file.filename}",
            "name": file.filename,
            "mime": file.content_type,
            "size": 0,  # Would be real size
            "sha256": "mock-hash",
        },
        "ocr": {"done": False, "engine": None},
        "extracted": {},
        "status": DocumentStatus.UPLOADED,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.documents.insert_one(document)

    # Trigger document extraction agent (async)
    asyncio.create_task(trigger_document_extraction(document_id, tenant_id))

    return {
        "document_id": document_id,
        "status": DocumentStatus.UPLOADED,
        "message": "Document uploaded successfully",
    }


@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    document = await db.documents.find_one({"_id": document_id, "tenant_id": tenant_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document["_id"],
        "patient_id": document["patient_id"],
        "kind": document["kind"],
        "file": document["file"],
        "status": document["status"],
        "extracted": document.get("extracted"),
        "created_at": document["created_at"],
    }


@app.patch("/api/documents/{document_id}")
async def update_document(
    document_id: str,
    update_data: DocumentUpdate,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    update_fields = {}
    if update_data.status:
        update_fields["status"] = update_data.status
    if update_data.extracted:
        update_fields["extracted"] = update_data.extracted

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.documents.update_one(
        {"_id": document_id, "tenant_id": tenant_id}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document updated successfully"}


# ==================== MOCK AGENT FUNCTION ====================


async def trigger_document_extraction(document_id: str, tenant_id: str):
    """Mock document extraction agent"""
    db = get_db()

    # Wait 2 seconds
    await asyncio.sleep(2)

    # Update status to ingesting
    await db.documents.update_one(
        {"_id": document_id}, {"$set": {"status": DocumentStatus.INGESTING}}
    )

    # Wait 3 more seconds
    await asyncio.sleep(3)

    # Simulate extraction
    confidence = random.uniform(0.75, 0.98)

    extracted_data = {
        "blood_type": "O+",
        "cholesterol": "205 mg/dL",
        "bp": "125/80",
        "hr": 68,
        "confidence": confidence,
    }

    status = (
        DocumentStatus.INGESTED if confidence > 0.9 else DocumentStatus.NOT_INGESTED
    )

    await db.documents.update_one(
        {"_id": document_id},
        {
            "$set": {
                "status": status,
                "extracted": {
                    "fields": extracted_data,
                    "confidence": confidence,
                    "needs_review": [] if confidence > 0.9 else ["cholesterol"],
                },
            }
        },
    )

    # If low confidence, create task
    if confidence < 0.9:
        doc = await db.documents.find_one({"_id": document_id})
        patient = await db.patients.find_one({"_id": doc["patient_id"]})

        task_id = str(uuid.uuid4())
        task = {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": tenant_id,
            "source": "agent",
            "kind": "document_review",
            "title": "Verify Medical History Extraction",
            "description": f"Review extracted data from {doc['file']['name']}. Confidence: {int(confidence*100)}%. Please verify cholesterol reading.",
            "patient_id": doc["patient_id"],
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "doc_id": document_id,
            "assigned_to": "Dr. James O'Brien",
            "agent_type": "ai_agent",
            "priority": TaskPriority.HIGH,
            "state": TaskState.OPEN,
            "confidence_score": confidence,
            "waiting_minutes": 0,
            "ai_resume_hook": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        await db.tasks.insert_one(task)

        # Increment patient task count
        await db.patients.update_one(
            {"_id": doc["patient_id"]}, {"$inc": {"tasks_count": 1}}
        )


# ==================== TASK ROUTES ====================


@app.get("/api/tasks")
async def list_tasks(
    state: Optional[str] = None,
    patient_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    query = {"tenant_id": tenant_id}
    if state:
        query["state"] = state
    else:
        # By default, exclude "done" tasks unless state is explicitly requested
        query["state"] = {"$ne": "done"}
    if patient_id:
        query["patient_id"] = patient_id
        # Debug logging
        print(f"DEBUG: Filtering tasks by patient_id: {patient_id}")
    if assignee_id:
        query["assignee_id"] = assignee_id
    if priority:
        query["priority"] = priority

    # Debug: Count total tasks and tasks matching query
    total_tasks = await db.tasks.count_documents({"tenant_id": tenant_id})
    matching_tasks = await db.tasks.count_documents(query)
    print(
        f"DEBUG: Total tasks in DB: {total_tasks}, Matching query: {matching_tasks}, Query: {query}"
    )

    cursor = db.tasks.find(query).skip(skip).limit(limit).sort("created_at", -1)
    tasks = await cursor.to_list(length=limit)

    # Debug: Log found tasks
    if patient_id:
        print(f"DEBUG: Found {len(tasks)} tasks for patient_id: {patient_id}")
        for task in tasks:
            print(
                f"  - Task: {task.get('title')}, patient_id: {task.get('patient_id')}, state: {task.get('state')}"
            )

    return [
        {
            "task_id": task["_id"],  # Use _id as task_id for API consistency
            "title": task["title"],
            "description": task["description"],
            "patient_name": task.get("patient_name"),
            "assigned_to": task["assigned_to"],
            "agent_type": task["agent_type"],
            "priority": task["priority"],
            "state": task["state"],
            "confidence_score": task.get("confidence_score"),
            "waiting_minutes": task.get("waiting_minutes", 0),
            "created_at": task["created_at"],
        }
        for task in tasks
    ]


@app.post("/api/tasks")
async def create_task(task_data: TaskCreate):
    from database import get_client

    db = get_db()
    client = get_client()
    tenant_id = DEFAULT_TENANT

    # Get patient name
    patient = await db.patients.find_one(
        {"_id": task_data.patient_id, "tenant_id": tenant_id}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    task_id = str(uuid.uuid4())
    task = {
        "_id": task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": tenant_id,
        "source": "manual",
        "kind": task_data.kind or "general",
        "title": task_data.title,
        "description": task_data.description,
        "patient_id": task_data.patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "assigned_to": task_data.assigned_to,
        "agent_type": task_data.agent_type,
        "priority": task_data.priority,
        "state": TaskState.OPEN,
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "demo-user",
    }

    # Use transaction to ensure atomicity
    try:
        if client:
            async with client.start_session() as session:
                async with session.start_transaction():
                    await db.tasks.insert_one(task, session=session)
                    await db.patients.update_one(
                        {"_id": task_data.patient_id},
                        {"$inc": {"tasks_count": 1}},
                        session=session,
                    )
        else:
            # Fallback without transaction
            await db.tasks.insert_one(task)
            await db.patients.update_one(
                {"_id": task_data.patient_id}, {"$inc": {"tasks_count": 1}}
            )
    except Exception as e:
        # Fallback without transaction if session fails
        await db.tasks.insert_one(task)
        await db.patients.update_one(
            {"_id": task_data.patient_id}, {"$inc": {"tasks_count": 1}}
        )

    return {"task_id": task_id, "message": "Task created successfully"}


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, update_data: TaskUpdate):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    update_operations = {}

    # Handle $set operations
    set_fields = {}
    if update_data.state:
        set_fields["state"] = update_data.state
    set_fields["updated_at"] = datetime.now(timezone.utc)
    update_operations["$set"] = set_fields

    # Handle $push operations
    if update_data.comment:
        update_operations["$push"] = {
            "comments": {
                "user_id": "demo-user",
                "text": update_data.comment,
                "created_at": datetime.now(timezone.utc),
            }
        }

    result = await db.tasks.update_one(
        {"_id": task_id, "tenant_id": tenant_id}, update_operations
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task updated successfully"}


@app.patch("/api/appointments/{appointment_id}")
async def update_appointment(appointment_id: str, update_data: dict):
    """Update appointment status and create insurance verification task if completed"""
    db = get_db()
    tenant_id = DEFAULT_TENANT

    update_fields = {}
    if update_data.get("status"):
        update_fields["status"] = update_data["status"]
    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.appointments.update_one(
        {"_id": appointment_id, "tenant_id": tenant_id}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # If appointment is marked as completed, create insurance verification task
    if update_data.get("status") == "completed":
        appointment = await db.appointments.find_one(
            {"_id": appointment_id, "tenant_id": tenant_id}
        )
        if appointment:
            patient = await db.patients.find_one(
                {"_id": appointment["patient_id"], "tenant_id": tenant_id}
            )
            if patient:
                patient_name = (
                    f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
                )

                # Create insurance verification task
                task_id = str(uuid.uuid4())
                insurance_task = {
                    "_id": task_id,
                    "task_id": f"T{random.randint(10000, 99999)}",
                    "tenant_id": tenant_id,
                    "source": "agent",
                    "kind": "insurance_verification",
                    "title": f"Verify Insurance Forms - {patient_name}",
                    "description": f"Consultation completed for {patient_name}. Please verify insurance forms and coverage details.",
                    "patient_id": appointment["patient_id"],
                    "patient_name": patient_name,
                    "assigned_to": "AI - Insurance Agent",
                    "agent_type": "insurance",
                    "priority": "high",
                    "state": TaskState.OPEN,
                    "confidence_score": 1.0,
                    "waiting_minutes": 0,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "created_by": "ai_agent",
                }

                await db.tasks.insert_one(insurance_task)
                await db.patients.update_one(
                    {"_id": appointment["patient_id"]}, {"$inc": {"tasks_count": 1}}
                )
                print(f"Insurance verification task created for patient {patient_name}")

    return {"message": "Appointment updated successfully"}


# ==================== CLAIM ROUTES ====================


@app.get("/api/claims")
async def list_claims(
    status: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    if patient_id:
        query["patient_id"] = patient_id

    cursor = db.claims.find(query).skip(skip).limit(limit).sort("last_event_at", -1)
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
            "last_event_at": claim.get("last_event_at"),
        }
        for claim in claims
    ]


@app.post("/api/claims")
async def create_claim(claim_data: ClaimCreate):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    # Get patient
    patient = await db.patients.find_one(
        {"_id": claim_data.patient_id, "tenant_id": tenant_id}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    claim_id = str(uuid.uuid4())
    claim_id_display = f"C{random.randint(10000, 99999)}"

    claim = {
        "_id": claim_id,
        "claim_id": claim_id_display,
        "tenant_id": tenant_id,
        "patient_id": claim_data.patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "insurance_provider": claim_data.insurance_provider,
        "amount": int(claim_data.amount * 100),  # Store in cents
        "amount_display": claim_data.amount,
        "procedure_code": claim_data.procedure_code,
        "diagnosis_code": claim_data.diagnosis_code,
        "service_date": claim_data.service_date,
        "submitted_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": claim_data.description,
        "status": ClaimStatus.PENDING,
        "last_event_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.claims.insert_one(claim)

    # Create initial event
    event = {
        "_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "claim_id": claim_id,
        "event_type": "submitted",
        "description": f"Claim submitted to {claim_data.insurance_provider} for ${claim_data.amount:.2f}",
        "at": datetime.now(timezone.utc),
        "time": datetime.now(timezone.utc).strftime("%I:%M %p"),
        "created_at": datetime.now(timezone.utc),
    }

    await db.claim_events.insert_one(event)

    return {
        "claim_id": claim_id,
        "claim_id_display": claim_id_display,
        "status": ClaimStatus.PENDING,
        "message": "Claim created successfully",
    }


@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: str):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    claim = await db.claims.find_one({"_id": claim_id, "tenant_id": tenant_id})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "claim_id": claim["_id"],
        "claim_id_display": claim["claim_id"],
        "patient_name": claim["patient_name"],
        "insurance_provider": claim["insurance_provider"],
        "amount": claim["amount_display"],
        "procedure_code": claim.get("procedure_code"),
        "diagnosis_code": claim.get("diagnosis_code"),
        "service_date": claim["service_date"],
        "submitted_date": claim["submitted_date"],
        "description": claim.get("description"),
        "status": claim["status"],
    }


@app.get("/api/claims/{claim_id}/events")
async def get_claim_events(claim_id: str):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    cursor = db.claim_events.find({"claim_id": claim_id, "tenant_id": tenant_id}).sort(
        "at", 1
    )
    events = await cursor.to_list(length=100)

    return [
        {
            "event_id": event["_id"],
            "event_type": event["event_type"],
            "description": event["description"],
            "at": event["at"].strftime("%Y-%m-%d"),
            "time": event["time"],
        }
        for event in events
    ]


# ==================== APPOINTMENT ROUTES ====================


@app.get("/api/appointments")
async def list_appointments(
    date: Optional[str] = None,
    provider_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    query = {"tenant_id": tenant_id}
    if provider_id:
        query["provider_id"] = provider_id
    if patient_id:
        query["patient_id"] = patient_id

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

    # Get all unique patient IDs
    patient_ids = list(set(apt["patient_id"] for apt in appointments))

    # Batch fetch all patients
    patients_cursor = db.patients.find({"_id": {"$in": patient_ids}})
    patients_list = await patients_cursor.to_list(length=len(patient_ids))
    patients_map = {p["_id"]: p for p in patients_list}

    # Build result with patient data from map
    result = []
    for apt in appointments:
        patient = patients_map.get(apt["patient_id"])
        result.append(
            {
                "appointment_id": apt["_id"],
                "patient_name": (
                    f"{patient['first_name']} {patient['last_name']}"
                    if patient
                    else "Unknown"
                ),
                "provider_name": "Dr. James O'Brien",
                "type": apt["type"],
                "time": apt["starts_at"].strftime("%I:%M %p"),
                "starts_at": apt["starts_at"],
                "ends_at": apt["ends_at"],
                "status": apt["status"],
                "location": apt.get("location"),
                "title": apt.get("title"),
            }
        )

    return result


@app.post("/api/appointments")
async def create_appointment(appointment_data: AppointmentCreate):
    from database import get_client

    db = get_db()
    client = get_client()
    tenant_id = DEFAULT_TENANT

    appointment_id = str(uuid.uuid4())

    appointment = {
        "_id": appointment_id,
        "tenant_id": tenant_id,
        "patient_id": appointment_data.patient_id,
        "provider_id": appointment_data.provider_id,
        "type": appointment_data.type,
        "title": appointment_data.title,
        "starts_at": appointment_data.starts_at,
        "ends_at": appointment_data.ends_at,
        "location": appointment_data.location,
        "status": "scheduled",
        "google_calendar": {
            "event_id": f"mock-event-{appointment_id[:8]}",
            "calendar_id": "primary",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Use transaction to ensure atomicity
    try:
        if client:
            async with client.start_session() as session:
                async with session.start_transaction():
                    await db.appointments.insert_one(appointment, session=session)
                    await db.patients.update_one(
                        {"_id": appointment_data.patient_id},
                        {"$inc": {"appointments_count": 1}},
                        session=session,
                    )
        else:
            # Fallback without transaction
            await db.appointments.insert_one(appointment)
            await db.patients.update_one(
                {"_id": appointment_data.patient_id},
                {"$inc": {"appointments_count": 1}},
            )
    except Exception as e:
        # Fallback without transaction if session fails
        await db.appointments.insert_one(appointment)
        await db.patients.update_one(
            {"_id": appointment_data.patient_id}, {"$inc": {"appointments_count": 1}}
        )

    # Send appointment confirmation email
    try:
        from composio_integration import send_appointment_scheduled_email

        patient = await db.patients.find_one(
            {"_id": appointment_data.patient_id, "tenant_id": tenant_id}
        )
        if patient:
            patient_name = (
                f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
            )
            # Format appointment date and time
            starts_at = appointment_data.starts_at
            if isinstance(starts_at, datetime):
                appointment_date = starts_at.strftime("%Y-%m-%d")
                appointment_time = starts_at.strftime("%I:%M %p")
            else:
                # If it's a string, parse it
                try:
                    starts_at_dt = datetime.fromisoformat(
                        str(starts_at).replace("Z", "+00:00")
                    )
                    appointment_date = starts_at_dt.strftime("%Y-%m-%d")
                    appointment_time = starts_at_dt.strftime("%I:%M %p")
                except:
                    appointment_date = (
                        str(starts_at).split("T")[0] if "T" in str(starts_at) else "TBD"
                    )
                    appointment_time = "TBD"

            email_result = await send_appointment_scheduled_email(
                patient_email=patient["contact"]["email"],
                patient_name=patient_name,
                date=appointment_date,
                time=appointment_time,
                type=appointment_data.type,
                provider="Dr. James O'Brien",
            )
            print(
                f"Appointment confirmation email sent: {email_result.get('success', False)}"
            )
    except Exception as e:
        print(f"Warning: Failed to send appointment confirmation email: {e}")

    return {
        "appointment_id": appointment_id,
        "google_calendar": {
            "event_id": appointment["google_calendar"]["event_id"],
            "event_link": f"https://calendar.google.com/event?eid={appointment_id[:10]}",
        },
        "message": "Appointment created successfully",
    }


# ==================== DASHBOARD ROUTES ====================


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    db = get_db()
    tenant_id = DEFAULT_TENANT

    pending_tasks = await db.tasks.count_documents(
        {"tenant_id": tenant_id, "state": TaskState.OPEN}
    )

    today = datetime.now(timezone.utc).date()
    appointments_today = await db.appointments.count_documents(
        {
            "tenant_id": tenant_id,
            "starts_at": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()),
            },
        }
    )

    patients_total = await db.patients.count_documents({"tenant_id": tenant_id})

    claims_pending = await db.claims.count_documents(
        {"tenant_id": tenant_id, "status": ClaimStatus.PENDING}
    )

    return {
        "pending_tasks": pending_tasks,
        "appointments_today": appointments_today,
        "patients_total": patients_total,
        "claims_pending": claims_pending,
    }


@app.get("/api/dashboard/appointments")
async def get_dashboard_appointments():
    """Get today's appointments for dashboard"""
    db = get_db()
    tenant_id = DEFAULT_TENANT

    today = datetime.now(timezone.utc).date()
    cursor = db.appointments.find(
        {
            "tenant_id": tenant_id,
            "starts_at": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()),
            },
        }
    ).sort("starts_at", 1)

    appointments = await cursor.to_list(length=None)

    result = []
    for apt in appointments:
        result.append(
            {
                "appointment_id": apt["_id"],
                "patient_name": apt.get("patient_name", "Unknown"),
                "starts_at": (
                    apt["starts_at"].isoformat()
                    if isinstance(apt["starts_at"], datetime)
                    else apt["starts_at"]
                ),
                "appointment_type": apt.get("appointment_type", "consultation"),
                "provider_id": apt.get("provider_id"),
            }
        )

    return result


# ==================== CONSENT FORMS ROUTES ====================


@app.get("/api/consent-forms")
async def list_consent_forms(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    query = {"tenant_id": tenant_id}
    if patient_id:
        query["patient_id"] = patient_id
    if status:
        query["status"] = status

    cursor = db.consent_forms.find(query).skip(skip).limit(limit).sort("created_at", -1)
    forms = await cursor.to_list(length=limit)

    return [
        {
            "consent_form_id": form["_id"],
            "patient_id": form["patient_id"],
            "patient_name": form.get("patient_name"),
            "template_id": form.get("template_id"),
            "form_type": form.get("form_type"),
            "title": form.get("title"),
            "status": form.get("status"),
            "sent_at": form.get("sent_at").isoformat() if form.get("sent_at") else None,
            "signed_at": (
                form.get("signed_at").isoformat() if form.get("signed_at") else None
            ),
            "created_at": (
                form.get("created_at").isoformat() if form.get("created_at") else None
            ),
        }
        for form in forms
    ]


@app.get("/api/form-templates")
async def list_form_templates():
    db = get_db()
    tenant_id = DEFAULT_TENANT

    cursor = db.form_templates.find({"tenant_id": tenant_id}).sort("created_at", -1)
    templates = await cursor.to_list(length=100)

    return [
        {
            "template_id": template["_id"],
            "name": template.get("name"),
            "description": template.get("description"),
            "purpose": template.get("purpose"),
        }
        for template in templates
    ]


@app.post("/api/consent-forms/send")
async def send_consent_forms(data: dict):
    """Send consent forms email to patient and mark task as done"""
    db = get_db()
    tenant_id = DEFAULT_TENANT

    patient_id = data.get("patient_id")
    if not patient_id:
        raise HTTPException(status_code=400, detail="patient_id is required")

    # Get patient
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}"
    patient_email = patient["contact"]["email"]

    # Send consent form email
    try:
        from composio_integration import send_consent_form_email

        email_result = await send_consent_form_email(
            patient_email=patient_email, patient_name=patient_name
        )

        # Find and mark consent email task as done
        consent_task = await db.tasks.find_one(
            {
                "patient_id": patient_id,
                "tenant_id": tenant_id,
                "kind": "consent_forms",
                "state": "open",
            }
        )

        if consent_task and email_result.get("success"):
            await db.tasks.update_one(
                {"_id": consent_task["_id"], "tenant_id": tenant_id},
                {"$set": {"state": "done", "updated_at": datetime.now(timezone.utc)}},
            )
            print(f"Consent email task marked as done")

        return {
            "success": email_result.get("success", False),
            "message": (
                "Consent forms email sent successfully"
                if email_result.get("success")
                else "Failed to send email"
            ),
            "email_result": email_result,
        }
    except Exception as e:
        print(f"Error sending consent forms email: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send consent forms email: {str(e)}"
        )


# ==================== MCP PROXY ROUTE ====================


@app.api_route(
    "/api/special/mcp/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
)
async def special_mcp_proxy(request: Request, path: str = ""):
    """Simple proxy to MCP server on localhost:8002"""
    target_url = (
        f"http://localhost:8002/mcp/{path}" if path else "http://localhost:8002/mcp"
    )

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body(),
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


# ==================== EMAIL ENDPOINTS (Temporarily Disabled) ====================
# Note: Composio integration endpoints disabled due to import issues
# TODO: Fix composio_openai import and re-enable

# @app.post("/api/emails/send")
# async def send_email(email_data: dict):
#     """Send email via Composio Gmail integration"""
#     try:
#         result = await send_email_via_composio(
#             to_email=email_data.get("to_email"),
#             subject=email_data.get("subject"),
#             body=email_data.get("body"),
#             user_id=email_data.get("user_id", "backlinemd-system")
#         )
#         return result
#     except Exception as e:
#         logger.error(f"Error sending email: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/api/patients/{patient_id}/send-notification")
# async def send_patient_notification(patient_id: str, notification_data: dict):
#     """Send notification email to patient"""
#     try:
#         # Get patient details
#         db = get_db()
#         tenant_id = DEFAULT_TENANT
#
#         patient = await db.patients.find_one({
#             "_id": patient_id,
#             "tenant_id": tenant_id
#         })
#
#         if not patient:
#             raise HTTPException(status_code=404, detail="Patient not found")
#
#         # Send notification
#         result = await send_patient_notification_email(
#             patient_email=patient.get("email"),
#             patient_name=f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
#             notification_type=notification_data.get("type", "general"),
#             details=notification_data.get("details", {})
#         )
#
#         return result
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error sending patient notification: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
