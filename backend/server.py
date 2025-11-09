from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, File, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, List
import os
import uuid
import random
import asyncio
import json
from datetime import datetime, timedelta, timezone

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import our modules
from database import connect_db, close_db, get_db
from models import *
from auth import create_access_token, decode_token, get_password_hash, verify_password
from websocket_manager import manager

# Create FastAPI app
app = FastAPI(title="BacklineMD API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    await connect_db()
    print("\u2713 BacklineMD API started")

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()
    print("\u2713 BacklineMD API stopped")

# ==================== AUTH DEPENDENCY ====================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_tenant_id: Optional[str] = Header(None)
):
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    tenant_id = payload.get("tenant_id") or x_tenant_id
    
    if not user_id or not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return {"user_id": user_id, "tenant_id": tenant_id, "email": payload.get("email")}

# ==================== HELPER FUNCTIONS ====================

def generate_ngrams(text: str, n: int = 3) -> List[str]:
    """Generate n-grams for fuzzy search"""
    text = text.lower().replace(" ", "")
    return [text[i:i+n] for i in range(len(text) - n + 1)]

async def broadcast_event(tenant_id: str, event_type: str, op: str, doc: dict):
    """Broadcast event to WebSocket connections"""
    await manager.broadcast(tenant_id, {
        "type": event_type,
        "op": op,
        "doc": doc
    })

# ==================== AUTH ROUTES ====================

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    db = get_db()
    
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create tenant
    tenant_id = str(uuid.uuid4())
    tenant_name = user_data.tenant_name or f"{user_data.name}'s Practice"
    
    # Create user
    user_id = str(uuid.uuid4())
    user = {
        "_id": user_id,
        "tenant_id": tenant_id,
        "email": user_data.email,
        "password_hash": get_password_hash(user_data.password),
        "name": user_data.name,
        "roles": [UserRole.ADMIN],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user)
    
    # Create access token
    token = create_access_token({
        "user_id": user_id,
        "tenant_id": tenant_id,
        "email": user_data.email
    })
    
    return {
        "user": UserResponse(
            user_id=user_id,
            email=user_data.email,
            name=user_data.name,
            roles=[UserRole.ADMIN],
            tenant_id=tenant_id
        ),
        "tenant": {"tenant_id": tenant_id, "name": tenant_name},
        "token": token
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    db = get_db()
    
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({
        "user_id": user["_id"],
        "tenant_id": user["tenant_id"],
        "email": user["email"]
    })
    
    return {
        "user": UserResponse(
            user_id=user["_id"],
            email=user["email"],
            name=user["name"],
            roles=user["roles"],
            tenant_id=user["tenant_id"]
        ),
        "token": token,
        "tenant_id": user["tenant_id"]
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    db = get_db()
    user = await db.users.find_one({"_id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        user_id=user["_id"],
        email=user["email"],
        name=user["name"],
        roles=user["roles"],
        tenant_id=user["tenant_id"]
    )

# ==================== PATIENT ROUTES ====================

@app.get("/api/patients")
async def list_patients(
    q: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if q:
        # Search using n-grams
        ngrams = generate_ngrams(q)
        query["search.ngrams"] = {"$in": ngrams}
    
    cursor = db.patients.find(query).skip(skip).limit(limit).sort("created_at", -1)
    patients = await cursor.to_list(length=limit)
    
    result = []
    for p in patients:
        result.append({
            "patient_id": p["_id"],
            "first_name": p["first_name"],
            "last_name": p["last_name"],
            "email": p["contact"]["email"],
            "phone": p["contact"]["phone"],
            "status": p.get("status", "Active"),
            "tasks_count": p.get("tasks_count", 0),
            "appointments_count": p.get("appointments_count", 0),
            "flagged_count": p.get("flagged_count", 0),
            "profile_image": p.get("profile_image")
        })
    
    return result

@app.post("/api/patients")
async def create_patient(
    patient_data: PatientCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
            "address": patient_data.address or {}
        },
        "preconditions": patient_data.preconditions or [],
        "flags": [],
        "latest_vitals": {},
        "profile_image": patient_data.profile_image,
        "status": "Active",
        "tasks_count": 0,
        "appointments_count": 0,
        "flagged_count": 0,
        "search": {"ngrams": ngrams},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user["user_id"]
    }
    
    await db.patients.insert_one(patient)
    
    # Broadcast event
    await broadcast_event(tenant_id, "patient", "insert", {
        "patient_id": patient_id,
        "name": full_name
    })
    
    return {"patient_id": patient_id, "message": "Patient created successfully"}

@app.get("/api/patients/{patient_id}")
async def get_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
        "age": patient.get("age", 34)
    }

@app.get("/api/patients/{patient_id}/summary")
async def get_patient_summary(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    # Check if cached
    cached = await db.ai_artifacts.find_one({
        "tenant_id": tenant_id,
        "kind": "patient_summary",
        "subject.patient_id": patient_id
    })
    
    if cached and cached.get("expires_at") > datetime.utcnow():
        return cached["payload"]
    
    # Generate mock summary
    patient = await db.patients.find_one({"_id": patient_id, "tenant_id": tenant_id})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    summary_text = f"{patient.get('age', 34)}-year-old {patient['gender'].lower()} patient with documented {', '.join(patient.get('preconditions', ['family history of heart disease']))}. Currently under {patient.get('status', 'active').lower()}. Initial consultation completed with comprehensive medical history review. Recent vitals show stable condition. Recommended follow-up in 4-6 weeks."
    
    payload = {
        "summary": summary_text,
        "citations": [
            {"doc_id": "DOC123", "kind": "lab", "page": 2, "excerpt": "Cholesterol: 205 mg/dL"},
            {"doc_id": "DOC124", "kind": "imaging", "page": 1, "excerpt": "X-Ray: No abnormalities"}
        ],
        "generated_at": datetime.utcnow().isoformat(),
        "model": "gpt-4"
    }
    
    # Cache it
    await db.ai_artifacts.insert_one({
        "_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "kind": "patient_summary",
        "subject": {"patient_id": patient_id},
        "payload": payload,
        "model": "gpt-4",
        "score": 0.95,
        "expires_at": datetime.utcnow() + timedelta(hours=1),
        "created_at": datetime.utcnow()
    })
    
    return payload

# ==================== DOCUMENT ROUTES ====================

@app.get("/api/documents")
async def list_documents(
    patient_id: Optional[str] = None,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
            "created_at": doc["created_at"]
        }
        for doc in documents
    ]

@app.post("/api/documents/upload")
async def upload_document(
    patient_id: str,
    kind: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
            "sha256": "mock-hash"
        },
        "ocr": {"done": False, "engine": None},
        "extracted": {},
        "status": DocumentStatus.UPLOADED,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.documents.insert_one(document)
    
    # Trigger document extraction agent (async)
    asyncio.create_task(trigger_document_extraction(document_id, tenant_id))
    
    return {
        "document_id": document_id,
        "status": DocumentStatus.UPLOADED,
        "message": "Document uploaded successfully"
    }

@app.get("/api/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
        "created_at": document["created_at"]
    }

@app.patch("/api/documents/{document_id}")
async def update_document(
    document_id: str,
    update_data: DocumentUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    update_fields = {}
    if update_data.status:
        update_fields["status"] = update_data.status
    if update_data.extracted:
        update_fields["extracted"] = update_data.extracted
    
    update_fields["updated_at"] = datetime.utcnow()
    
    result = await db.documents.update_one(
        {"_id": document_id, "tenant_id": tenant_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Broadcast event
    await broadcast_event(tenant_id, "document", "update", {
        "document_id": document_id,
        "status": update_data.status
    })
    
    return {"message": "Document updated successfully"}

# ==================== MOCK AGENT FUNCTION ====================

async def trigger_document_extraction(document_id: str, tenant_id: str):
    \"\"\"Mock document extraction agent\"\"\"
    db = get_db()
    
    # Wait 2 seconds
    await asyncio.sleep(2)
    
    # Update status to ingesting
    await db.documents.update_one(
        {"_id": document_id},
        {"$set": {"status": DocumentStatus.INGESTING}}
    )
    
    await broadcast_event(tenant_id, "document", "update", {
        "document_id": document_id,
        "status": DocumentStatus.INGESTING
    })
    
    # Wait 3 more seconds
    await asyncio.sleep(3)
    
    # Simulate extraction
    confidence = random.uniform(0.75, 0.98)
    
    extracted_data = {
        "blood_type": "O+",
        "cholesterol": "205 mg/dL",
        "bp": "125/80",
        "hr": 68,
        "confidence": confidence
    }
    
    status = DocumentStatus.INGESTED if confidence > 0.9 else DocumentStatus.NOT_INGESTED
    
    await db.documents.update_one(
        {"_id": document_id},
        {"$set": {
            "status": status,
            "extracted": {
                "fields": extracted_data,
                "confidence": confidence,
                "needs_review": [] if confidence > 0.9 else ["cholesterol"]
            }
        }}
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
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.tasks.insert_one(task)
        
        # Increment patient task count
        await db.patients.update_one(
            {"_id": doc["patient_id"]},
            {"$inc": {"tasks_count": 1}}
        )
        
        # Broadcast task
        await broadcast_event(tenant_id, "task", "insert", {
            "task_id": task_id,
            "title": task["title"],
            "patient_name": task["patient_name"]
        })
    
    # Broadcast document update
    await broadcast_event(tenant_id, "document", "update", {
        "document_id": document_id,
        "status": status
    })

# ==================== TASK ROUTES ====================

@app.get("/api/tasks")
async def list_tasks(
    state: Optional[str] = None,
    patient_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
            "created_at": task["created_at"]
        }
        for task in tasks
    ]

@app.post("/api/tasks")
async def create_task(
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    # Get patient name
    patient = await db.patients.find_one({"_id": task_data.patient_id, "tenant_id": tenant_id})
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
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "created_by": current_user["user_id"]
    }
    
    await db.tasks.insert_one(task)
    
    # Increment patient task count
    await db.patients.update_one(
        {"_id": task_data.patient_id},
        {"$inc": {"tasks_count": 1}}
    )
    
    # Broadcast event
    await broadcast_event(tenant_id, "task", "insert", {
        "task_id": task_id,
        "title": task["title"]
    })
    
    return {"task_id": task_id, "message": "Task created successfully"}

@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    update_fields = {}
    if update_data.state:
        update_fields["state"] = update_data.state
    if update_data.comment:
        update_fields["$push"] = {"comments": {
            "user_id": current_user["user_id"],
            "text": update_data.comment,
            "created_at": datetime.utcnow()
        }}
    
    update_fields["updated_at"] = datetime.utcnow()
    
    result = await db.tasks.update_one(
        {"_id": task_id, "tenant_id": tenant_id},
        {"$set": update_fields}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Broadcast event
    await broadcast_event(tenant_id, "task", "update", {
        "task_id": task_id,
        "state": update_data.state
    })
    
    return {"message": "Task updated successfully"}

# ==================== CLAIM ROUTES ====================

@app.get("/api/claims")
async def list_claims(
    status: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
            "last_event_at": claim.get("last_event_at")
        }
        for claim in claims
    ]

@app.post("/api/claims")
async def create_claim(
    claim_data: ClaimCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    # Get patient
    patient = await db.patients.find_one({"_id": claim_data.patient_id, "tenant_id": tenant_id})
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
        "submitted_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "description": claim_data.description,
        "status": ClaimStatus.PENDING,
        "last_event_at": datetime.utcnow(),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.claims.insert_one(claim)
    
    # Create initial event
    event = {
        "_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "claim_id": claim_id,
        "event_type": "submitted",
        "description": f"Claim submitted to {claim_data.insurance_provider} for ${claim_data.amount:.2f}",
        "at": datetime.utcnow(),
        "time": datetime.utcnow().strftime("%I:%M %p"),
        "created_at": datetime.utcnow()
    }
    
    await db.claim_events.insert_one(event)
    
    # Broadcast event
    await broadcast_event(tenant_id, "claim", "insert", {
        "claim_id": claim_id,
        "patient_name": claim["patient_name"]
    })
    
    return {
        "claim_id": claim_id,
        "claim_id_display": claim_id_display,
        "status": ClaimStatus.PENDING,
        "message": "Claim created successfully"
    }

@app.get("/api/claims/{claim_id}")
async def get_claim(
    claim_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
        "status": claim["status"]
    }

@app.get("/api/claims/{claim_id}/events")
async def get_claim_events(
    claim_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    cursor = db.claim_events.find({"claim_id": claim_id, "tenant_id": tenant_id}).sort("at", 1)
    events = await cursor.to_list(length=100)
    
    return [
        {
            "event_id": event["_id"],
            "event_type": event["event_type"],
            "description": event["description"],
            "at": event["at"].strftime("%Y-%m-%d"),
            "time": event["time"]
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
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    query = {"tenant_id": tenant_id}
    if provider_id:
        query["provider_id"] = provider_id
    if patient_id:
        query["patient_id"] = patient_id
    
    if date == "today":
        today = datetime.utcnow().date()
        query["starts_at"] = {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    elif date:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        query["starts_at"] = {
            "$gte": datetime.combine(date_obj, datetime.min.time()),
            "$lt": datetime.combine(date_obj + timedelta(days=1), datetime.min.time())
        }
    
    cursor = db.appointments.find(query).sort("starts_at", 1).limit(limit)
    appointments = await cursor.to_list(length=limit)
    
    result = []
    for apt in appointments:
        patient = await db.patients.find_one({"_id": apt["patient_id"]})
        result.append({
            "appointment_id": apt["_id"],
            "patient_name": f"{patient['first_name']} {patient['last_name']}" if patient else "Unknown",
            "provider_name": "Dr. James O'Brien",
            "type": apt["type"],
            "time": apt["starts_at"].strftime("%I:%M %p"),
            "starts_at": apt["starts_at"],
            "ends_at": apt["ends_at"],
            "status": apt["status"],
            "location": apt.get("location"),
            "title": apt.get("title")
        })
    
    return result

@app.post("/api/appointments")
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
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
            "calendar_id": "primary"
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.appointments.insert_one(appointment)
    
    # Increment patient appointment count
    await db.patients.update_one(
        {"_id": appointment_data.patient_id},
        {"$inc": {"appointments_count": 1}}
    )
    
    # Broadcast event
    await broadcast_event(tenant_id, "appointment", "insert", {
        "appointment_id": appointment_id,
        "patient_id": appointment_data.patient_id
    })
    
    return {
        "appointment_id": appointment_id,
        "google_calendar": {
            "event_id": appointment["google_calendar"]["event_id"],
            "event_link": f"https://calendar.google.com/event?eid={appointment_id[:10]}"
        },
        "message": "Appointment created successfully"
    }

# ==================== DASHBOARD ROUTES ====================

@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    db = get_db()
    tenant_id = current_user["tenant_id"]
    
    pending_tasks = await db.tasks.count_documents({
        "tenant_id": tenant_id,
        "state": TaskState.OPEN
    })
    
    today = datetime.utcnow().date()
    appointments_today = await db.appointments.count_documents({
        "tenant_id": tenant_id,
        "starts_at": {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time())
        }
    })
    
    patients_total = await db.patients.count_documents({"tenant_id": tenant_id})
    
    claims_pending = await db.claims.count_documents({
        "tenant_id": tenant_id,
        "status": ClaimStatus.PENDING
    })
    
    return {
        "pending_tasks": pending_tasks,
        "appointments_today": appointments_today,
        "patients_total": patients_total,
        "claims_pending": claims_pending
    }

# ==================== WEBSOCKET ROUTE ====================

@app.websocket("/ws/tenant/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Handle subscriptions if needed
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(websocket, tenant_id)

# ==================== COPILOT ENDPOINT ====================

@app.post("/api/copilot")
async def copilot_endpoint(request: dict):
    \"\"\"Simple CopilotKit endpoint\"\"\"
    return {
        "response": "I'm here to help with BacklineMD. How can I assist you today?",
        "context": "Dashboard"
    }
