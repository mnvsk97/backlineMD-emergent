from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums
class UserRole(str, Enum):
    DOCTOR = "doctor"
    ADMIN = "admin"
    STAFF = "staff"

class DocumentKind(str, Enum):
    LAB = "lab"
    IMAGING = "imaging"
    MEDICAL_HISTORY = "medical_history"
    SUMMARY = "summary"
    CONSENT_FORM = "consent_form"

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INGESTING = "ingesting"
    INGESTED = "ingested"
    NOT_INGESTED = "not_ingested"
    APPROVED = "approved"
    REJECTED = "rejected"

class ConsentFormStatus(str, Enum):
    TO_DO = "to_do"
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    SIGNED = "signed"

class TaskState(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ClaimStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"

class AgentStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"

# Request Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    tenant_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    dob: str
    gender: str
    email: EmailStr
    phone: str
    address: Optional[Dict[str, Any]] = None
    preconditions: Optional[List[str]] = []
    profile_image: Optional[str] = None

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preconditions: Optional[List[str]] = None
    latest_vitals: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class DocumentUpdate(BaseModel):
    status: Optional[DocumentStatus] = None
    extracted: Optional[Dict[str, Any]] = None

class ConsentFormSend(BaseModel):
    patient_id: str
    form_template_ids: List[str]

class AppointmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    type: str
    title: str
    starts_at: datetime
    ends_at: datetime
    location: Optional[str] = None

class ClaimCreate(BaseModel):
    patient_id: str
    insurance_provider: str
    amount: float
    procedure_code: Optional[str] = None
    diagnosis_code: Optional[str] = None
    service_date: str
    description: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    description: str
    patient_id: str
    assigned_to: str
    agent_type: str = "human"
    priority: TaskPriority = TaskPriority.MEDIUM
    kind: Optional[str] = None

class TaskUpdate(BaseModel):
    state: Optional[TaskState] = None
    comment: Optional[str] = None

class MessageCreate(BaseModel):
    conversation_id: str
    text: str
    rich: Optional[Dict[str, Any]] = None

class AgentStart(BaseModel):
    subject: Dict[str, Any]
    inputs: Optional[Dict[str, Any]] = {}

class AgentResume(BaseModel):
    task_id: str
    resolution: str

# Response Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    roles: List[str]
    tenant_id: str

class PatientResponse(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    status: str
    tasks_count: int = 0
    appointments_count: int = 0
    flagged_count: int = 0
    profile_image: Optional[str] = None

class DocumentResponse(BaseModel):
    document_id: str
    patient_id: str
    kind: str
    file: Dict[str, Any]
    status: str
    created_at: datetime

class TaskResponse(BaseModel):
    task_id: str
    title: str
    description: str
    patient_name: Optional[str] = None
    assigned_to: str
    agent_type: str
    priority: str
    state: str
    confidence_score: Optional[float] = None
    waiting_minutes: int = 0
    created_at: datetime

class ClaimResponse(BaseModel):
    claim_id: str
    patient_name: str
    insurance_provider: str
    amount: float
    status: str
    submitted_date: str
    last_event_at: Optional[datetime] = None