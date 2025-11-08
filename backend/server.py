from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="BacklineMD API")
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================

class Patient(BaseModel):
    model_config = ConfigDict(extra="ignore")
    patient_id: str = Field(default_factory=lambda: f"PAT-{uuid.uuid4().hex[:8].upper()}")
    first_name: str
    last_name: str
    email: str
    phone: str
    age: Optional[int] = None
    gender: Optional[str] = None
    status: Literal["intake", "processing", "review", "approved", "scheduled"] = "intake"
    flagged_items: int = 0
    tasks_count: int = 0
    appointments_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    age: Optional[int] = None
    gender: Optional[str] = None

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    task_id: str = Field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:8].upper()}")
    title: str
    description: str
    patient_id: str
    patient_name: str
    agent_type: str
    status: Literal["pending", "in_progress", "awaiting_approval", "completed", "rejected"] = "awaiting_approval"
    priority: Literal["low", "medium", "high", "urgent"] = "high"
    confidence_score: float
    ai_context: dict
    suggested_actions: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    waiting_minutes: int = 0

class TaskDecision(BaseModel):
    decision: Literal["approve", "reject", "approve_with_followup"]
    notes: Optional[str] = None

class AgentExecution(BaseModel):
    model_config = ConfigDict(extra="ignore")
    execution_id: str = Field(default_factory=lambda: f"EXEC-{uuid.uuid4().hex[:8].upper()}")
    agent_type: str
    patient_id: str
    patient_name: str
    status: Literal["queued", "running", "completed", "failed"] = "running"
    progress: int = 0
    current_step: str = ""
    duration_seconds: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatCard(BaseModel):
    title: str
    value: str
    subtitle: str
    icon: str
    color: str

class Appointment(BaseModel):
    time: str
    type: str
    patient_name: str
    doctor: str

# ==================== MOCK DATA INITIALIZATION ====================

async def init_mock_data():
    """Initialize mock data on startup"""
    # Check if data exists
    patient_count = await db.patients.count_documents({})
    if patient_count > 0:
        return
    
    # Create mock patients
    mock_patients = [
        {
            "patient_id": "PAT-ALEX001",
            "first_name": "Alex",
            "last_name": "Rodriguez",
            "email": "mmvsk97+alex@gmail.com",
            "phone": "+14159050147",
            "age": 34,
            "gender": "Male",
            "status": "Insurance Verification",
            "flagged_items": 1,
            "tasks_count": 1,
            "appointments_count": 7,
            "profile_image": "https://i.pravatar.cc/150?img=12",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "patient_id": "PAT-EMMA002",
            "first_name": "Emma",
            "last_name": "Watson",
            "email": "emma.watson@example.com",
            "phone": "+14155552222",
            "age": 32,
            "gender": "Female",
            "status": "Document Review",
            "flagged_items": 2,
            "tasks_count": 2,
            "appointments_count": 3,
            "profile_image": "https://i.pravatar.cc/150?img=45",
            "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        },
        {
            "patient_id": "PAT-DAVID003",
            "first_name": "David",
            "last_name": "Anderson",
            "email": "mmvsk97+david@gmail.com",
            "phone": "+14155553333",
            "age": 38,
            "gender": "Male",
            "status": "Ready for Treatment",
            "flagged_items": 0,
            "tasks_count": 0,
            "appointments_count": 1,
            "profile_image": "https://i.pravatar.cc/150?img=33",
            "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        }
    ]
    await db.patients.insert_many(mock_patients)
    
    # Create mock tasks
    mock_tasks = [
        {
            "task_id": "TASK-INS001",
            "title": "Review Insurance Coverage",
            "description": "Insurance provider fertility coverage needs manual verification",
            "patient_id": "PAT-EMMA002",
            "patient_name": "Emma Watson",
            "agent_type": "insurance_validator",
            "status": "awaiting_approval",
            "priority": "high",
            "confidence_score": 0.72,
            "ai_context": {
                "provider": "Aetna PPO",
                "policy_number": "AC-12345-XY",
                "issue": "Fertility coverage limit unclear",
                "details": [
                    "Max cycles: Not specified in response",
                    "IVF coverage: Possible but needs manual verification"
                ],
                "confidence_breakdown": {
                    "policy_active": 0.98,
                    "fertility_coverage": 0.72,
                    "ivf_cycles": 0.45
                }
            },
            "suggested_actions": [
                "Call insurance provider to verify details",
                "Request written confirmation of coverage",
                "Mark for manual follow-up"
            ],
            "created_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            "waiting_minutes": 5
        },
        {
            "task_id": "TASK-DOC001",
            "title": "Verify Medical History Extraction",
            "description": "Low confidence on previous treatments section",
            "patient_id": "PAT-ALEX001",
            "patient_name": "Alex Rodriguez",
            "agent_type": "document_extractor",
            "status": "awaiting_approval",
            "priority": "medium",
            "confidence_score": 0.68,
            "ai_context": {
                "document": "Medical History - Page 3",
                "issue": "Previous treatments section partially illegible",
                "extracted_data": {
                    "diagnoses": "Unexplained Infertility",
                    "previous_treatments": "IUI x2 (unclear success rate)"
                },
                "confidence_breakdown": {
                    "diagnoses": 0.95,
                    "previous_treatments": 0.68,
                    "medications": 0.88
                }
            },
            "suggested_actions": [
                "Request clarification from patient",
                "Review original document manually",
                "Approve with note for follow-up"
            ],
            "created_at": (datetime.now(timezone.utc) - timedelta(minutes=12)).isoformat(),
            "waiting_minutes": 12
        }
    ]
    await db.tasks.insert_many(mock_tasks)
    
    # Create mock agent executions
    mock_executions = [
        {
            "execution_id": "EXEC-DOC001",
            "agent_type": "document_extractor",
            "patient_id": "PAT-EMMA002",
            "patient_name": "Emma Watson",
            "status": "running",
            "progress": 67,
            "current_step": "Extracting medical history from page 4 of 6...",
            "duration_seconds": 45,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "execution_id": "EXEC-SCH001",
            "agent_type": "scheduler_agent",
            "patient_id": "PAT-ALEX001",
            "patient_name": "Alex Rodriguez",
            "status": "completed",
            "progress": 100,
            "current_step": "Appointment scheduled successfully",
            "duration_seconds": 154,
            "created_at": (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()
        }
    ]
    await db.agent_executions.insert_many(mock_executions)
    
    logger.info("Mock data initialized successfully")

# ==================== API ENDPOINTS ====================

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "BacklineMD API", "version": "1.0.0"}

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    stats = [
        StatCard(
            title="TIME SAVED",
            value="3.3 hrs",
            subtitle="AI vs Manual Process",
            icon="Clock",
            color="blue"
        ),
        StatCard(
            title="AI COMMUNICATIONS",
            value="4",
            subtitle="Automated Interactions",
            icon="MessageSquare",
            color="teal"
        ),
        StatCard(
            title="PENDING APPROVALS",
            value="14",
            subtitle="Require Physician Review",
            icon="FileCheck",
            color="orange"
        ),
        StatCard(
            title="TODAY'S APPOINTMENTS",
            value="3",
            subtitle="Scheduled for Today",
            icon="Calendar",
            color="purple"
        )
    ]
    return stats

@api_router.get("/dashboard/appointments")
async def get_todays_appointments():
    appointments = [
        Appointment(
            time="9:00 AM",
            type="Follow Up",
            patient_name="Alex Rodriguez",
            doctor="Dr. James O'Brien"
        ),
        Appointment(
            time="11:30 AM",
            type="Consultation",
            patient_name="Emma Watson",
            doctor="Dr. Sarah Chen"
        )
    ]
    return appointments

# Patients
@api_router.get("/patients", response_model=List[Patient])
async def get_patients(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    
    patients = await db.patients.find(query, {"_id": 0}).to_list(100)
    for p in patients:
        if isinstance(p.get('created_at'), str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
    return patients

@api_router.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: str):
    patient = await db.patients.find_one({"patient_id": patient_id}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if isinstance(patient.get('created_at'), str):
        patient['created_at'] = datetime.fromisoformat(patient['created_at'])
    return patient

@api_router.post("/patients", response_model=Patient)
async def create_patient(patient_data: PatientCreate):
    patient = Patient(**patient_data.model_dump())
    doc = patient.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.patients.insert_one(doc)
    return patient

# Tasks
@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    else:
        query["status"] = "awaiting_approval"  # Default to pending
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    for t in tasks:
        if isinstance(t.get('created_at'), str):
            t['created_at'] = datetime.fromisoformat(t['created_at'])
    return tasks

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if isinstance(task.get('created_at'), str):
        task['created_at'] = datetime.fromisoformat(task['created_at'])
    return task

@api_router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, decision: TaskDecision):
    task = await db.tasks.find_one({"task_id": task_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task status
    new_status = "completed" if decision.decision == "approve" else "rejected"
    await db.tasks.update_one(
        {"task_id": task_id},
        {"$set": {"status": new_status}}
    )
    
    # Update patient status if approved
    if decision.decision in ["approve", "approve_with_followup"]:
        await db.patients.update_one(
            {"patient_id": task["patient_id"]},
            {"$set": {"status": "approved"}, "$inc": {"tasks_count": -1}}
        )
    
    return {
        "status": "success",
        "task_id": task_id,
        "decision": decision.decision,
        "agent_resumed": True
    }

# Agent Executions
@api_router.get("/agents/active", response_model=List[AgentExecution])
async def get_active_agents():
    agents = await db.agent_executions.find(
        {"status": {"$in": ["running", "queued"]}},
        {"_id": 0}
    ).to_list(50)
    
    for a in agents:
        if isinstance(a.get('created_at'), str):
            a['created_at'] = datetime.fromisoformat(a['created_at'])
    return agents

# Server-Sent Events for real-time updates
@api_router.get("/agents/stream")
async def stream_agent_updates():
    async def event_generator():
        while True:
            # Get active agents
            agents = await db.agent_executions.find(
                {"status": {"$in": ["running", "queued"]}},
                {"_id": 0}
            ).to_list(50)
            
            # Simulate progress updates
            for agent in agents:
                if agent.get('status') == 'running' and agent.get('progress', 0) < 100:
                    # Increment progress
                    new_progress = min(agent.get('progress', 0) + 5, 95)
                    await db.agent_executions.update_one(
                        {"execution_id": agent['execution_id']},
                        {"$set": {"progress": new_progress, "duration_seconds": agent.get('duration_seconds', 0) + 2}}
                    )
                    agent['progress'] = new_progress
            
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agents": agents
            }
            
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(2)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Startup event
@app.on_event("startup")
async def startup_event():
    await init_mock_data()
    logger.info("BacklineMD API started successfully")

# Patient Notes
class NoteCreate(BaseModel):
    patient_id: str
    content: str
    author: str = "Dr. James O'Brien"

@api_router.post("/patients/{patient_id}/notes")
async def create_note(patient_id: str, note_data: NoteCreate):
    note = {
        "note_id": f"NOTE-{uuid.uuid4().hex[:8].upper()}",
        "patient_id": patient_id,
        "content": note_data.content,
        "author": note_data.author,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notes.insert_one(note)
    return {"status": "success", "note": note}

@api_router.get("/patients/{patient_id}/notes")
async def get_patient_notes(patient_id: str):
    notes = await db.notes.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return notes

# CopilotKit endpoint (placeholder for future LangGraph integration)
@api_router.post("/copilot")
async def copilot_endpoint(request: dict):
    """
    CopilotKit endpoint - ready for LangGraph agent integration
    This will be connected to LangGraph platform agents later
    """
    # For now, return a simple response
    # Later this will invoke LangGraph agents via API
    return {
        "status": "ready",
        "message": "CopilotKit endpoint ready for LangGraph integration"
    }

@app.on_event("shutdown")
async def shutdown_event():
    client.close()
    logger.info("BacklineMD API shut down")