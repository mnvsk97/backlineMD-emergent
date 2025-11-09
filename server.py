import asyncio
import os
import random
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Import our modules
from database import close_db, connect_db, get_db
from logger import (
    get_logger
)
from models import *



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

    patient = {
        "_id": patient_id,
        "tenant_id": tenant_id,
        "mrn": mrn,
        "first_name": patient_data.first_name,
        "last_name": patient_data.last_name,
        "dob": patient_data.dob,
        "gender": patient_data.gender,
        "contact": {
            "email": patient_data.email,
            "phone": patient_data.phone,
            "address": patient_data.address or {},
        },
        "preconditions": patient_data.preconditions or [],
        "flags": [],
        "latest_vitals": {},
        "profile_image": patient_data.profile_image,
        "status": "Intake In Progress",  # Default initial status
        "tasks_count": 0,
        "appointments_count": 0,
        "flagged_count": 0,
        "search": {"ngrams": ngrams},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": "demo-user",
    }

    await db.patients.insert_one(patient)

    return {"patient_id": patient_id, "message": "Patient created successfully"}


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return {
        "patient_id": patient["_id"],
        "mrn": patient["mrn"],
        "first_name": patient["first_name"],
        "last_name": patient["last_name"],
        "dob": patient["dob"],
        "gender": patient["gender"],
        "email": patient["contact"]["email"],
        "phone": patient["contact"]["phone"],
        "address": patient["contact"].get("address"),
        "preconditions": patient.get("preconditions", []),
        "latest_vitals": patient.get("latest_vitals", {}),
        "profile_image": patient.get("profile_image"),
        "status": patient.get("status"),
        "tasks_count": patient.get("tasks_count", 0),
        "appointments_count": patient.get("appointments_count", 0),
        "flagged_count": patient.get("flagged_count", 0),
        "age": patient.get("age", 34),
    }


@app.patch("/api/patients/{patient_id}")
async def update_patient(patient_id: str, patient_data: PatientUpdate):
    """Update patient information"""
    db = get_db()
    tenant_id = DEFAULT_TENANT

    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_fields = {}
    
    if patient_data.first_name is not None:
        update_fields["first_name"] = patient_data.first_name
    if patient_data.last_name is not None:
        update_fields["last_name"] = patient_data.last_name
    if patient_data.dob is not None:
        update_fields["dob"] = patient_data.dob
    if patient_data.gender is not None:
        update_fields["gender"] = patient_data.gender
    if patient_data.email is not None:
        if "contact" not in update_fields:
            update_fields["contact"] = patient.get("contact", {})
        update_fields["contact"]["email"] = patient_data.email
    if patient_data.phone is not None:
        if "contact" not in update_fields:
            update_fields["contact"] = patient.get("contact", {})
        update_fields["contact"]["phone"] = patient_data.phone
    if patient_data.preconditions is not None:
        update_fields["preconditions"] = patient_data.preconditions
    if patient_data.latest_vitals is not None:
        update_fields["latest_vitals"] = patient_data.latest_vitals
    if patient_data.status is not None:
        update_fields["status"] = patient_data.status
    if patient_data.insurance_provider is not None:
        if "insurance" not in update_fields:
            update_fields["insurance"] = patient.get("insurance", {})
        update_fields["insurance"]["provider"] = patient_data.insurance_provider
    if patient_data.insurance_policy_number is not None:
        if "insurance" not in update_fields:
            update_fields["insurance"] = patient.get("insurance", {})
        update_fields["insurance"]["policy_number"] = patient_data.insurance_policy_number
    if patient_data.insurance_group_number is not None:
        if "insurance" not in update_fields:
            update_fields["insurance"] = patient.get("insurance", {})
        update_fields["insurance"]["group_number"] = patient_data.insurance_group_number
    if patient_data.insurance_effective_date is not None:
        if "insurance" not in update_fields:
            update_fields["insurance"] = patient.get("insurance", {})
        update_fields["insurance"]["effective_date"] = patient_data.insurance_effective_date
    if patient_data.insurance_expiry_date is not None:
        if "insurance" not in update_fields:
            update_fields["insurance"] = patient.get("insurance", {})
        update_fields["insurance"]["expiry_date"] = patient_data.insurance_expiry_date
    
    # Recalculate age if DOB changed
    if patient_data.dob is not None:
        from dateutil.parser import parse as parse_date
        dob = parse_date(patient_data.dob)
        today = datetime.now(timezone.utc)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        update_fields["age"] = age
    
    update_fields["updated_at"] = datetime.now(timezone.utc)
    
    # Regenerate search n-grams if name changed
    if patient_data.first_name is not None or patient_data.last_name is not None:
        first_name = update_fields.get("first_name", patient["first_name"])
        last_name = update_fields.get("last_name", patient["last_name"])
        full_name = f"{first_name} {last_name}"
        update_fields["search"] = {"ngrams": generate_ngrams(full_name)}

    await db.patients.update_one(
        {"_id": patient_id, "tenant_id": tenant_id},
        {"$set": update_fields}
    )

    return {"message": "Patient updated successfully"}


@app.get("/api/patients/{patient_id}/summary")
async def get_patient_summary(patient_id: str):
    db = get_db()
    tenant_id = DEFAULT_TENANT

    # Check if cached
    cached = await db.ai_artifacts.find_one(
        {
            "tenant_id": tenant_id,
            "kind": "patient_summary",
            "subject.patient_id": patient_id,
        }
    )

    if cached and cached.get("expires_at"):
        expires_at = cached["expires_at"]
        # Handle both datetime objects and strings
        if isinstance(expires_at, str):
            from dateutil.parser import isoparse
            expires_at = isoparse(expires_at)
        # Ensure both are timezone-aware
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > datetime.now(timezone.utc):
            return cached["payload"]

    # If no cache, generate summary using real data
    # Call the regenerate endpoint logic
    return await regenerate_patient_summary(patient_id)


@app.post("/api/patients/{patient_id}/summary/regenerate")
async def regenerate_patient_summary(patient_id: str):
    """Regenerate patient summary using OpenAI"""
    import os
    from openai import OpenAI
    
    db = get_db()
    tenant_id = DEFAULT_TENANT
    
    # Get patient
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get patient documents
    documents = await db.documents.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).limit(10).to_list(length=10)
    
    # Get patient tasks
    tasks = await db.tasks.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).limit(20).to_list(length=20)
    
    # Get patient appointments
    appointments = await db.appointments.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("starts_at", -1).limit(10).to_list(length=10)
    
    # Get patient notes
    notes = await db.notes.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).limit(10).to_list(length=10)
    
    # Build comprehensive patient information
    patient_age = patient.get('age')
    if not patient_age and patient.get('date_of_birth'):
        from datetime import date
        dob = patient.get('date_of_birth')
        if isinstance(dob, str):
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            except:
                dob_date = None
        elif hasattr(dob, 'date'):
            dob_date = dob.date() if hasattr(dob, 'date') else None
        else:
            dob_date = None
        if dob_date:
            today = date.today()
            patient_age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
    
    # Build documents summary with detailed extracted data
    docs_info = ""
    if documents:
        docs_info = f"\n**Medical Documents ({len(documents)} total):**\n"
        for doc in documents[:10]:  # Top 10 documents
            doc_kind = doc.get("kind", "unknown")
            doc_status = doc.get("status", "unknown")
            extracted = doc.get("extracted", {})
            file_name = doc.get("file_name", "Unknown")
            
            docs_info += f"- **{doc_kind}** ({doc_status}): {file_name}\n"
            if extracted:
                # Format extracted data nicely
                if isinstance(extracted, dict):
                    for key, value in extracted.items():
                        if value:
                            docs_info += f"  - {key}: {value}\n"
                else:
                    docs_info += f"  - Extracted data: {str(extracted)[:200]}\n"
    else:
        docs_info = "\n**Medical Documents:** No documents have been provided or reviewed.\n"
    
    # Build tasks summary
    tasks_info = ""
    if tasks:
        tasks_info = f"\n**Tasks and Activities ({len(tasks)} total):**\n"
        for task in tasks[:15]:  # Top 15 tasks
            task_title = task.get("title", "")
            task_desc = task.get("description", "")
            task_state = task.get("state", "")
            task_agent = task.get("agent_type", "human")
            task_priority = task.get("priority", "")
            created_at = task.get("created_at", datetime.now(timezone.utc))
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.now(timezone.utc)
            created_str = created_at.strftime("%Y-%m-%d") if hasattr(created_at, 'strftime') else str(created_at)[:10]
            
            tasks_info += f"- **{task_title}** ({task_state}, {task_agent}, priority: {task_priority}) - {created_str}\n"
            if task_desc:
                tasks_info += f"  Description: {task_desc[:150]}\n"
    else:
        tasks_info = "\n**Tasks and Activities:** No tasks or activities have been recorded.\n"
    
    # Build appointments summary
    appointments_info = ""
    if appointments:
        appointments_info = f"\n**Appointments ({len(appointments)} total):**\n"
        for apt in appointments[:10]:  # Top 10 appointments
            apt_title = apt.get("title", apt.get("type", "Appointment"))
            apt_status = apt.get("status", "")
            apt_date = apt.get("starts_at")
            if apt_date:
                if isinstance(apt_date, str):
                    try:
                        apt_date = datetime.fromisoformat(apt_date.replace('Z', '+00:00'))
                    except:
                        apt_date = None
                if apt_date and hasattr(apt_date, 'strftime'):
                    apt_date_str = apt_date.strftime("%Y-%m-%d %H:%M")
                else:
                    apt_date_str = str(apt_date)[:16]
            else:
                apt_date_str = "Not scheduled"
            
            appointments_info += f"- **{apt_title}** ({apt_status}) - {apt_date_str}\n"
    else:
        appointments_info = "\n**Appointments:** No appointments have been scheduled.\n"
    
    # Build notes summary
    notes_info = ""
    if notes:
        notes_info = f"\n**Clinical Notes ({len(notes)} total):**\n"
        for note in notes[:10]:  # Top 10 notes
            note_content = note.get("content", "")
            note_author = note.get("author", "Unknown")
            note_date = note.get("created_at", datetime.now(timezone.utc))
            if isinstance(note_date, str):
                try:
                    note_date = datetime.fromisoformat(note_date.replace('Z', '+00:00'))
                except:
                    note_date = datetime.now(timezone.utc)
            note_date_str = note_date.strftime("%Y-%m-%d") if hasattr(note_date, 'strftime') else str(note_date)[:10]
            
            notes_info += f"- **{note_date_str}** by {note_author}: {note_content[:200]}\n"
    else:
        notes_info = "\n**Clinical Notes:** No clinical notes have been documented.\n"
    
    # Build patient demographics
    preconditions_str = ", ".join(patient.get('preconditions', [])) if patient.get('preconditions') else "None documented"
    vitals = patient.get('latest_vitals', {})
    vitals_str = ""
    if vitals:
        vitals_str = "\n**Latest Vital Signs:**\n"
        for key, value in vitals.items():
            vitals_str += f"- {key}: {value}\n"
    else:
        vitals_str = "\n**Latest Vital Signs:** Not available\n"
    
    # Prepare comprehensive prompt for OpenAI
    patient_info = f"""
**Patient Demographics:**
- Name: {patient.get('first_name', '')} {patient.get('last_name', '')}
- Age: {patient_age if patient_age else 'Not specified'}
- Gender: {patient.get('gender', 'Not specified')}
- Date of Birth: {patient.get('date_of_birth', 'Not specified')}
- Status: {patient.get('status', 'Not specified')}
- Preconditions/Medical History: {preconditions_str}
{vitals_str}
"""
    
    prompt = f"""You are an experienced medical professional generating a comprehensive clinical summary for a patient. Think like a doctor reviewing a patient case.

{patient_info}
{docs_info}
{tasks_info}
{appointments_info}
{notes_info}

Generate a concise 23-line medical summary in plain text format, like a doctor's note:

Line 1: Age, gender, and brief chief complaint/status (e.g., "43 M with [condition/status]")
Line 2 and 3: Key findings or current clinical status or any other relevant latest info from activities and stage.

Important guidelines:
- Keep it brief and clinical - maximum 2 lines
- DO NOT make up or assume any information not provided
- Use professional medical terminology
- Only include information that is explicitly provided in the data above
- Format as simple plain text, no headers or structure
"""
    
    # Call OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        client = OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an experienced physician generating clinical summaries for patient cases. Think critically about the available information, identify key clinical findings, and provide actionable recommendations. Only use information explicitly provided - never fabricate or assume details. Use professional medical terminology and maintain clinical objectivity."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        
        summary_text = response.choices[0].message.content

        payload = {
            "summary": summary_text,
            "citations": [
                {
                    "doc_id": doc["_id"],
                    "kind": doc.get("kind", "unknown"),
                    "excerpt": str(doc.get("extracted", {}))[:200],
                }
                for doc in documents[:5]
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": "gpt-4o",
        }
        
        # Cache it (invalidate old cache first)
        await db.ai_artifacts.delete_many(
            {
                "tenant_id": tenant_id,
                "kind": "patient_summary",
                "subject.patient_id": patient_id,
            }
        )
        
        await db.ai_artifacts.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "kind": "patient_summary",
                "subject": {"patient_id": patient_id},
                "payload": payload,
                "model": "gpt-4o",
                "score": 0.95,
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
                "created_at": datetime.now(timezone.utc),
            }
        )

        return payload
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@app.get("/api/patients/{patient_id}/notes")
async def get_patient_notes(patient_id: str):
    """Get all notes for a patient"""
    db = get_db()
    tenant_id = DEFAULT_TENANT
    
    # Verify patient exists
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    cursor = db.notes.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1)
    notes = await cursor.to_list(length=100)
    
    return [
        {
            "note_id": note["_id"],
            "patient_id": note["patient_id"],
            "content": note["content"],
            "author": note.get("author", "Unknown"),
            "created_at": note.get("created_at", datetime.now(timezone.utc)),
            "date": note.get("created_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d") if isinstance(note.get("created_at"), datetime) else note.get("created_at", ""),
        }
        for note in notes
    ]


@app.post("/api/patients/{patient_id}/notes")
async def create_patient_note(patient_id: str, note_data: dict):
    """Create a new note for a patient"""
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
        "author": note_data.get("author", "Dr. James O'Brien"),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    
    await db.notes.insert_one(note)
    
    return {
        "note_id": note_id,
        "message": "Note created successfully",
    }


@app.get("/api/patients/{patient_id}/activities")
async def get_patient_activities(patient_id: str):
    """Get all activities for a patient (tasks, appointments, documents, notes)"""
    db = get_db()
    tenant_id = DEFAULT_TENANT
    
    # Verify patient exists
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    activities = []
    
    # Get tasks
    tasks = await db.tasks.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).limit(50).to_list(length=50)
    
    for task in tasks:
        activities.append({
            "activity_id": task["_id"],
            "type": "task",
            "agent_type": task.get("agent_type", "human"),
            "title": task.get("title", ""),
            "description": task.get("description", ""),
            "status": task.get("state", ""),
            "priority": task.get("priority", ""),
            "created_at": task.get("created_at", datetime.now(timezone.utc)),
            "time_ago": _get_time_ago(task.get("created_at", datetime.now(timezone.utc))),
        })
    
    # Get appointments
    appointments = await db.appointments.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("starts_at", -1).limit(50).to_list(length=50)
    
    for apt in appointments:
        activities.append({
            "activity_id": apt["_id"],
            "type": "appointment",
            "agent_type": "human",
            "title": apt.get("title", "Appointment"),
            "description": f"Appointment scheduled for {apt.get('starts_at', '').strftime('%Y-%m-%d %I:%M %p') if isinstance(apt.get('starts_at'), datetime) else apt.get('starts_at', '')}",
            "status": apt.get("status", ""),
            "created_at": apt.get("starts_at", apt.get("created_at", datetime.now(timezone.utc))),
            "time_ago": _get_time_ago(apt.get("starts_at", apt.get("created_at", datetime.now(timezone.utc)))),
        })
    
    # Get documents
    documents = await db.documents.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).limit(50).to_list(length=50)
    
    for doc in documents:
        activities.append({
            "activity_id": doc["_id"],
            "type": "document",
            "agent_type": "ai" if doc.get("status") == "ingested" else "human",
            "title": f"{doc.get('kind', 'Document').replace('_', ' ').title()} uploaded",
            "description": f"Document {doc.get('file', {}).get('name', '')} - Status: {doc.get('status', '')}",
            "status": doc.get("status", ""),
            "created_at": doc.get("created_at", datetime.now(timezone.utc)),
            "time_ago": _get_time_ago(doc.get("created_at", datetime.now(timezone.utc))),
        })
    
    # Get notes
    notes = await db.notes.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).limit(50).to_list(length=50)
    
    for note in notes:
        activities.append({
            "activity_id": note["_id"],
            "type": "note",
            "agent_type": "human",
            "title": f"Note added by {note.get('author', 'Unknown')}",
            "description": note.get("content", "")[:200],
            "status": "completed",
            "created_at": note.get("created_at", datetime.now(timezone.utc)),
            "time_ago": _get_time_ago(note.get("created_at", datetime.now(timezone.utc))),
        })
    
    # Sort by created_at descending
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    
    return activities


def _get_time_ago(dt):
    """Helper function to get human-readable time ago"""
    if isinstance(dt, str):
        from dateutil.parser import isoparse
        dt = isoparse(dt)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


@app.get("/api/patients/{patient_id}/documents/summary")
async def get_documents_summary(patient_id: str):
    """Get summary of all documents for a patient"""
    db = get_db()
    tenant_id = DEFAULT_TENANT
    
    # Verify patient exists
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    documents = await db.documents.find(
        {"patient_id": patient_id, "tenant_id": tenant_id}
    ).sort("created_at", -1).to_list(length=100)
    
    summary = {
        "total_documents": len(documents),
        "by_kind": {},
        "by_status": {},
        "recent_documents": [],
        "extracted_data": [],
    }
    
    for doc in documents:
        kind = doc.get("kind", "unknown")
        status = doc.get("status", "unknown")
        
        summary["by_kind"][kind] = summary["by_kind"].get(kind, 0) + 1
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
        
        if len(summary["recent_documents"]) < 10:
            summary["recent_documents"].append({
                "document_id": doc["_id"],
                "kind": kind,
                "status": status,
                "created_at": doc.get("created_at", datetime.now(timezone.utc)),
                "file_name": doc.get("file", {}).get("name", "Unknown"),
            })
        
        if doc.get("extracted"):
            summary["extracted_data"].append({
                "document_id": doc["_id"],
                "kind": kind,
                "extracted": doc.get("extracted", {}),
            })
    
    return summary


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
    if patient_id:
        query["patient_id"] = patient_id
    if assignee_id:
        query["assignee_id"] = assignee_id
    if priority:
        query["priority"] = priority

    cursor = db.tasks.find(query).skip(skip).limit(limit).sort("created_at", -1)
    tasks = await cursor.to_list(length=limit)

    return [
        {
            "task_id": task["task_id"],
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

    # Try to find task by _id first, then by task_id
    task = await db.tasks.find_one({"tenant_id": tenant_id, "_id": task_id})
    if not task:
        task = await db.tasks.find_one({"tenant_id": tenant_id, "task_id": task_id})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task_id = task["_id"]

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
                {"_id": appointment_data.patient_id}, {"$inc": {"appointments_count": 1}}
            )
    except Exception as e:
        # Fallback without transaction if session fails
        await db.appointments.insert_one(appointment)
        await db.patients.update_one(
            {"_id": appointment_data.patient_id}, {"$inc": {"appointments_count": 1}}
        )

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
        result.append({
            "appointment_id": apt["_id"],
            "patient_name": apt.get("patient_name", "Unknown"),
            "starts_at": apt["starts_at"].isoformat() if isinstance(apt["starts_at"], datetime) else apt["starts_at"],
            "appointment_type": apt.get("appointment_type", "consultation"),
            "provider_id": apt.get("provider_id"),
        })

    return result



# ==================== EMAIL ENDPOINTS ====================

@app.post("/api/patients/{patient_id}/send-notification")
async def send_patient_notification(patient_id: str, notification_data: dict):
    """Send notification email to patient"""
    try:
        # Get patient details
        db = get_db()
        tenant_id = DEFAULT_TENANT
        
        patient = await db.patients.find_one({
            "_id": patient_id,
            "tenant_id": tenant_id
        })
        
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Send notification (stub - implement email sending logic here)
        # TODO: Implement email sending via Composio or other email service
        result = {
            "success": True,
            "message": "Notification sent successfully (stub)",
            "patient_email": patient.get("email"),
            "notification_type": notification_data.get("type", "general"),
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending patient notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

