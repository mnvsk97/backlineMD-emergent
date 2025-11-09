"""
Enhanced seed data with specific patient journey stages
Run with: python seed_data_enhanced.py
"""

import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb://localhost:27017"
DEFAULT_TENANT = "hackathon-demo"

# Staff names
DOCTORS = ["Dr. James O'Brien", "Dr. Sarah Chen", "Dr. Michael Rodriguez"]
BACKOFFICE_STAFF = [
    "Emily Parker - Insurance Coordinator",
    "David Kim - Records Manager",
]

# Agent types
AGENT_TYPES = [
    "AI - Document Extractor",
    "AI - Insurance Verifier",
    "AI - Onboarding Agent",
    "AI - Prior Auth Agent",
    "AI - Claim Status Checker",
]

# Patient statuses
PATIENT_STATUSES = [
    "Active - Routine Care",
    "Active - Under Treatment",
    "Pending - Awaiting Documentation",
    "Pending - Insurance Verification",
    "Urgent - Requires Immediate Attention",
    "Follow-up Required",
]

# Task priorities
TASK_PRIORITIES = ["urgent", "high", "medium", "low"]

# Document statuses
DOCUMENT_STATUSES = [
    "uploaded",
    "ingesting",
    "ingested",
    "not_ingested",
    "approved",
    "rejected",
]

# Consent form statuses
CONSENT_FORM_STATUSES = ["to_do", "sent", "in_progress", "signed"]

# Claim statuses
CLAIM_STATUSES = [
    "pending",
    "submitted",
    "received",
    "under_review",
    "approved",
    "denied",
]

# Task states
TASK_STATES = ["open", "in_progress", "done", "cancelled"]

# Enhanced patient data with statuses
PATIENTS = [
    {
        "first_name": "Alex",
        "last_name": "Rodriguez",
        "age": 34,
        "gender": "Male",
        "dob": "1990-05-15",
        "email": "alex.rodriguez@email.com",
        "phone": "+1-555-0101",
        "preconditions": ["Family history of heart disease", "Elevated cholesterol"],
        "profile_image": "https://i.pravatar.cc/150?img=12",
        "status": "Active - Under Treatment",
        "stage": "blood_report_review",
    },
    {
        "first_name": "Maria",
        "last_name": "Garcia",
        "age": 39,
        "gender": "Female",
        "dob": "1985-08-22",
        "email": "maria.garcia@email.com",
        "phone": "+1-555-0102",
        "preconditions": ["Diabetes Type 2", "Hypertension"],
        "profile_image": "https://i.pravatar.cc/150?img=45",
        "status": "Pending - Awaiting Documentation",
        "stage": "consent_forms_needed",
    },
    {
        "first_name": "James",
        "last_name": "Smith",
        "age": 46,
        "gender": "Male",
        "dob": "1978-12-10",
        "email": "james.smith@email.com",
        "phone": "+1-555-0103",
        "preconditions": ["Hypertension", "Sleep apnea"],
        "profile_image": "https://i.pravatar.cc/150?img=33",
        "status": "Active - Routine Care",
        "stage": "ready_for_consultation",
    },
    {
        "first_name": "Sarah",
        "last_name": "Chen",
        "age": 28,
        "gender": "Female",
        "dob": "1996-03-18",
        "email": "sarah.chen@email.com",
        "phone": "+1-555-0104",
        "preconditions": ["Asthma", "Allergies"],
        "profile_image": "https://i.pravatar.cc/150?img=23",
        "status": "Pending - Insurance Verification",
        "stage": "insurance_resubmit",
    },
    {
        "first_name": "Michael",
        "last_name": "Johnson",
        "age": 52,
        "gender": "Male",
        "dob": "1972-11-05",
        "email": "michael.johnson@email.com",
        "phone": "+1-555-0105",
        "preconditions": ["Obesity", "Pre-diabetes", "High blood pressure"],
        "profile_image": "https://i.pravatar.cc/150?img=52",
        "status": "Urgent - Requires Immediate Attention",
        "stage": "urgent_followup",
    },
    {
        "first_name": "Emily",
        "last_name": "Davis",
        "age": 31,
        "gender": "Female",
        "dob": "1993-07-22",
        "email": "emily.davis@email.com",
        "phone": "+1-555-0106",
        "preconditions": ["Anxiety disorder", "Hypothyroidism"],
        "profile_image": "https://i.pravatar.cc/150?img=38",
        "status": "Follow-up Required",
        "stage": "medication_review",
    },
    {
        "first_name": "Robert",
        "last_name": "Williams",
        "age": 67,
        "gender": "Male",
        "dob": "1957-02-14",
        "email": "robert.williams@email.com",
        "phone": "+1-555-0107",
        "preconditions": ["Coronary artery disease", "Type 2 diabetes", "Arthritis"],
        "profile_image": "https://i.pravatar.cc/150?img=60",
        "status": "Active - Under Treatment",
        "stage": "prior_auth_pending",
    },
    {
        "first_name": "Jennifer",
        "last_name": "Martinez",
        "age": 42,
        "gender": "Female",
        "dob": "1982-09-30",
        "email": "jennifer.martinez@email.com",
        "phone": "+1-555-0108",
        "preconditions": ["Migraine", "GERD"],
        "profile_image": "https://i.pravatar.cc/150?img=47",
        "status": "Active - Routine Care",
        "stage": "routine_checkup",
    },
]

FORM_TEMPLATES = [
    {
        "name": "Insurance Information Release",
        "description": "Authorization to release medical information to insurance provider",
        "purpose": "Insurance verification and claims processing",
    },
    {
        "name": "Medical Records Request",
        "description": "Authorization to request medical records from external providers",
        "purpose": "Obtain complete medical history",
    },
]


def generate_ngrams(text: str, n: int = 3):
    """Generate n-grams for search"""
    text = text.lower().replace(" ", "")
    return [text[i : i + n] for i in range(len(text) - n + 1)]


async def seed_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.backlinemd

    print("🌱 Starting enhanced seed data creation...")
    print(f"   Tenant: {DEFAULT_TENANT}")
    print("")

    # Clear existing data
    print("🗑️  Clearing existing data...")
    await db.patients.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.documents.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.tasks.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.claims.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.claim_events.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.appointments.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.consent_forms.delete_many({"tenant_id": DEFAULT_TENANT})
    await db.form_templates.delete_many({"tenant_id": DEFAULT_TENANT})
    print("   ✓ Cleared")
    print("")

    # Create form templates
    print("📋 Creating form templates...")
    template_ids = []
    for template in FORM_TEMPLATES:
        template_id = str(uuid4())
        await db.form_templates.insert_one(
            {
                "_id": template_id,
                "tenant_id": DEFAULT_TENANT,
                **template,
                "template_url": f"/templates/{template_id}.pdf",
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        template_ids.append(template_id)
        print(f"   ✓ {template['name']}")
    print("")

    # Create patients
    print("👥 Creating patients...")
    patient_data_list = []
    for patient_data in PATIENTS:
        patient_id = str(uuid4())
        mrn = f"MRN{random.randint(100000, 999999)}"
        full_name = f"{patient_data['first_name']} {patient_data['last_name']}"
        ngrams = generate_ngrams(full_name)

        patient = {
            "_id": patient_id,
            "tenant_id": DEFAULT_TENANT,
            "mrn": mrn,
            "first_name": patient_data["first_name"],
            "last_name": patient_data["last_name"],
            "age": patient_data["age"],
            "dob": patient_data["dob"],
            "gender": patient_data["gender"],
            "contact": {
                "email": patient_data["email"],
                "phone": patient_data["phone"],
                "address": {},
            },
            "preconditions": patient_data["preconditions"],
            "flags": [],
            "latest_vitals": {},
            "profile_image": patient_data["profile_image"],
            "status": patient_data["status"],
            "tasks_count": 0,
            "appointments_count": 0,
            "flagged_count": 0,
            "search": {"ngrams": ngrams},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        await db.patients.insert_one(patient)
        patient_data_list.append((patient_id, full_name, patient_data["stage"]))
        print(f"   ✓ {full_name} - {patient_data['status']}")
    print("")

    # Create stage-specific documents and tasks
    print("📄 Creating documents and tasks by patient stage...")

    # PATIENT 1: Blood Report Review Stage
    patient_id, patient_name, stage = patient_data_list[0]
    print(f"\n   Patient 1: {patient_name}")

    # Add blood report document
    doc_id = str(uuid4())
    await db.documents.insert_one(
        {
            "_id": doc_id,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "kind": "lab",
            "file": {
                "url": f"/uploads/{doc_id}/Blood_Test_Results_Oct_2024.pdf",
                "name": "Blood Test Results - Oct 2024.pdf",
                "mime": "application/pdf",
                "size": 245000,
                "sha256": f"hash-{doc_id[:8]}",
            },
            "ocr": {"done": True, "engine": "tesseract"},
            "extracted": {
                "fields": {
                    "cholesterol": "245 mg/dL",
                    "ldl": "165 mg/dL",
                    "hdl": "42 mg/dL",
                    "triglycerides": "195 mg/dL",
                },
                "confidence": 0.92,
            },
            "status": "ingested",
            "created_at": datetime.utcnow() - timedelta(days=2),
            "updated_at": datetime.utcnow(),
        }
    )
    print(f"      ✓ Added blood report (ingested)")

    # Add task for blood report review
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "document_review",
            "title": f"Review Blood Test Results - {patient_name}",
            "description": "Recent blood work shows elevated cholesterol (245 mg/dL) and low HDL (42 mg/dL). Please review results and recommend treatment plan. Consider statin therapy.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "doc_id": doc_id,
            "assigned_to": DOCTORS[0],
            "agent_type": "ai_agent",
            "priority": "high",
            "state": "open",
            "confidence_score": 0.92,
            "waiting_minutes": 45,
            "created_at": datetime.utcnow() - timedelta(hours=2),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Created task: Review blood report (HIGH priority)")

    # PATIENT 2: Consent Forms Needed Stage
    patient_id, patient_name, stage = patient_data_list[1]
    print(f"\n   Patient 2: {patient_name}")

    # Add uploaded documents
    for doc_name in [
        "Medical History Summary.pdf",
        "Insurance Card Front.pdf",
        "Insurance Card Back.pdf",
    ]:
        doc_id = str(uuid4())
        await db.documents.insert_one(
            {
                "_id": doc_id,
                "tenant_id": DEFAULT_TENANT,
                "patient_id": patient_id,
                "kind": "medical_history",
                "file": {
                    "url": f"/uploads/{doc_id}/{doc_name}",
                    "name": doc_name,
                    "mime": "application/pdf",
                    "size": random.randint(150000, 350000),
                    "sha256": f"hash-{doc_id[:8]}",
                },
                "ocr": {"done": True, "engine": "tesseract"},
                "extracted": {"fields": {}, "confidence": 0.88},
                "status": "ingested",
                "created_at": datetime.utcnow() - timedelta(days=1),
                "updated_at": datetime.utcnow(),
            }
        )
    print(f"      ✓ Added 3 documents (all ingested)")

    # Add task for sending consent forms
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "consent_forms",
            "title": f"Send Consent Forms - {patient_name}",
            "description": "All medical records and insurance documentation have been uploaded and verified. Ready to send consent forms for insurance information release and medical records request via DocuSign.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": BACKOFFICE_STAFF[0],
            "agent_type": "human",
            "priority": "medium",
            "state": "open",
            "confidence_score": 1.0,
            "waiting_minutes": 120,
            "created_at": datetime.utcnow() - timedelta(hours=5),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Created task: Send consent forms (MEDIUM priority)")

    # PATIENT 3: Ready for Consultation Stage
    patient_id, patient_name, stage = patient_data_list[2]
    print(f"\n   Patient 3: {patient_name}")

    # Add signed consent forms
    for i, template_id in enumerate(template_ids):
        template = FORM_TEMPLATES[i]
        form_id = str(uuid4())
        await db.consent_forms.insert_one(
            {
                "_id": form_id,
                "tenant_id": DEFAULT_TENANT,
                "patient_id": patient_id,
                "form_template_id": template_id,
                "name": template["name"],
                "description": template["description"],
                "purpose": template["purpose"],
                "status": "signed",
                "sent_date": datetime.utcnow() - timedelta(days=7),
                "signed_date": datetime.utcnow() - timedelta(days=5),
                "docusign": {
                    "envelope_id": f"env-{form_id[:8]}",
                    "status": "completed",
                    "signed_document_url": f"/signed/{form_id}.pdf",
                },
                "created_at": datetime.utcnow() - timedelta(days=8),
                "updated_at": datetime.utcnow() - timedelta(days=5),
            }
        )
    print(f"      ✓ Added 2 signed consent forms")

    # Add task for scheduling consultation
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "schedule_consultation",
            "title": f"Schedule Initial Consultation - {patient_name}",
            "description": "All medical records submitted and consent forms signed. Patient is ready for initial consultation. Please schedule appointment and send calendar invite.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": BACKOFFICE_STAFF[1],
            "agent_type": "human",
            "priority": "medium",
            "state": "open",
            "confidence_score": 1.0,
            "waiting_minutes": 180,
            "created_at": datetime.utcnow() - timedelta(hours=7),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Created task: Schedule consultation (MEDIUM priority)")

    # PATIENT 4: Insurance Resubmit Stage
    patient_id, patient_name, stage = patient_data_list[3]
    print(f"\n   Patient 4: {patient_name}")

    # Add task for insurance resubmission
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "insurance_verification",
            "title": f"Resubmit Insurance Details - {patient_name}",
            "description": "Prior authorization request was denied due to missing policy holder information. Please contact patient to obtain complete insurance details including policy holder name, date of birth, and policy effective date.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": BACKOFFICE_STAFF[0],
            "agent_type": "ai_agent",
            "priority": "high",
            "state": "open",
            "confidence_score": 0.95,
            "waiting_minutes": 90,
            "created_at": datetime.utcnow() - timedelta(hours=4),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Created task: Resubmit insurance (HIGH priority)")

    # PATIENT 5-8: Additional varied tasks
    print(f"\n   Additional patients (5-8):")

    # Patient 5: Urgent follow-up
    patient_id, patient_name, _ = patient_data_list[4]
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "manual",
            "kind": "urgent_followup",
            "title": f"URGENT: Follow-up on Abnormal A1C - {patient_name}",
            "description": "Patient's A1C levels came back at 9.2%, indicating poorly controlled diabetes. Immediate follow-up required to adjust medication and discuss lifestyle changes. Patient has missed previous appointment.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": DOCTORS[1],
            "agent_type": "human",
            "priority": "urgent",
            "state": "open",
            "confidence_score": 1.0,
            "waiting_minutes": 30,
            "created_at": datetime.utcnow() - timedelta(hours=1),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Patient 5: Urgent follow-up task")

    # Patient 6: Medication review
    patient_id, patient_name, _ = patient_data_list[5]
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "medication_review",
            "title": f"Medication Interaction Check - {patient_name}",
            "description": "Patient recently started new anxiety medication. AI detected potential interaction with thyroid medication. Please review current medication list and adjust dosages if necessary.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": DOCTORS[0],
            "agent_type": "ai_agent",
            "priority": "high",
            "state": "open",
            "confidence_score": 0.87,
            "waiting_minutes": 200,
            "created_at": datetime.utcnow() - timedelta(hours=8),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Patient 6: Medication review task")

    # Patient 7: Prior auth
    patient_id, patient_name, _ = patient_data_list[6]
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "prior_authorization",
            "title": f"Submit Prior Authorization - {patient_name}",
            "description": "Cardiologist recommended cardiac catheterization. Need to submit prior authorization to Medicare with supporting documentation including recent stress test results and medication history.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": BACKOFFICE_STAFF[0],
            "agent_type": "ai_agent",
            "priority": "medium",
            "state": "in_progress",
            "confidence_score": 0.91,
            "waiting_minutes": 300,
            "created_at": datetime.utcnow() - timedelta(days=1),
            "updated_at": datetime.utcnow() - timedelta(hours=3),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Patient 7: Prior auth task (IN PROGRESS)")

    # Patient 8: Routine checkup
    patient_id, patient_name, _ = patient_data_list[7]
    task_id = str(uuid4())
    await db.tasks.insert_one(
        {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "routine_checkup",
            "title": f"Schedule Annual Checkup - {patient_name}",
            "description": "Patient is due for annual preventive care visit. Send reminder and schedule appointment. Include flu shot and routine bloodwork orders.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": BACKOFFICE_STAFF[1],
            "agent_type": "human",
            "priority": "low",
            "state": "open",
            "confidence_score": 1.0,
            "waiting_minutes": 500,
            "created_at": datetime.utcnow() - timedelta(days=2),
            "updated_at": datetime.utcnow(),
        }
    )
    await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"      ✓ Patient 8: Routine checkup task (LOW priority)")

    print("")

    # Create appointments
    print("📅 Creating appointments with varied types...")
    appointment_types = [
        {
            "type": "initial_consultation",
            "title": "Initial Consultation",
            "duration": 60,
        },
        {"type": "follow_up", "title": "Follow-up Visit", "duration": 30},
        {"type": "procedure", "title": "Minor Procedure", "duration": 90},
        {"type": "telehealth", "title": "Telehealth Check-in", "duration": 20},
        {"type": "lab_review", "title": "Lab Results Review", "duration": 30},
        {"type": "consultation", "title": "Specialist Consultation", "duration": 45},
    ]

    for i in range(6):
        patient_id, patient_name, _ = patient_data_list[i]
        apt_type = appointment_types[i]
        apt_id = str(uuid4())
        starts_at = datetime.utcnow() + timedelta(hours=2 + i * 2)

        appointment = {
            "_id": apt_id,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "provider_id": "demo-user",
            "provider_name": DOCTORS[i % 3],
            "type": apt_type["type"],
            "title": apt_type["title"],
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(minutes=apt_type["duration"]),
            "location": (
                f"Room {100 + i}" if apt_type["type"] != "telehealth" else "Virtual"
            ),
            "status": "scheduled",
            "google_calendar": {
                "event_id": f"gcal-{apt_id[:8]}",
                "calendar_id": "primary",
                "event_link": f"https://calendar.google.com/event?eid={apt_id[:10]}",
            },
            "composio_metadata": {
                "action_id": f"composio-{apt_id[:8]}",
                "calendar_service": "google",
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        await db.appointments.insert_one(appointment)
        await db.patients.update_one(
            {"_id": patient_id}, {"$inc": {"appointments_count": 1}}
        )
        print(
            f"   ✓ {patient_name}: {apt_type['title']} at {starts_at.strftime('%I:%M %p')}"
        )
    print("")

    # Create claims with varied statuses
    print("💰 Creating insurance claims with varied statuses...")
    insurance_providers = [
        "Blue Shield",
        "Aetna",
        "UnitedHealthcare",
        "Cigna",
        "Medicare",
        "Medicaid",
    ]
    claim_statuses_varied = [
        "pending",
        "submitted",
        "under_review",
        "approved",
        "denied",
        "received",
    ]

    for i in range(6):
        patient_id, patient_name, _ = patient_data_list[i]
        claim_id = str(uuid4())
        claim_id_display = f"C{random.randint(10000, 99999)}"
        amount = random.choice([1500, 2500, 3500, 4200, 5800])
        status = claim_statuses_varied[i]

        claim = {
            "_id": claim_id,
            "claim_id": claim_id_display,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "insurance_provider": insurance_providers[i],
            "amount": amount * 100,
            "amount_display": amount,
            "procedure_code": f"99{random.randint(213, 215)}",
            "diagnosis_code": random.choice(["Z00.00", "E11.9", "I10", "J45.9"]),
            "service_date": (
                datetime.utcnow() - timedelta(days=random.randint(10, 45))
            ).strftime("%Y-%m-%d"),
            "submitted_date": (
                datetime.utcnow() - timedelta(days=random.randint(5, 20))
            ).strftime("%Y-%m-%d"),
            "description": "Medical consultation with diagnostic tests",
            "status": status,
            "last_event_at": datetime.utcnow(),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(5, 25)),
            "updated_at": datetime.utcnow(),
        }
        await db.claims.insert_one(claim)

        # Create claim events
        event = {
            "_id": str(uuid4()),
            "tenant_id": DEFAULT_TENANT,
            "claim_id": claim_id,
            "event_type": "submitted",
            "description": f"Claim submitted to {claim['insurance_provider']} for ${amount:.2f}",
            "at": claim["created_at"],
            "time": claim["created_at"].strftime("%I:%M %p"),
            "created_at": claim["created_at"],
        }
        await db.claim_events.insert_one(event)

        print(f"   ✓ {patient_name}: ${amount} - {status}")
    print("")

    client.close()

    print("✅ Enhanced seed data creation complete!")
    print("")
    print("📊 Summary:")
    print(f"   - {len(PATIENTS)} patients (varied statuses)")
    print(f"   - 8+ tasks (varied priorities & stages)")
    print(f"   - 6 appointments (varied types)")
    print(f"   - 6 claims (varied statuses)")
    print(f"   - Multiple documents (varied statuses)")
    print(f"   - Consent forms (varied statuses)")
    print("")
    print("👥 Staff:")
    print(f"   Doctors: {', '.join(DOCTORS)}")
    print(f"   Back Office: {', '.join(BACKOFFICE_STAFF)}")
    print("")
    print("🤖 AI Agents:")
    for agent in AGENT_TYPES:
        print(f"   - {agent}")
    print("")


if __name__ == "__main__":
    asyncio.run(seed_database())
