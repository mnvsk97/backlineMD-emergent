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

# Continue in next file due to size...
