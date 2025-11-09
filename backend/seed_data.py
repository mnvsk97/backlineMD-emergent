"""
Comprehensive seed data for BacklineMD hackathon demo
Run with: python seed_data.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random
from uuid import uuid4

MONGO_URL = "mongodb://localhost:27017"
DEFAULT_TENANT = "hackathon-demo"

# Sample data
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
        "profile_image": "https://i.pravatar.cc/150?img=12"
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
        "profile_image": "https://i.pravatar.cc/150?img=45"
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
        "profile_image": "https://i.pravatar.cc/150?img=33"
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
        "profile_image": "https://i.pravatar.cc/150?img=23"
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
        "profile_image": "https://i.pravatar.cc/150?img=52"
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
        "profile_image": "https://i.pravatar.cc/150?img=38"
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
        "profile_image": "https://i.pravatar.cc/150?img=60"
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
        "profile_image": "https://i.pravatar.cc/150?img=47"
    }
]

FORM_TEMPLATES = [
    {
        "name": "Insurance Information Release",
        "description": "Authorization to release medical information to insurance provider",
        "purpose": "Insurance verification and claims processing"
    },
    {
        "name": "Medical Records Request",
        "description": "Authorization to request medical records from external providers",
        "purpose": "Obtain complete medical history"
    }
]

DOCUMENTS = [
    {
        "kind": "lab",
        "file_name": "Blood Test Results - Oct 2024.pdf",
        "status": "ingested"
    },
    {
        "kind": "imaging",
        "file_name": "X-Ray Chest - Sep 2024.pdf",
        "status": "ingested"
    },
    {
        "kind": "medical_history",
        "file_name": "Medical History Summary.pdf",
        "status": "not_ingested"
    },
    {
        "kind": "lab",
        "file_name": "A1C Test Results.pdf",
        "status": "ingested"
    }
]


def generate_ngrams(text: str, n: int = 3):
    """Generate n-grams for search"""
    text = text.lower().replace(" ", "")
    return [text[i:i+n] for i in range(len(text) - n + 1)]


async def seed_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.backlinemd
    
    print("🌱 Starting seed data creation...")
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
        await db.form_templates.insert_one({
            "_id": template_id,
            "tenant_id": DEFAULT_TENANT,
            **template,
            "template_url": f"/templates/{template_id}.pdf",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        template_ids.append(template_id)
        print(f"   ✓ {template['name']}")
    print("")
    
    # Create patients
    print("👥 Creating patients...")
    patient_ids = []
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
                "address": {}
            },
            "preconditions": patient_data["preconditions"],
            "flags": [],
            "latest_vitals": {},
            "profile_image": patient_data["profile_image"],
            "status": "Active",
            "tasks_count": 0,
            "appointments_count": 0,
            "flagged_count": 0,
            "search": {"ngrams": ngrams},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.patients.insert_one(patient)
        patient_ids.append((patient_id, full_name))
        print(f"   ✓ {full_name} (Age: {patient_data['age']}, {patient_data['gender']})")
    print("")
    
    # Create documents for first 3 patients
    print("📄 Creating documents...")
    doc_count = 0
    for i in range(3):
        patient_id, patient_name = patient_ids[i]
        for doc_template in DOCUMENTS[:2]:  # 2 docs per patient
            document_id = str(uuid4())
            doc = {
                "_id": document_id,
                "tenant_id": DEFAULT_TENANT,
                "patient_id": patient_id,
                "kind": doc_template["kind"],
                "file": {
                    "url": f"/uploads/{document_id}/{doc_template['file_name']}",
                    "name": doc_template["file_name"],
                    "mime": "application/pdf",
                    "size": random.randint(100000, 500000),
                    "sha256": f"hash-{document_id[:8]}"
                },
                "ocr": {"done": True, "engine": "tesseract"},
                "extracted": {
                    "fields": {
                        "test_type": "Blood Panel" if doc_template["kind"] == "lab" else "X-Ray",
                        "date": "2024-10-15",
                        "result": "Normal"
                    },
                    "confidence": 0.92 if doc_template["status"] == "ingested" else 0.85
                },
                "status": doc_template["status"],
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "updated_at": datetime.utcnow()
            }
            await db.documents.insert_one(doc)
            doc_count += 1
    print(f"   ✓ Created {doc_count} documents")
    print("")
    
    # Create consent forms
    print("📝 Creating consent forms...")
    form_statuses = ["to_do", "sent", "signed"]
    form_count = 0
    for i, (patient_id, patient_name) in enumerate(patient_ids[:5]):
        for j, template_id in enumerate(template_ids):
            template = FORM_TEMPLATES[j]
            status = form_statuses[i % 3]
            
            form_data = {
                "_id": str(uuid4()),
                "tenant_id": DEFAULT_TENANT,
                "patient_id": patient_id,
                "form_template_id": template_id,
                "name": template["name"],
                "description": template["description"],
                "purpose": template["purpose"],
                "status": status,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if status in ["sent", "signed"]:
                form_data["sent_date"] = datetime.utcnow() - timedelta(days=random.randint(1, 10))
            
            if status == "signed":
                form_data["signed_date"] = datetime.utcnow() - timedelta(days=random.randint(1, 5))
                form_data["docusign"] = {
                    "envelope_id": f"env-{str(uuid4())[:8]}",
                    "status": "completed",
                    "signed_document_url": f"/signed/{form_data['_id']}.pdf"
                }
            
            await db.consent_forms.insert_one(form_data)
            form_count += 1
    print(f"   ✓ Created {form_count} consent forms")
    print("")
    
    # Create tasks
    print("✅ Creating tasks...")
    for i in range(3):
        patient_id, patient_name = patient_ids[i]
        task_id = str(uuid4())
        task = {
            "_id": task_id,
            "task_id": f"T{random.randint(10000, 99999)}",
            "tenant_id": DEFAULT_TENANT,
            "source": "agent",
            "kind": "document_review",
            "title": f"Verify Medical History Extraction - {patient_name}",
            "description": f"Review extracted data from recent upload. Confidence: {random.randint(85, 92)}%. Please verify key findings.",
            "patient_id": patient_id,
            "patient_name": patient_name,
            "assigned_to": "Dr. James O'Brien",
            "agent_type": "ai_agent",
            "priority": random.choice(["high", "medium", "urgent"]),
            "state": "open",
            "confidence_score": random.uniform(0.85, 0.92),
            "waiting_minutes": random.randint(10, 120),
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
            "updated_at": datetime.utcnow()
        }
        await db.tasks.insert_one(task)
        await db.patients.update_one({"_id": patient_id}, {"$inc": {"tasks_count": 1}})
    print(f"   ✓ Created 3 tasks")
    print("")
    
    # Create appointments
    print("📅 Creating appointments...")
    for i in range(4):
        patient_id, patient_name = patient_ids[i]
        apt_id = str(uuid4())
        starts_at = datetime.utcnow() + timedelta(hours=2 + i*2)
        appointment = {
            "_id": apt_id,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "provider_id": "demo-user",
            "type": random.choice(["consultation", "follow_up", "procedure"]),
            "title": f"{random.choice(['Follow-up', 'Initial', 'Routine'])} Consultation",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=1),
            "location": f"Room {100 + i}",
            "status": "scheduled",
            "google_calendar": {
                "event_id": f"gcal-{apt_id[:8]}",
                "calendar_id": "primary"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.appointments.insert_one(appointment)
        await db.patients.update_one({"_id": patient_id}, {"$inc": {"appointments_count": 1}})
    print(f"   ✓ Created 4 appointments")
    print("")
    
    # Create claims
    print("💰 Creating insurance claims...")
    insurance_providers = ["Blue Shield", "Aetna", "UnitedHealthcare", "Cigna"]
    for i in range(4):
        patient_id, patient_name = patient_ids[i]
        claim_id = str(uuid4())
        claim_id_display = f"C{random.randint(10000, 99999)}"
        amount = random.choice([1500, 2500, 3500, 4200])
        
        claim = {
            "_id": claim_id,
            "claim_id": claim_id_display,
            "tenant_id": DEFAULT_TENANT,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "insurance_provider": insurance_providers[i % 4],
            "amount": amount * 100,
            "amount_display": amount,
            "procedure_code": f"99{random.randint(213, 215)}",
            "diagnosis_code": random.choice(["Z00.00", "E11.9", "I10"]),
            "service_date": (datetime.utcnow() - timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d"),
            "submitted_date": (datetime.utcnow() - timedelta(days=random.randint(1, 15))).strftime("%Y-%m-%d"),
            "description": "Medical consultation with diagnostic tests",
            "status": random.choice(["pending", "pending", "approved", "denied"]),
            "last_event_at": datetime.utcnow(),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 20)),
            "updated_at": datetime.utcnow()
        }
        await db.claims.insert_one(claim)
        
        # Create claim event
        event = {
            "_id": str(uuid4()),
            "tenant_id": DEFAULT_TENANT,
            "claim_id": claim_id,
            "event_type": "submitted",
            "description": f"Claim submitted to {claim['insurance_provider']} for ${amount:.2f}",
            "at": claim["created_at"],
            "time": claim["created_at"].strftime("%I:%M %p"),
            "created_at": claim["created_at"]
        }
        await db.claim_events.insert_one(event)
    print(f"   ✓ Created 4 claims with events")
    print("")
    
    client.close()
    
    print("✅ Seed data creation complete!")
    print("")
    print("Summary:")
    print(f"   - {len(PATIENTS)} patients")
    print(f"   - {doc_count} documents")
    print(f"   - {form_count} consent forms")
    print(f"   - {len(template_ids)} form templates")
    print(f"   - 3 tasks")
    print(f"   - 4 appointments")
    print(f"   - 4 claims")
    print("")

if __name__ == "__main__":
    asyncio.run(seed_database())
