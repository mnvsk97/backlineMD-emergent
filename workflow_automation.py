"""
Workflow Automation for BacklineMD Patient Journey
Automates task creation based on patient status changes
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

DEFAULT_TENANT = "hackathon-demo"


async def create_task(db: AsyncIOMotorDatabase, task_data: Dict[str, Any]):
    """Helper to create a task"""
    task_data.setdefault("tenant_id", DEFAULT_TENANT)
    task_data.setdefault("created_at", datetime.now(timezone.utc))
    task_data.setdefault("state", "open")
    result = await db.tasks.insert_one(task_data)
    logger.info(f"Created task: {task_data.get('title')} - ID: {result.inserted_id}")
    return result.inserted_id


async def trigger_new_patient_workflow(db: AsyncIOMotorDatabase, patient_id: str, patient_data: Dict[str, Any]):
    """
    Triggered when a new patient is created
    Creates:
    1. Intake agent task
    2. Document collection task
    """
    logger.info(f"Starting new patient workflow for: {patient_id}")
    
    patient_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
    
    # Task 1: Intake Agent - Collect patient information
    await create_task(db, {
        "_id": f"TASK-INTAKE-{patient_id[:8]}",
        "title": f"Complete Patient Intake - {patient_name}",
        "description": "Collect comprehensive patient information including medical history, allergies, and current medications.",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "ai_agent",
        "assignee_name": "Intake Agent",
        "priority": "high",
        "confidence_score": 95,
        "tags": ["intake", "patient-onboarding"],
    })
    
    # Task 2: Document Collection
    await create_task(db, {
        "_id": f"TASK-DOCS-{patient_id[:8]}",
        "title": f"Collect Medical Records - {patient_name}",
        "description": "Request and collect all medical records, lab results, and imaging from previous providers.",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "human",
        "assignee_name": "Medical Records Coordinator",
        "priority": "medium",
        "confidence_score": 90,
        "tags": ["documents", "records-collection"],
    })
    
    # Update patient status
    await db.patients.update_one(
        {"_id": patient_id},
        {"$set": {"status": "Intake In Progress"}}
    )
    
    logger.info(f"Created intake and document collection tasks for patient: {patient_id}")


async def trigger_documents_collected_workflow(db: AsyncIOMotorDatabase, patient_id: str, patient_name: str):
    """
    Triggered when all medical records are collected
    Creates: Document extraction agent task
    """
    logger.info(f"Starting document extraction workflow for: {patient_id}")
    
    # Task: Document Extraction Agent
    await create_task(db, {
        "_id": f"TASK-EXTRACT-{patient_id[:8]}",
        "title": f"Extract Data from Medical Records - {patient_name}",
        "description": "Use AI to extract key medical information, diagnoses, treatments, and lab values from uploaded documents.",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "ai_agent",
        "assignee_name": "Document Extraction Agent",
        "priority": "high",
        "confidence_score": 92,
        "tags": ["extraction", "ai-processing"],
    })
    
    # Update patient status
    await db.patients.update_one(
        {"_id": patient_id},
        {"$set": {"status": "Doc Collection Done"}}
    )
    
    logger.info(f"Created document extraction task for patient: {patient_id}")


async def trigger_extraction_complete_workflow(db: AsyncIOMotorDatabase, patient_id: str, patient_name: str):
    """
    Triggered when document extraction is complete
    Creates: Appointment scheduling task for coordinator
    """
    logger.info(f"Starting appointment scheduling workflow for: {patient_id}")
    
    # Task: Schedule Appointment
    await create_task(db, {
        "_id": f"TASK-APPT-{patient_id[:8]}",
        "title": f"Schedule Initial Consultation - {patient_name}",
        "description": "Review extracted medical information and schedule an initial consultation with the appropriate specialist.",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "human",
        "assignee_name": "Care Coordinator",
        "priority": "high",
        "confidence_score": 88,
        "tags": ["scheduling", "consultation"],
    })
    
    # Update patient status
    await db.patients.update_one(
        {"_id": patient_id},
        {"$set": {"status": "Awaiting Response"}}
    )
    
    logger.info(f"Created appointment scheduling task for patient: {patient_id}")


async def trigger_appointment_complete_workflow(db: AsyncIOMotorDatabase, patient_id: str, patient_name: str, appointment_data: Dict[str, Any]):
    """
    Triggered when appointment is completed
    Creates:
    1. Doctor treatment plan task
    2. Insurance verification task
    """
    logger.info(f"Starting post-appointment workflow for: {patient_id}")
    
    # Task 1: Doctor creates treatment plan
    await create_task(db, {
        "_id": f"TASK-TREAT-{patient_id[:8]}",
        "title": f"Create Treatment Plan - {patient_name}",
        "description": "Based on consultation, create comprehensive treatment plan, add clinical notes, and send treatment summary to patient.",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "human",
        "assignee_name": "Dr. James O'Brien",
        "priority": "high",
        "confidence_score": 95,
        "tags": ["treatment", "clinical-notes"],
    })
    
    # Task 2: Insurance verification
    await create_task(db, {
        "_id": f"TASK-INS-{patient_id[:8]}",
        "title": f"Verify Insurance Coverage - {patient_name}",
        "description": "Verify if proposed treatment is covered under patient's insurance plan and get pre-authorization if needed.",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "ai_agent",
        "assignee_name": "Insurance Verification Agent",
        "priority": "high",
        "confidence_score": 90,
        "tags": ["insurance", "verification"],
    })
    
    # Update patient status
    await db.patients.update_one(
        {"_id": patient_id},
        {"$set": {"status": "Consultation Complete"}}
    )
    
    logger.info(f"Created treatment and insurance tasks for patient: {patient_id}")


async def trigger_insurance_verified_workflow(db: AsyncIOMotorDatabase, patient_id: str, patient_name: str, treatment_amount: float = 5000.0):
    """
    Triggered when insurance verification is complete
    Creates: Insurance claim
    """
    logger.info(f"Creating insurance claim for: {patient_id}")
    
    # Get patient info for insurance details
    patient = await db.patients.find_one({"_id": patient_id})
    if not patient:
        logger.error(f"Patient not found: {patient_id}")
        return
    
    # Create insurance claim
    claim_id = f"CLAIM-{patient_id[:8]}-{datetime.now().strftime('%Y%m%d')}"
    claim_data = {
        "_id": claim_id,
        "tenant_id": DEFAULT_TENANT,
        "patient_id": patient_id,
        "patient_name": patient_name,
        "insurance_provider": patient.get("insurance_provider", "Blue Cross Blue Shield"),
        "policy_number": patient.get("insurance_policy_number", "Unknown"),
        "amount": treatment_amount,
        "status": "pending",
        "submitted_date": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc),
        "events": [
            {
                "event_type": "created",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "description": "Claim created following insurance verification",
                "status": "pending"
            }
        ]
    }
    
    await db.claims.insert_one(claim_data)
    
    # Create task to track claim
    await create_task(db, {
        "_id": f"TASK-CLAIM-{patient_id[:8]}",
        "title": f"Track Insurance Claim - {patient_name}",
        "description": f"Monitor insurance claim {claim_id} for approval. Expected amount: ${treatment_amount:,.2f}",
        "patient_id": patient_id,
        "patient_name": patient_name,
        "assignee_type": "ai_agent",
        "assignee_name": "Claim Status Checker",
        "priority": "medium",
        "confidence_score": 85,
        "tags": ["claims", "insurance"],
    })
    
    logger.info(f"Created insurance claim {claim_id} for patient: {patient_id}")
