from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from datetime import datetime

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client: Optional[AsyncIOMotorClient] = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.backlinemd
    print(f"✓ Connected to MongoDB at {MONGO_URL}")
    
    # Create indexes
    await create_indexes()

async def close_db():
    global client
    if client:
        client.close()
        print("✓ Closed MongoDB connection")

async def create_indexes():
    """Create all necessary indexes for collections"""
    print("Creating indexes...")
    
    # Users
    await db.users.create_index([("tenant_id", 1), ("email", 1)], unique=True)
    
    # Patients
    await db.patients.create_index([("tenant_id", 1), ("search.ngrams", 1)])
    await db.patients.create_index([("tenant_id", 1), ("mrn", 1)], unique=True)
    
    # Documents
    await db.documents.create_index([("tenant_id", 1), ("patient_id", 1), ("kind", 1), ("created_at", -1)])
    await db.documents.create_index([("tenant_id", 1), ("status", 1), ("created_at", -1)])
    
    # Consent Forms
    await db.consent_forms.create_index([("tenant_id", 1), ("patient_id", 1), ("status", 1)])
    
    # Appointments
    await db.appointments.create_index([("tenant_id", 1), ("provider_id", 1), ("starts_at", 1)])
    await db.appointments.create_index([("tenant_id", 1), ("patient_id", 1), ("starts_at", 1)])
    
    # Claims
    await db.claims.create_index([("tenant_id", 1), ("status", 1), ("last_event_at", -1)])
    await db.claims.create_index([("tenant_id", 1), ("patient_id", 1)])
    
    # Claim Events
    await db.claim_events.create_index([("tenant_id", 1), ("claim_id", 1), ("at", 1)])
    
    # Tasks
    await db.tasks.create_index([("tenant_id", 1), ("assignee_id", 1), ("state", 1), ("due_at", 1)])
    await db.tasks.create_index([("tenant_id", 1), ("source", 1), ("state", 1), ("created_at", -1)])
    await db.tasks.create_index([("tenant_id", 1), ("patient_id", 1), ("state", 1)])
    
    # Conversations
    await db.conversations.create_index([("tenant_id", 1), ("subject.patient_id", 1), ("last_msg_at", -1)])
    
    # Messages
    await db.messages.create_index([("tenant_id", 1), ("conversation_id", 1), ("created_at", 1)])
    
    # Agent Executions
    await db.agent_executions.create_index([("tenant_id", 1), ("agent", 1), ("status", 1), ("updated_at", -1)])
    await db.agent_executions.create_index([("tenant_id", 1), ("run_id", 1)], unique=True)
    
    # AI Artifacts (TTL)
    await db.ai_artifacts.create_index([("expires_at", 1)], expireAfterSeconds=0)
    
    # Voice Calls
    await db.voice_calls.create_index([("tenant_id", 1), ("patient_id", 1), ("created_at", -1)])
    
    print("✓ All indexes created")

def get_db():
    return db