"""
Email Event Handler for BacklineMD
Processes incoming emails and creates tasks for appropriate agents
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import re

from composio_email_service import (
    get_email_service,
    send_welcome_email,
    send_document_received_email,
)
from database import get_db
from models import TaskState, TaskPriority

logger = logging.getLogger(__name__)

DEFAULT_TENANT = "hackathon-demo"
CLINIC_EMAIL = "mnvsk97@gmail.com"


async def process_incoming_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an incoming email and create appropriate tasks
    
    Args:
        email_data: Email data from Gmail
        
    Returns:
        Dict with processing result
    """
    try:
        service = await get_email_service()
        email_info = service.extract_email_info(email_data)
        
        sender_email = email_info.get("from_email", "").lower()
        subject = email_info.get("subject", "")
        body = email_info.get("body", "")
        message_id = email_info.get("message_id", "")
        has_attachments = email_info.get("has_attachments", False)
        
        # Skip if email is from clinic itself
        if sender_email == CLINIC_EMAIL.lower():
            logger.info(f"Skipping email from clinic: {sender_email}")
            return {"processed": False, "reason": "from_clinic"}
        
        # Skip if already processed
        db = get_db()
        existing_task = await db.tasks.find_one({
            "tenant_id": DEFAULT_TENANT,
            "email_message_id": message_id,
        })
        if existing_task:
            logger.info(f"Email already processed: {message_id}")
            return {"processed": False, "reason": "already_processed"}
        
        # Find or create patient by email
        patient = await db.patients.find_one({
            "tenant_id": DEFAULT_TENANT,
            "contact.email": sender_email,
        })
        
        # Check if this is a new patient email (first contact)
        is_new_patient = patient is None
        
        # Check if email has attachments (document submission)
        has_documents = has_attachments
        
        if is_new_patient:
            # New patient email - create patient and intake task
            return await handle_new_patient_email(
                sender_email=sender_email,
                subject=subject,
                body=body,
                message_id=message_id,
                email_info=email_info,
            )
        elif has_documents:
            # Existing patient sending documents
            return await handle_document_email(
                patient=patient,
                sender_email=sender_email,
                subject=subject,
                body=body,
                message_id=message_id,
                email_info=email_info,
            )
        else:
            # General inquiry from existing patient
            logger.info(f"General inquiry email from {sender_email}")
            return {"processed": True, "action": "general_inquiry"}
            
    except Exception as e:
        logger.error(f"Error processing incoming email: {e}", exc_info=True)
        return {"processed": False, "error": str(e)}


async def handle_new_patient_email(
    sender_email: str,
    subject: str,
    body: str,
    message_id: str,
    email_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle email from a new patient
    Creates patient record and intake task
    """
    db = get_db()
    
    try:
        # Extract patient name from email
        sender_name = email_info.get("from", "")
        # Try to extract name from email body or subject
        name_match = re.search(r"([A-Z][a-z]+ [A-Z][a-z]+)", body[:200] + " " + subject)
        if name_match:
            full_name = name_match.group(1)
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        else:
            # Extract from sender field
            name_parts = sender_name.split(" ", 1)
            first_name = name_parts[0] if name_parts else "Patient"
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Create patient
        import uuid
        import random
        from datetime import datetime, timezone
        
        patient_id = str(uuid.uuid4())
        mrn = f"MRN{random.randint(100000, 999999)}"
        
        # Generate search n-grams
        full_name = f"{first_name} {last_name}".strip()
        ngrams = [
            full_name.lower().replace(" ", "")[i : i + 3]
            for i in range(len(full_name.replace(" ", "")) - 2)
        ]
        
        patient = {
            "_id": patient_id,
            "tenant_id": DEFAULT_TENANT,
            "mrn": mrn,
            "first_name": first_name,
            "last_name": last_name or "",
            "dob": "1990-01-01",  # Default, will be updated
            "gender": "Unknown",
            "contact": {
                "email": sender_email,
                "phone": "",  # Will be collected
                "address": {},
            },
            "preconditions": [],
            "flags": [],
            "latest_vitals": {},
            "profile_image": None,
            "status": "Intake In Progress",
            "tasks_count": 0,
            "appointments_count": 0,
            "flagged_count": 0,
            "search": {"ngrams": ngrams},
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "email_intake",
        }
        
        await db.patients.insert_one(patient)
        logger.info(f"Created new patient from email: {patient_id} - {full_name}")
        
        # Create intake task to send welcome email
        task_id = str(uuid.uuid4())
        task_id_display = f"T{random.randint(10000, 99999)}"
        
        task = {
            "_id": task_id,
            "task_id": task_id_display,
            "tenant_id": DEFAULT_TENANT,
            "source": "email",
            "kind": "intake",
            "title": f"Send Welcome Email to {full_name}",
            "description": f"New patient {full_name} ({sender_email}) reached out via email. Send welcome email and request documents.",
            "patient_id": patient_id,
            "patient_name": full_name,
            "assigned_to": "intake_agent",
            "agent_type": "intake_agent",
            "priority": TaskPriority.HIGH.value,
            "state": TaskState.OPEN.value,
            "confidence_score": 1.0,
            "waiting_minutes": 0,
            "email_message_id": message_id,
            "email_subject": subject,
            "email_from": sender_email,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "email_handler",
        }
        
        await db.tasks.insert_one(task)
        await db.patients.update_one(
            {"_id": patient_id},
            {"$inc": {"tasks_count": 1}}
        )
        
        logger.info(f"Created intake task for new patient: {task_id}")
        
        return {
            "processed": True,
            "action": "new_patient",
            "patient_id": patient_id,
            "task_id": task_id,
        }
        
    except Exception as e:
        logger.error(f"Error handling new patient email: {e}", exc_info=True)
        return {"processed": False, "error": str(e)}


async def handle_document_email(
    patient: Dict[str, Any],
    sender_email: str,
    subject: str,
    body: str,
    message_id: str,
    email_info: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handle email with documents from existing patient
    Creates document extraction task
    """
    db = get_db()
    
    try:
        patient_id = patient["_id"]
        patient_name = f"{patient['first_name']} {patient['last_name']}"
        
        # Get attachments
        service = await get_email_service()
        attachments = await service.get_email_attachments(message_id)
        
        # Create document records for each attachment
        import uuid
        import random
        from datetime import datetime, timezone
        
        document_ids = []
        for attachment in attachments:
            document_id = str(uuid.uuid4())
            
            # Determine document kind from filename
            filename = attachment.get("filename", "unknown")
            kind = "medical_history"  # Default
            if any(term in filename.lower() for term in ["lab", "test", "result"]):
                kind = "lab"
            elif any(term in filename.lower() for term in ["image", "xray", "scan", "ultrasound"]):
                kind = "imaging"
            elif any(term in filename.lower() for term in ["insurance", "card"]):
                kind = "insurance"
            
            document = {
                "_id": document_id,
                "tenant_id": DEFAULT_TENANT,
                "patient_id": patient_id,
                "kind": kind,
                "file": {
                    "url": f"/email-attachments/{message_id}/{attachment.get('attachment_id')}",
                    "name": filename,
                    "mime": attachment.get("mime_type", "application/octet-stream"),
                    "size": attachment.get("size", 0),
                    "sha256": f"email-{message_id}-{attachment.get('attachment_id')}",
                },
                "ocr": {"done": False, "engine": None},
                "extracted": {},
                "status": "uploaded",
                "source": "email",
                "email_message_id": message_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            
            await db.documents.insert_one(document)
            document_ids.append(document_id)
        
        logger.info(f"Created {len(document_ids)} document records from email")
        
        # Create document extraction task
        task_id = str(uuid.uuid4())
        task_id_display = f"T{random.randint(10000, 99999)}"
        
        task = {
            "_id": task_id,
            "task_id": task_id_display,
            "tenant_id": DEFAULT_TENANT,
            "source": "email",
            "kind": "document_extraction",
            "title": f"Extract Documents from Email - {patient_name}",
            "description": f"Patient {patient_name} sent {len(attachments)} document(s) via email. Extract and summarize medical information from each document.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": "doc_extraction_agent",
            "agent_type": "doc_extraction_agent",
            "priority": TaskPriority.HIGH.value,
            "state": TaskState.OPEN.value,
            "confidence_score": 1.0,
            "waiting_minutes": 0,
            "email_message_id": message_id,
            "email_subject": subject,
            "email_from": sender_email,
            "document_ids": document_ids,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "email_handler",
        }
        
        await db.tasks.insert_one(task)
        await db.patients.update_one(
            {"_id": patient_id},
            {"$inc": {"tasks_count": 1}}
        )
        
        # Send confirmation email
        await send_document_received_email(
            patient_email=sender_email,
            patient_name=patient_name
        )
        
        # Create task for caretaker agent to call patient and schedule appointment
        caretaker_task_id = str(uuid.uuid4())
        caretaker_task_id_display = f"T{random.randint(10000, 99999)}"
        
        caretaker_task = {
            "_id": caretaker_task_id,
            "task_id": caretaker_task_id_display,
            "tenant_id": DEFAULT_TENANT,
            "source": "email",
            "kind": "appointment_scheduling",
            "title": f"Call Patient and Schedule Consultation - {patient_name}",
            "description": f"Patient {patient_name} has submitted documents. Call patient to schedule initial consultation. Clinic hours: Monday-Friday 9:00 AM - 4:00 PM (closed weekends). Find available appointment slot and create appointment.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": "care_taker_agent",
            "agent_type": "care_taker_agent",
            "priority": TaskPriority.HIGH.value,
            "state": TaskState.OPEN.value,
            "confidence_score": 1.0,
            "waiting_minutes": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "email_handler",
        }
        
        await db.tasks.insert_one(caretaker_task)
        await db.patients.update_one(
            {"_id": patient_id},
            {"$inc": {"tasks_count": 1}}
        )
        
        # Create task for insurance agent to collect insurance details
        insurance_task_id = str(uuid.uuid4())
        insurance_task_id_display = f"T{random.randint(10000, 99999)}"
        
        insurance_task = {
            "_id": insurance_task_id,
            "task_id": insurance_task_id_display,
            "tenant_id": DEFAULT_TENANT,
            "source": "email",
            "kind": "insurance_collection",
            "title": f"Collect Insurance Details - {patient_name}",
            "description": f"Patient {patient_name} has submitted documents. Review insurance card documents, extract insurance details (provider, policy number, group number), and update patient record. Submit claims for procedures as needed.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": "insurance_agent",
            "agent_type": "insurance_agent",
            "priority": TaskPriority.MEDIUM.value,
            "state": TaskState.OPEN.value,
            "confidence_score": 1.0,
            "waiting_minutes": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "created_by": "email_handler",
        }
        
        await db.tasks.insert_one(insurance_task)
        await db.patients.update_one(
            {"_id": patient_id},
            {"$inc": {"tasks_count": 1}}
        )
        
        logger.info(f"Created document extraction task: {task_id}")
        logger.info(f"Created caretaker task: {caretaker_task_id}")
        logger.info(f"Created insurance task: {insurance_task_id}")
        
        return {
            "processed": True,
            "action": "documents_received",
            "patient_id": patient_id,
            "task_id": task_id,
            "caretaker_task_id": caretaker_task_id,
            "insurance_task_id": insurance_task_id,
            "document_count": len(document_ids),
        }
        
    except Exception as e:
        logger.error(f"Error handling document email: {e}", exc_info=True)
        return {"processed": False, "error": str(e)}


async def start_email_listener():
    """
    Start listening for incoming emails via Composio triggers
    This runs in the background and processes new emails
    """
    try:
        service = await get_email_service()
        
        # Create trigger for new Gmail messages
        trigger = await asyncio.to_thread(
            service.composio.triggers.create,
            user_id=service.external_user_id,
            slug="GMAIL_NEW_GMAIL_MESSAGE",
            trigger_config={
                "labelIds": "INBOX",
                "userId": "me",
                "interval": 1,  # Check every minute
            },
        )
        
        logger.info(f"Created Gmail trigger: {trigger.trigger_id}")
        
        # Subscribe to trigger events
        subscription = await asyncio.to_thread(
            service.composio.triggers.subscribe,
        )
        
        # Define handler
        @subscription.handle(trigger_id=trigger.trigger_id)
        async def handle_gmail_event(data):
            """Handle incoming Gmail events"""
            try:
                logger.info(f"Received Gmail event: {data}")
                
                # Process the email
                if isinstance(data, dict) and "message" in data:
                    email_data = data["message"]
                    result = await process_incoming_email(email_data)
                    logger.info(f"Email processing result: {result}")
                elif isinstance(data, list):
                    for email_data in data:
                        result = await process_incoming_email(email_data)
                        logger.info(f"Email processing result: {result}")
                        
            except Exception as e:
                logger.error(f"Error handling Gmail event: {e}", exc_info=True)
        
        # Listen to incoming events (this blocks)
        logger.info("Starting email listener...")
        await asyncio.to_thread(subscription.wait_forever)
        
    except Exception as e:
        logger.error(f"Error starting email listener: {e}", exc_info=True)
        raise

