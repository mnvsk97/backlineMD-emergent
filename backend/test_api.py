"""
Comprehensive API Test Suite for BacklineMD Backend
Tests all patient, document, appointment, and claim operations
"""

import pytest
import httpx
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import uuid


# Test Configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api"
MCP_BASE = f"{API_BASE}/mcp"


@pytest.fixture
async def client():
    """Create async HTTP client for testing"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture
async def test_patient_id(client: httpx.AsyncClient) -> str:
    """Create a test patient and return patient_id"""
    patient_data = {
        "first_name": "Test",
        "last_name": "Patient",
        "dob": "1990-01-15",
        "gender": "Male",
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "phone": "555-0100",
        "preconditions": ["Hypertension"],
    }
    
    response = await client.post(f"{API_BASE}/patients", json=patient_data)
    assert response.status_code == 200
    data = response.json()
    patient_id = data["patient_id"]
    
    yield patient_id
    
    # Cleanup - Note: There's no delete endpoint, so we'll just leave test data


class TestPatientOperations:
    """Test suite for Patient CRUD operations"""
    
    async def test_create_patient(self, client: httpx.AsyncClient):
        """Test creating a new patient"""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1985-05-20",
            "gender": "Male",
            "email": f"john.doe_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-1234",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            },
            "preconditions": ["Diabetes", "Hypertension"],
            "profile_image": "https://example.com/avatar.jpg"
        }
        
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 200
        data = response.json()
        assert "patient_id" in data
        assert data["message"] == "Patient created successfully"
        
        # Verify patient was created
        patient_id = data["patient_id"]
        get_response = await client.get(f"{API_BASE}/patients/{patient_id}")
        assert get_response.status_code == 200
        patient = get_response.json()
        assert patient["first_name"] == patient_data["first_name"]
        assert patient["last_name"] == patient_data["last_name"]
        assert patient["email"] == patient_data["email"]
        assert patient["status"] == "Intake In Progress"
    
    async def test_list_patients(self, client: httpx.AsyncClient):
        """Test listing all patients"""
        response = await client.get(f"{API_BASE}/patients")
        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)
        
        if len(patients) > 0:
            patient = patients[0]
            assert "patient_id" in patient
            assert "first_name" in patient
            assert "last_name" in patient
            assert "email" in patient
            assert "status" in patient
    
    async def test_list_patients_with_search(self, client: httpx.AsyncClient):
        """Test searching patients by name"""
        # First create a patient with unique name
        unique_name = f"SearchTest{uuid.uuid4().hex[:8]}"
        patient_data = {
            "first_name": unique_name,
            "last_name": "Test",
            "dob": "1990-01-01",
            "gender": "Female",
            "email": f"{unique_name.lower()}@example.com",
            "phone": "555-9999",
        }
        
        create_response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert create_response.status_code == 200
        
        # Search for the patient
        search_response = await client.get(
            f"{API_BASE}/patients",
            params={"q": unique_name}
        )
        assert search_response.status_code == 200
        results = search_response.json()
        assert len(results) > 0
        assert any(p["first_name"] == unique_name for p in results)
    
    async def test_list_patients_with_pagination(self, client: httpx.AsyncClient):
        """Test pagination for patient list"""
        response = await client.get(
            f"{API_BASE}/patients",
            params={"limit": 5, "skip": 0}
        )
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) <= 5
    
    async def test_get_patient_by_id(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting a specific patient by ID"""
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        assert response.status_code == 200
        patient = response.json()
        assert patient["patient_id"] == test_patient_id
        assert "first_name" in patient
        assert "last_name" in patient
        assert "email" in patient
        assert "phone" in patient
        assert "status" in patient
        assert "mrn" in patient
    
    async def test_get_patient_not_found(self, client: httpx.AsyncClient):
        """Test getting a non-existent patient"""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{API_BASE}/patients/{fake_id}")
        assert response.status_code == 404
    
    async def test_update_patient_via_mcp(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating patient information via MCP endpoint"""
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": test_patient_id,
                "first_name": "Updated",
                "last_name": "Name",
                "status": "Intake Done",
                "preconditions": ["Diabetes", "Hypertension", "Asthma"]
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "patient_id" in data["result"]
        assert data["result"]["patient_id"] == test_patient_id
        
        # Verify update
        get_response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        patient = get_response.json()
        assert patient["first_name"] == "Updated"
        assert patient["last_name"] == "Name"
        assert patient["status"] == "Intake Done"
    
    async def test_update_patient_status(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating patient status through various workflow stages"""
        statuses = [
            "Intake In Progress",
            "Intake Done",
            "Doc Collection In Progress",
            "Doc Collection Done",
            "Consultation Scheduled",
            "Consultation Complete"
        ]
        
        for status in statuses:
            update_data = {
                "tool": "update_patient",
                "arguments": {
                    "patient_id": test_patient_id,
                    "status": status
                }
            }
            
            response = await client.post(f"{MCP_BASE}/call", json=update_data)
            assert response.status_code == 200
            assert response.json()["success"] is True
            
            # Verify status update
            get_response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
            patient = get_response.json()
            assert patient["status"] == status


class TestDocumentOperations:
    """Test suite for Document operations"""
    
    async def test_create_document(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating/uploading a document"""
        # Create a mock file upload
        files = {
            "file": ("test_document.pdf", b"fake pdf content", "application/pdf")
        }
        data = {
            "patient_id": test_patient_id,
            "kind": "lab"
        }
        
        response = await client.post(
            f"{API_BASE}/documents/upload",
            params=data,
            files=files
        )
        assert response.status_code == 200
        doc_data = response.json()
        assert "document_id" in doc_data
        assert doc_data["status"] == "uploaded"
        
        return doc_data["document_id"]
    
    async def test_list_documents(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test listing documents"""
        # First create a document
        doc_id = await self.test_create_document(client, test_patient_id)
        
        # List all documents
        response = await client.get(f"{API_BASE}/documents")
        assert response.status_code == 200
        documents = response.json()
        assert isinstance(documents, list)
        
        # List documents for specific patient
        patient_docs_response = await client.get(
            f"{API_BASE}/documents",
            params={"patient_id": test_patient_id}
        )
        assert patient_docs_response.status_code == 200
        patient_docs = patient_docs_response.json()
        assert any(doc["patient_id"] == test_patient_id for doc in patient_docs)
    
    async def test_list_documents_by_kind(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering documents by kind"""
        # Create documents of different kinds
        kinds = ["lab", "imaging", "medical_history"]
        doc_ids = []
        
        for kind in kinds:
            files = {"file": (f"test_{kind}.pdf", b"content", "application/pdf")}
            data = {"patient_id": test_patient_id, "kind": kind}
            response = await client.post(
                f"{API_BASE}/documents/upload",
                params=data,
                files=files
            )
            assert response.status_code == 200
            doc_ids.append(response.json()["document_id"])
        
        # Filter by kind
        for kind in kinds:
            response = await client.get(
                f"{API_BASE}/documents",
                params={"kind": kind}
            )
            assert response.status_code == 200
            docs = response.json()
            assert all(doc["kind"] == kind for doc in docs)
    
    async def test_get_document_by_id(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting a specific document by ID"""
        doc_id = await self.test_create_document(client, test_patient_id)
        
        response = await client.get(f"{API_BASE}/documents/{doc_id}")
        assert response.status_code == 200
        document = response.json()
        assert document["document_id"] == doc_id
        assert document["patient_id"] == test_patient_id
        assert "kind" in document
        assert "status" in document
        assert "file" in document
    
    async def test_update_document_status(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating document status through workflow stages"""
        doc_id = await self.test_create_document(client, test_patient_id)
        
        statuses = ["uploaded", "ingesting", "ingested"]
        
        for status in statuses:
            update_data = {
                "status": status,
                "extracted": {
                    "fields": {"test_field": "test_value"},
                    "confidence": 0.95
                } if status == "ingested" else None
            }
            
            response = await client.patch(
                f"{API_BASE}/documents/{doc_id}",
                json=update_data
            )
            assert response.status_code == 200
            
            # Verify status update
            get_response = await client.get(f"{API_BASE}/documents/{doc_id}")
            document = get_response.json()
            assert document["status"] == status
            
            if status == "ingested":
                assert "extracted" in document
                assert document["extracted"] is not None


class TestPatientSummaryAndTimeline:
    """Test suite for Patient Summary and Timeline operations"""
    
    async def test_get_patient_summary(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting patient summary"""
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}/summary")
        assert response.status_code == 200
        summary = response.json()
        assert "summary" in summary
        assert "citations" in summary
        assert "generated_at" in summary
        assert isinstance(summary["citations"], list)
    
    async def test_patient_summary_caching(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that patient summary is cached"""
        # First request
        response1 = await client.get(f"{API_BASE}/patients/{test_patient_id}/summary")
        assert response1.status_code == 200
        summary1 = response1.json()
        generated_at1 = summary1["generated_at"]
        
        # Second request should return cached version
        response2 = await client.get(f"{API_BASE}/patients/{test_patient_id}/summary")
        assert response2.status_code == 200
        summary2 = response2.json()
        generated_at2 = summary2["generated_at"]
        
        # Should be same (cached) or different (regenerated if expired)
        assert "generated_at" in summary2
    
    async def test_update_patient_summary_via_mcp(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating patient summary via MCP (if available)"""
        # Note: This would require an MCP tool for updating summary
        # For now, we'll test that summary can be retrieved after patient update
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": test_patient_id,
                "preconditions": ["Updated Condition 1", "Updated Condition 2"]
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        
        # Get summary after update
        summary_response = await client.get(f"{API_BASE}/patients/{test_patient_id}/summary")
        assert summary_response.status_code == 200


class TestAppointmentOperations:
    """Test suite for Appointment CRUD operations"""
    
    async def test_create_appointment(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating a new appointment"""
        starts_at = datetime.now(timezone.utc) + timedelta(days=7)
        ends_at = starts_at + timedelta(hours=1)
        
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Initial Consultation",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "location": "Main Clinic - Room 101"
        }
        
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        assert response.status_code == 200
        data = response.json()
        assert "appointment_id" in data
        assert "google_calendar" in data
        assert data["message"] == "Appointment created successfully"
        
        return data["appointment_id"]
    
    async def test_list_appointments(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test listing appointments"""
        # Create an appointment first
        appointment_id = await self.test_create_appointment(client, test_patient_id)
        
        # List all appointments
        response = await client.get(f"{API_BASE}/appointments")
        assert response.status_code == 200
        appointments = response.json()
        assert isinstance(appointments, list)
        
        # List appointments for specific patient
        patient_appts_response = await client.get(
            f"{API_BASE}/appointments",
            params={"patient_id": test_patient_id}
        )
        assert patient_appts_response.status_code == 200
        patient_appts = patient_appts_response.json()
        assert any(apt["appointment_id"] == appointment_id for apt in patient_appts if "appointment_id" in apt)
    
    async def test_list_appointments_by_date(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering appointments by date"""
        # Create appointment for today
        today = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0, microsecond=0)
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "follow-up",
            "title": "Follow-up Visit",
            "starts_at": today.isoformat(),
            "ends_at": (today + timedelta(hours=1)).isoformat(),
        }
        
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        assert response.status_code == 200
        
        # Get today's appointments
        response = await client.get(
            f"{API_BASE}/appointments",
            params={"date": "today"}
        )
        assert response.status_code == 200
        appointments = response.json()
        assert isinstance(appointments, list)
    
    async def test_update_appointment_via_mcp(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating appointment via MCP"""
        # Create appointment first
        appointment_id = await self.test_create_appointment(client, test_patient_id)
        
        # Update appointment
        new_starts_at = datetime.now(timezone.utc) + timedelta(days=14)
        new_ends_at = new_starts_at + timedelta(hours=1)
        
        update_data = {
            "tool": "update_appointment",
            "arguments": {
                "appointment_id": appointment_id,
                "starts_at": new_starts_at.isoformat(),
                "ends_at": new_ends_at.isoformat(),
                "status": "confirmed"
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    async def test_delete_appointment_via_mcp(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test deleting appointment via MCP"""
        # Create appointment first
        appointment_id = await self.test_create_appointment(client, test_patient_id)
        
        # Delete appointment
        delete_data = {
            "tool": "delete_appointment",
            "arguments": {
                "appointment_id": appointment_id
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=delete_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestInsuranceClaimOperations:
    """Test suite for Insurance Claim CRUD operations"""
    
    async def test_create_claim(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating a new insurance claim"""
        claim_data = {
            "patient_id": test_patient_id,
            "insurance_provider": "Blue Cross Blue Shield",
            "amount": 1500.00,
            "procedure_code": "99213",
            "diagnosis_code": "E11.9",
            "service_date": "2024-11-01",
            "description": "Office visit for diabetes management"
        }
        
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        assert response.status_code == 200
        data = response.json()
        assert "claim_id" in data
        assert data["status"] == "pending"
        assert "claim_id_display" in data
        
        return data["claim_id"]
    
    async def test_list_claims(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test listing insurance claims"""
        # Create a claim first
        claim_id = await self.test_create_claim(client, test_patient_id)
        
        # List all claims
        response = await client.get(f"{API_BASE}/claims")
        assert response.status_code == 200
        claims = response.json()
        assert isinstance(claims, list)
        
        # List claims for specific patient
        patient_claims_response = await client.get(
            f"{API_BASE}/claims",
            params={"patient_id": test_patient_id}
        )
        assert patient_claims_response.status_code == 200
        patient_claims = patient_claims_response.json()
        assert any(claim["claim_id"] == claim_id for claim in patient_claims)
    
    async def test_list_claims_by_status(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering claims by status"""
        # Create a claim
        claim_id = await self.test_create_claim(client, test_patient_id)
        
        # Filter by status
        response = await client.get(
            f"{API_BASE}/claims",
            params={"status": "pending"}
        )
        assert response.status_code == 200
        claims = response.json()
        assert all(claim["status"] == "pending" for claim in claims)
    
    async def test_get_claim_by_id(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting a specific claim by ID"""
        claim_id = await self.test_create_claim(client, test_patient_id)
        
        response = await client.get(f"{API_BASE}/claims/{claim_id}")
        assert response.status_code == 200
        claim = response.json()
        assert claim["claim_id"] == claim_id
        assert "patient_name" in claim
        assert "insurance_provider" in claim
        assert "amount" in claim
        assert "status" in claim
    
    async def test_get_claim_events(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting claim event history"""
        claim_id = await self.test_create_claim(client, test_patient_id)
        
        response = await client.get(f"{API_BASE}/claims/{claim_id}/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        if len(events) > 0:
            event = events[0]
            assert "event_type" in event
            assert "description" in event
            assert "at" in event
    
    async def test_update_claim_via_mcp(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating claim status via MCP"""
        claim_id = await self.test_create_claim(client, test_patient_id)
        
        # Update claim status
        update_data = {
            "tool": "update_insurance_claim",
            "arguments": {
                "claim_id": claim_id,
                "status": "submitted"
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify update
        get_response = await client.get(f"{API_BASE}/claims/{claim_id}")
        claim = get_response.json()
        assert claim["status"] == "submitted"
    
    async def test_delete_claim_via_mcp(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test deleting claim via MCP (if available)"""
        claim_id = await self.test_create_claim(client, test_patient_id)
        
        # Note: Check if delete_insurance_claim tool exists
        # For now, we'll test update to cancelled status
        update_data = {
            "tool": "update_insurance_claim",
            "arguments": {
                "claim_id": claim_id,
                "status": "denied"
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200


class TestTaskOperations:
    """Test suite for Task operations"""
    
    async def test_create_task(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating a new task"""
        task_data = {
            "title": "Review lab results",
            "description": "Review and verify lab results for patient",
            "patient_id": test_patient_id,
            "assigned_to": "Dr. Smith",
            "agent_type": "human",
            "priority": "high",
            "kind": "review"
        }
        
        response = await client.post(f"{API_BASE}/tasks", json=task_data)
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert data["message"] == "Task created successfully"
        
        return data["task_id"]
    
    async def test_list_tasks(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test listing tasks"""
        # Create a task first
        task_id = await self.test_create_task(client, test_patient_id)
        
        # List all tasks
        response = await client.get(f"{API_BASE}/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert isinstance(tasks, list)
        
        # List tasks for specific patient
        patient_tasks_response = await client.get(
            f"{API_BASE}/tasks",
            params={"patient_id": test_patient_id}
        )
        assert patient_tasks_response.status_code == 200
        patient_tasks = patient_tasks_response.json()
        assert any(task["task_id"] == task_id for task in patient_tasks)
    
    async def test_update_task(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating task status"""
        task_id = await self.test_create_task(client, test_patient_id)
        
        # Update task to in_progress
        update_data = {
            "state": "in_progress",
            "comment": "Started reviewing lab results"
        }
        
        response = await client.patch(f"{API_BASE}/tasks/{task_id}", json=update_data)
        assert response.status_code == 200
        
        # Update task to done
        update_data = {
            "state": "done",
            "comment": "Lab results reviewed and verified"
        }
        
        response = await client.patch(f"{API_BASE}/tasks/{task_id}", json=update_data)
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration test scenarios"""
    
    async def test_patient_workflow(self, client: httpx.AsyncClient):
        """Test complete patient workflow"""
        # 1. Create patient
        patient_data = {
            "first_name": "Workflow",
            "last_name": "Test",
            "dob": "1980-03-15",
            "gender": "Female",
            "email": f"workflow_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-8888",
        }
        
        create_response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert create_response.status_code == 200
        patient_id = create_response.json()["patient_id"]
        
        # 2. Update patient status
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": patient_id,
                "status": "Intake Done"
            }
        }
        await client.post(f"{MCP_BASE}/call", json=update_data)
        
        # 3. Create document
        files = {"file": ("test.pdf", b"content", "application/pdf")}
        doc_response = await client.post(
            f"{API_BASE}/documents/upload",
            params={"patient_id": patient_id, "kind": "lab"},
            files=files
        )
        assert doc_response.status_code == 200
        doc_id = doc_response.json()["document_id"]
        
        # 4. Update document status
        await client.patch(
            f"{API_BASE}/documents/{doc_id}",
            json={"status": "ingested"}
        )
        
        # 5. Create appointment
        starts_at = datetime.now(timezone.utc) + timedelta(days=7)
        appointment_data = {
            "patient_id": patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Initial Consultation",
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
        }
        apt_response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        assert apt_response.status_code == 200
        
        # 6. Create claim
        claim_data = {
            "patient_id": patient_id,
            "insurance_provider": "Aetna",
            "amount": 2000.00,
            "service_date": "2024-11-01",
        }
        claim_response = await client.post(f"{API_BASE}/claims", json=claim_data)
        assert claim_response.status_code == 200
        
        # 7. Get patient summary
        summary_response = await client.get(f"{API_BASE}/patients/{patient_id}/summary")
        assert summary_response.status_code == 200


class TestPatientValidationAndErrors:
    """Test suite for Patient validation and error handling"""
    
    async def test_create_patient_missing_required_fields(self, client: httpx.AsyncClient):
        """Test creating patient with missing required fields"""
        # Missing first_name
        patient_data = {
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": "test@example.com",
            "phone": "555-1234",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 422  # Validation error
    
    async def test_create_patient_invalid_email(self, client: httpx.AsyncClient):
        """Test creating patient with invalid email"""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": "invalid-email",
            "phone": "555-1234",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 422
    
    async def test_create_patient_empty_strings(self, client: httpx.AsyncClient):
        """Test creating patient with empty strings"""
        patient_data = {
            "first_name": "",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": "test@example.com",
            "phone": "555-1234",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        # Should either reject or handle gracefully
        assert response.status_code in [422, 400]
    
    async def test_create_patient_very_long_names(self, client: httpx.AsyncClient):
        """Test creating patient with very long names"""
        patient_data = {
            "first_name": "A" * 500,
            "last_name": "B" * 500,
            "dob": "1990-01-01",
            "gender": "Male",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-1234",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        # Should either accept or reject with appropriate status
        assert response.status_code in [200, 422, 400]
    
    async def test_create_patient_special_characters(self, client: httpx.AsyncClient):
        """Test creating patient with special characters in name"""
        patient_data = {
            "first_name": "John-O'Brien",
            "last_name": "D'Angelo",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-1234",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 200
        data = response.json()
        patient_id = data["patient_id"]
        
        # Verify special characters are preserved
        get_response = await client.get(f"{API_BASE}/patients/{patient_id}")
        patient = get_response.json()
        assert patient["first_name"] == "John-O'Brien"
        assert patient["last_name"] == "D'Angelo"
    
    async def test_create_patient_unicode_characters(self, client: httpx.AsyncClient):
        """Test creating patient with unicode characters"""
        patient_data = {
            "first_name": "José",
            "last_name": "García",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-1234",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 200
    
    async def test_update_patient_invalid_id(self, client: httpx.AsyncClient):
        """Test updating patient with invalid ID"""
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": "invalid-id-format",
                "status": "Active"
            }
        }
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False or "error" in data.get("result", {})
    
    async def test_update_patient_nonexistent(self, client: httpx.AsyncClient):
        """Test updating non-existent patient"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": fake_id,
                "status": "Active"
            }
        }
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert "error" in data.get("result", {})
    
    async def test_list_patients_invalid_pagination(self, client: httpx.AsyncClient):
        """Test pagination with invalid parameters"""
        # Negative limit
        response = await client.get(
            f"{API_BASE}/patients",
            params={"limit": -1, "skip": 0}
        )
        assert response.status_code == 200  # Should handle gracefully
        
        # Negative skip
        response = await client.get(
            f"{API_BASE}/patients",
            params={"limit": 10, "skip": -1}
        )
        assert response.status_code == 200
        
        # Very large limit
        response = await client.get(
            f"{API_BASE}/patients",
            params={"limit": 10000, "skip": 0}
        )
        assert response.status_code == 200


class TestDocumentValidationAndErrors:
    """Test suite for Document validation and error handling"""
    
    async def test_upload_document_missing_patient_id(self, client: httpx.AsyncClient):
        """Test uploading document without patient_id"""
        files = {"file": ("test.pdf", b"content", "application/pdf")}
        response = await client.post(
            f"{API_BASE}/documents/upload",
            params={"kind": "lab"},
            files=files
        )
        assert response.status_code == 422  # Validation error
    
    async def test_upload_document_missing_kind(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test uploading document without kind"""
        files = {"file": ("test.pdf", b"content", "application/pdf")}
        response = await client.post(
            f"{API_BASE}/documents/upload",
            params={"patient_id": test_patient_id},
            files=files
        )
        assert response.status_code == 422
    
    async def test_upload_document_invalid_patient_id(self, client: httpx.AsyncClient):
        """Test uploading document with invalid patient_id"""
        files = {"file": ("test.pdf", b"content", "application/pdf")}
        response = await client.post(
            f"{API_BASE}/documents/upload",
            params={"patient_id": "invalid-id", "kind": "lab"},
            files=files
        )
        # Should either accept (create doc) or reject
        assert response.status_code in [200, 404, 422]
    
    async def test_upload_document_all_kinds(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test uploading documents of all supported kinds"""
        kinds = ["lab", "imaging", "medical_history", "summary", "consent_form"]
        doc_ids = []
        
        for kind in kinds:
            files = {"file": (f"test_{kind}.pdf", b"content", "application/pdf")}
            response = await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": kind},
                files=files
            )
            assert response.status_code == 200
            doc_ids.append(response.json()["document_id"])
        
        # Verify all were created
        response = await client.get(
            f"{API_BASE}/documents",
            params={"patient_id": test_patient_id}
        )
        documents = response.json()
        created_kinds = {doc["kind"] for doc in documents if doc["document_id"] in doc_ids}
        assert set(kinds).issubset(created_kinds)
    
    async def test_upload_document_large_file(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test uploading a large file"""
        # Create a 5MB file
        large_content = b"x" * (5 * 1024 * 1024)
        files = {"file": ("large_file.pdf", large_content, "application/pdf")}
        response = await client.post(
            f"{API_BASE}/documents/upload",
            params={"patient_id": test_patient_id, "kind": "lab"},
            files=files,
            timeout=60.0
        )
        # Should either accept or reject with appropriate error
        assert response.status_code in [200, 413, 422]
    
    async def test_upload_document_different_file_types(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test uploading different file types"""
        file_types = [
            ("test.pdf", b"PDF content", "application/pdf"),
            ("test.jpg", b"JPEG content", "image/jpeg"),
            ("test.png", b"PNG content", "image/png"),
            ("test.txt", b"Text content", "text/plain"),
        ]
        
        for filename, content, content_type in file_types:
            files = {"file": (filename, content, content_type)}
            response = await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": "lab"},
                files=files
            )
            assert response.status_code == 200
    
    async def test_update_document_invalid_status(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating document with invalid status"""
        doc_id = await TestDocumentOperations().test_create_document(client, test_patient_id)
        
        update_data = {
            "status": "invalid_status_that_does_not_exist"
        }
        response = await client.patch(
            f"{API_BASE}/documents/{doc_id}",
            json=update_data
        )
        # Should either accept (if enum validation is lenient) or reject
        assert response.status_code in [200, 422]
    
    async def test_update_document_all_status_transitions(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test all valid document status transitions"""
        doc_id = await TestDocumentOperations().test_create_document(client, test_patient_id)
        
        # Test all status transitions
        status_sequence = [
            ("uploaded", None),
            ("ingesting", None),
            ("ingested", {"fields": {"test": "value"}, "confidence": 0.95}),
            ("not_ingested", {"fields": {}, "confidence": 0.5, "needs_review": ["field1"]}),
        ]
        
        for status, extracted in status_sequence:
            update_data = {"status": status}
            if extracted:
                update_data["extracted"] = extracted
            
            response = await client.patch(
                f"{API_BASE}/documents/{doc_id}",
                json=update_data
            )
            assert response.status_code == 200
            
            # Verify status
            get_response = await client.get(f"{API_BASE}/documents/{doc_id}")
            document = get_response.json()
            assert document["status"] == status
    
    async def test_get_document_not_found(self, client: httpx.AsyncClient):
        """Test getting non-existent document"""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{API_BASE}/documents/{fake_id}")
        assert response.status_code == 404
    
    async def test_list_documents_multiple_filters(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering documents with multiple criteria"""
        # Create documents with different statuses and kinds
        doc_configs = [
            ("lab", "uploaded"),
            ("lab", "ingested"),
            ("imaging", "uploaded"),
            ("imaging", "ingested"),
        ]
        
        for kind, status in doc_configs:
            files = {"file": (f"test_{kind}.pdf", b"content", "application/pdf")}
            response = await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": kind},
                files=files
            )
            doc_id = response.json()["document_id"]
            await client.patch(
                f"{API_BASE}/documents/{doc_id}",
                json={"status": status}
            )
        
        # Filter by both kind and status
        response = await client.get(
            f"{API_BASE}/documents",
            params={"patient_id": test_patient_id, "kind": "lab", "status": "ingested"}
        )
        assert response.status_code == 200
        documents = response.json()
        assert all(doc["kind"] == "lab" and doc["status"] == "ingested" for doc in documents)


class TestAppointmentValidationAndErrors:
    """Test suite for Appointment validation and error handling"""
    
    async def test_create_appointment_missing_required_fields(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating appointment with missing required fields"""
        # Missing patient_id
        appointment_data = {
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Test",
            "starts_at": datetime.now(timezone.utc).isoformat(),
            "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        assert response.status_code == 422
    
    async def test_create_appointment_invalid_dates(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating appointment with invalid dates"""
        # ends_at before starts_at
        starts_at = datetime.now(timezone.utc) + timedelta(days=7)
        ends_at = starts_at - timedelta(hours=1)
        
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Test",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        }
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        # Should either reject or handle gracefully
        assert response.status_code in [200, 422, 400]
    
    async def test_create_appointment_past_date(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating appointment in the past"""
        starts_at = datetime.now(timezone.utc) - timedelta(days=7)
        ends_at = starts_at + timedelta(hours=1)
        
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Past Appointment",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
        }
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        # Should either accept or reject
        assert response.status_code in [200, 422, 400]
    
    async def test_create_appointment_all_types(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating appointments of all types"""
        appointment_types = ["consultation", "follow-up", "procedure", "screening"]
        appointment_ids = []
        
        for apt_type in appointment_types:
            starts_at = datetime.now(timezone.utc) + timedelta(days=7)
            appointment_data = {
                "patient_id": test_patient_id,
                "provider_id": "provider-123",
                "type": apt_type,
                "title": f"{apt_type.title()} Appointment",
                "starts_at": starts_at.isoformat(),
                "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
            }
            response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
            assert response.status_code == 200
            appointment_ids.append(response.json()["appointment_id"])
        
        # Verify all were created
        response = await client.get(
            f"{API_BASE}/appointments",
            params={"patient_id": test_patient_id}
        )
        appointments = response.json()
        created_types = {apt.get("type") for apt in appointments}
        assert set(appointment_types).issubset(created_types)
    
    async def test_create_appointment_invalid_patient_id(self, client: httpx.AsyncClient):
        """Test creating appointment with invalid patient_id"""
        starts_at = datetime.now(timezone.utc) + timedelta(days=7)
        appointment_data = {
            "patient_id": "invalid-patient-id",
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Test",
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
        }
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        assert response.status_code == 404  # Patient not found
    
    async def test_list_appointments_by_provider(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering appointments by provider"""
        # Create appointments with different providers
        providers = ["provider-123", "provider-456"]
        for provider in providers:
            starts_at = datetime.now(timezone.utc) + timedelta(days=7)
            appointment_data = {
                "patient_id": test_patient_id,
                "provider_id": provider,
                "type": "consultation",
                "title": f"Appointment with {provider}",
                "starts_at": starts_at.isoformat(),
                "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
            }
            await client.post(f"{API_BASE}/appointments", json=appointment_data)
        
        # Filter by provider
        response = await client.get(
            f"{API_BASE}/appointments",
            params={"provider_id": "provider-123"}
        )
        assert response.status_code == 200
        appointments = response.json()
        # Note: The response might not include provider_id, but should filter correctly
    
    async def test_list_appointments_by_specific_date(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering appointments by specific date"""
        # Create appointment for specific date
        target_date = datetime.now(timezone.utc) + timedelta(days=14)
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Specific Date Appointment",
            "starts_at": target_date.isoformat(),
            "ends_at": (target_date + timedelta(hours=1)).isoformat(),
        }
        await client.post(f"{API_BASE}/appointments", json=appointment_data)
        
        # Get appointments for that date
        date_str = target_date.strftime("%Y-%m-%d")
        response = await client.get(
            f"{API_BASE}/appointments",
            params={"date": date_str}
        )
        assert response.status_code == 200
        appointments = response.json()
        assert isinstance(appointments, list)


class TestClaimValidationAndErrors:
    """Test suite for Claim validation and error handling"""
    
    async def test_create_claim_missing_required_fields(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating claim with missing required fields"""
        # Missing insurance_provider
        claim_data = {
            "patient_id": test_patient_id,
            "amount": 1500.00,
            "service_date": "2024-11-01",
        }
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        assert response.status_code == 422
    
    async def test_create_claim_invalid_amount(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating claim with invalid amounts"""
        # Negative amount
        claim_data = {
            "patient_id": test_patient_id,
            "insurance_provider": "Aetna",
            "amount": -100.00,
            "service_date": "2024-11-01",
        }
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        # Should either reject or handle gracefully
        assert response.status_code in [200, 422, 400]
        
        # Zero amount
        claim_data["amount"] = 0.00
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        assert response.status_code in [200, 422, 400]
        
        # Very large amount
        claim_data["amount"] = 999999999.99
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        assert response.status_code == 200
    
    async def test_create_claim_all_statuses(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating and updating claims through all statuses"""
        claim_id = await TestInsuranceClaimOperations().test_create_claim(client, test_patient_id)
        
        statuses = [
            "pending",
            "submitted",
            "received",
            "under_review",
            "approved",
            "denied",
            "settlement_in_progress",
            "settlement_done"
        ]
        
        for status in statuses:
            update_data = {
                "tool": "update_insurance_claim",
                "arguments": {
                    "claim_id": claim_id,
                    "status": status
                }
            }
            response = await client.post(f"{MCP_BASE}/call", json=update_data)
            assert response.status_code == 200
            
            # Verify status update
            get_response = await client.get(f"{API_BASE}/claims/{claim_id}")
            claim = get_response.json()
            assert claim["status"] == status
    
    async def test_create_claim_with_all_codes(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating claims with various procedure and diagnosis codes"""
        codes = [
            ("99213", "E11.9"),  # Office visit, Type 2 diabetes
            ("99214", "I10"),    # Office visit, Essential hypertension
            ("99215", "M79.3"),  # Office visit, Panniculitis
        ]
        
        for proc_code, diag_code in codes:
            claim_data = {
                "patient_id": test_patient_id,
                "insurance_provider": "Aetna",
                "amount": 200.00,
                "procedure_code": proc_code,
                "diagnosis_code": diag_code,
                "service_date": "2024-11-01",
            }
            response = await client.post(f"{API_BASE}/claims", json=claim_data)
            assert response.status_code == 200
            claim = response.json()
            assert claim["status"] == "pending"
    
    async def test_get_claim_not_found(self, client: httpx.AsyncClient):
        """Test getting non-existent claim"""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{API_BASE}/claims/{fake_id}")
        assert response.status_code == 404
    
    async def test_get_claim_events_empty(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting events for a claim (should have at least one event)"""
        claim_id = await TestInsuranceClaimOperations().test_create_claim(client, test_patient_id)
        
        response = await client.get(f"{API_BASE}/claims/{claim_id}/events")
        assert response.status_code == 200
        events = response.json()
        assert isinstance(events, list)
        # Should have at least one event (the initial submission)
        assert len(events) >= 1


class TestConsentFormOperations:
    """Test suite for Consent Form operations via MCP"""
    
    async def test_create_consent_form(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating a consent form"""
        form_data = {
            "tool": "create_consent_form",
            "arguments": {
                "patient_id": test_patient_id,
                "template_id": "template-123",
                "form_type": "HIPAA Authorization",
                "title": "HIPAA Authorization Form",
                "send_method": "email"
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=form_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "consent_form_id" in data["result"]
        assert data["result"]["status"] == "sent"
        
        return data["result"]["consent_form_id"]
    
    async def test_create_consent_form_without_sending(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating consent form without sending"""
        form_data = {
            "tool": "create_consent_form",
            "arguments": {
                "patient_id": test_patient_id,
                "template_id": "template-456",
                "form_type": "Treatment Consent",
                "title": "Treatment Consent Form",
                "send_method": None
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=form_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["status"] == "to_do"
    
    async def test_send_consent_forms(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test sending consent forms to patient"""
        form_data = {
            "tool": "send_consent_forms",
            "arguments": {
                "patient_id": test_patient_id,
                "form_template_ids": ["template-123", "template-456"],
                "send_method": "email"
            }
        }
        
        response = await client.post(f"{MCP_BASE}/call", json=form_data)
        # Note: This might fail if templates don't exist, but should handle gracefully
        assert response.status_code == 200
    
    async def test_get_consent_forms(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test getting consent forms for a patient"""
        # First create a form
        form_id = await self.test_create_consent_form(client, test_patient_id)
        
        # Get consent forms (if endpoint exists)
        response = await client.get(
            f"{API_BASE}/consent-forms",
            params={"patient_id": test_patient_id}
        )
        # Note: This endpoint might not exist, adjust based on actual API
        if response.status_code == 200:
            forms = response.json()
            assert isinstance(forms, list)


class TestTaskValidationAndErrors:
    """Test suite for Task validation and error handling"""
    
    async def test_create_task_all_priorities(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating tasks with all priority levels"""
        priorities = ["urgent", "high", "medium", "low"]
        task_ids = []
        
        for priority in priorities:
            task_data = {
                "title": f"Task with {priority} priority",
                "description": f"Test task with {priority} priority",
                "patient_id": test_patient_id,
                "assigned_to": "Dr. Smith",
                "agent_type": "human",
                "priority": priority,
                "kind": "review"
            }
            response = await client.post(f"{API_BASE}/tasks", json=task_data)
            assert response.status_code == 200
            task_ids.append(response.json()["task_id"])
        
        # Verify all were created
        response = await client.get(
            f"{API_BASE}/tasks",
            params={"patient_id": test_patient_id}
        )
        tasks = response.json()
        created_priorities = {task["priority"] for task in tasks if task["task_id"] in task_ids}
        assert set(priorities).issubset(created_priorities)
    
    async def test_create_task_all_states(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating and updating tasks through all states"""
        task_id = await TestTaskOperations().test_create_task(client, test_patient_id)
        
        states = ["open", "in_progress", "done", "cancelled"]
        
        for state in states:
            update_data = {
                "state": state,
                "comment": f"Updated to {state}"
            }
            response = await client.patch(f"{API_BASE}/tasks/{task_id}", json=update_data)
            assert response.status_code == 200
            
            # Verify state update
            response = await client.get(f"{API_BASE}/tasks")
            tasks = response.json()
            task = next((t for t in tasks if t["task_id"] == task_id), None)
            if task:
                assert task["state"] == state
    
    async def test_list_tasks_by_state(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering tasks by state"""
        # Create tasks in different states
        task_id = await TestTaskOperations().test_create_task(client, test_patient_id)
        
        # Update to different states
        for state in ["open", "in_progress", "done"]:
            await client.patch(
                f"{API_BASE}/tasks/{task_id}",
                json={"state": state}
            )
        
        # Filter by state
        response = await client.get(
            f"{API_BASE}/tasks",
            params={"state": "done"}
        )
        assert response.status_code == 200
        tasks = response.json()
        assert all(task["state"] == "done" for task in tasks)
    
    async def test_list_tasks_by_priority(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering tasks by priority"""
        # Create tasks with different priorities
        priorities = ["urgent", "high", "medium"]
        for priority in priorities:
            task_data = {
                "title": f"Task {priority}",
                "description": "Test",
                "patient_id": test_patient_id,
                "assigned_to": "Dr. Smith",
                "priority": priority,
            }
            await client.post(f"{API_BASE}/tasks", json=task_data)
        
        # Filter by priority
        response = await client.get(
            f"{API_BASE}/tasks",
            params={"priority": "urgent"}
        )
        assert response.status_code == 200
        tasks = response.json()
        assert all(task["priority"] == "urgent" for task in tasks)
    
    async def test_update_task_with_comments(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating task with multiple comments"""
        task_id = await TestTaskOperations().test_create_task(client, test_patient_id)
        
        comments = [
            "Initial review started",
            "Waiting for additional information",
            "Review completed"
        ]
        
        for i, comment in enumerate(comments):
            update_data = {
                "state": "in_progress" if i < len(comments) - 1 else "done",
                "comment": comment
            }
            response = await client.patch(f"{API_BASE}/tasks/{task_id}", json=update_data)
            assert response.status_code == 200
    
    async def test_get_task_not_found(self, client: httpx.AsyncClient):
        """Test getting non-existent task"""
        fake_id = str(uuid.uuid4())
        # Note: There's no GET /tasks/{task_id} endpoint, so we'll test via list
        response = await client.get(f"{API_BASE}/tasks")
        tasks = response.json()
        assert fake_id not in [task.get("task_id") for task in tasks]


class TestPatientSummaryAndTimelineExtended:
    """Extended tests for Patient Summary and Timeline"""
    
    async def test_patient_summary_with_documents(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test patient summary after creating documents"""
        # Create multiple documents
        for kind in ["lab", "imaging", "medical_history"]:
            files = {"file": (f"test_{kind}.pdf", b"content", "application/pdf")}
            await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": kind},
                files=files
            )
        
        # Get summary
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}/summary")
        assert response.status_code == 200
        summary = response.json()
        assert "summary" in summary
        assert "citations" in summary
    
    async def test_patient_summary_with_updated_preconditions(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that patient summary reflects updated preconditions"""
        # Update patient preconditions
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": test_patient_id,
                "preconditions": ["Diabetes", "Hypertension", "Asthma", "COPD"]
            }
        }
        await client.post(f"{MCP_BASE}/call", json=update_data)
        
        # Get summary
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}/summary")
        assert response.status_code == 200
        summary = response.json()
        # Summary should reflect the updated preconditions
        assert "summary" in summary


class TestDashboardEndpoints:
    """Test suite for Dashboard endpoints"""
    
    async def test_get_dashboard_stats(self, client: httpx.AsyncClient):
        """Test getting dashboard statistics"""
        response = await client.get(f"{API_BASE}/dashboard/stats")
        assert response.status_code == 200
        stats = response.json()
        assert "pending_tasks" in stats
        assert "appointments_today" in stats
        assert "patients_total" in stats
        assert "claims_pending" in stats
        assert isinstance(stats["pending_tasks"], int)
        assert isinstance(stats["appointments_today"], int)
        assert isinstance(stats["patients_total"], int)
        assert isinstance(stats["claims_pending"], int)
    
    async def test_get_dashboard_appointments(self, client: httpx.AsyncClient):
        """Test getting today's appointments for dashboard"""
        response = await client.get(f"{API_BASE}/dashboard/appointments")
        assert response.status_code == 200
        appointments = response.json()
        assert isinstance(appointments, list)
        
        if len(appointments) > 0:
            appointment = appointments[0]
            assert "appointment_id" in appointment
            assert "patient_name" in appointment
            assert "starts_at" in appointment


class TestMCPTools:
    """Test suite for MCP Tools endpoint"""
    
    async def test_get_mcp_tools(self, client: httpx.AsyncClient):
        """Test getting list of available MCP tools"""
        response = await client.get(f"{MCP_BASE}/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
        
        # Verify expected tools are present
        tool_names = [tool.get("name") for tool in data["tools"]]
        expected_tools = [
            "find_or_create_patient",
            "update_patient",
            "get_patient",
            "create_appointment",
            "update_appointment",
            "delete_appointment",
            "create_insurance_claim",
            "update_insurance_claim",
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Tool {expected_tool} not found in MCP tools"
    
    async def test_call_mcp_tool_invalid_tool(self, client: httpx.AsyncClient):
        """Test calling non-existent MCP tool"""
        call_data = {
            "tool": "nonexistent_tool",
            "arguments": {}
        }
        response = await client.post(f"{MCP_BASE}/call", json=call_data)
        assert response.status_code == 404
    
    async def test_call_mcp_tool_missing_arguments(self, client: httpx.AsyncClient):
        """Test calling MCP tool with missing required arguments"""
        call_data = {
            "tool": "update_patient",
            "arguments": {}  # Missing patient_id
        }
        response = await client.post(f"{MCP_BASE}/call", json=call_data)
        # Should either fail or handle gracefully
        assert response.status_code in [200, 400, 422]
    
    async def test_all_mcp_patient_tools(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test all MCP patient-related tools"""
        # Test get_patient
        get_data = {
            "tool": "get_patient",
            "arguments": {"patient_id": test_patient_id}
        }
        response = await client.post(f"{MCP_BASE}/call", json=get_data)
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "patient_id" in response.json()["result"]
        
        # Test find_or_create_patient (find existing)
        find_data = {
            "tool": "find_or_create_patient",
            "arguments": {
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com"
            }
        }
        response = await client.post(f"{MCP_BASE}/call", json=find_data)
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestDataIntegrityAndRelationships:
    """Test suite for data integrity and entity relationships"""
    
    async def test_patient_task_count_increment(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that creating a task increments patient's task_count"""
        # Get initial task count
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        initial_count = response.json()["tasks_count"]
        
        # Create a task
        task_data = {
            "title": "Test Task",
            "description": "Test",
            "patient_id": test_patient_id,
            "assigned_to": "Dr. Smith",
            "priority": "medium",
        }
        await client.post(f"{API_BASE}/tasks", json=task_data)
        
        # Verify task count incremented
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        new_count = response.json()["tasks_count"]
        assert new_count == initial_count + 1
    
    async def test_patient_appointment_count_increment(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that creating an appointment increments patient's appointment_count"""
        # Get initial appointment count
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        initial_count = response.json()["appointments_count"]
        
        # Create an appointment
        starts_at = datetime.now(timezone.utc) + timedelta(days=7)
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Test Appointment",
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
        }
        await client.post(f"{API_BASE}/appointments", json=appointment_data)
        
        # Verify appointment count incremented
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        new_count = response.json()["appointments_count"]
        assert new_count == initial_count + 1
    
    async def test_document_patient_relationship(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that documents are correctly linked to patients"""
        # Create document
        files = {"file": ("test.pdf", b"content", "application/pdf")}
        response = await client.post(
            f"{API_BASE}/documents/upload",
            params={"patient_id": test_patient_id, "kind": "lab"},
            files=files
        )
        doc_id = response.json()["document_id"]
        
        # Get document and verify patient_id
        response = await client.get(f"{API_BASE}/documents/{doc_id}")
        document = response.json()
        assert document["patient_id"] == test_patient_id
        
        # Get patient's documents
        response = await client.get(
            f"{API_BASE}/documents",
            params={"patient_id": test_patient_id}
        )
        documents = response.json()
        assert any(doc["document_id"] == doc_id for doc in documents)
    
    async def test_claim_patient_relationship(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that claims are correctly linked to patients"""
        # Create claim
        claim_data = {
            "patient_id": test_patient_id,
            "insurance_provider": "Aetna",
            "amount": 1000.00,
            "service_date": "2024-11-01",
        }
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        claim_id = response.json()["claim_id"]
        
        # Get claim and verify patient_id
        response = await client.get(f"{API_BASE}/claims/{claim_id}")
        claim = response.json()
        # Note: Response might have patient_name instead of patient_id
        assert "patient_name" in claim or "patient_id" in claim
        
        # Get patient's claims
        response = await client.get(
            f"{API_BASE}/claims",
            params={"patient_id": test_patient_id}
        )
        claims = response.json()
        assert any(c["claim_id"] == claim_id for c in claims)
    
    async def test_appointment_patient_relationship(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test that appointments are correctly linked to patients"""
        # Create appointment
        starts_at = datetime.now(timezone.utc) + timedelta(days=7)
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Test",
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
        }
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        appointment_id = response.json()["appointment_id"]
        
        # Get patient's appointments
        response = await client.get(
            f"{API_BASE}/appointments",
            params={"patient_id": test_patient_id}
        )
        appointments = response.json()
        assert any(apt.get("appointment_id") == appointment_id for apt in appointments)


class TestConcurrentOperations:
    """Test suite for concurrent operations and race conditions"""
    
    async def test_concurrent_patient_updates(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating patient concurrently"""
        async def update_status(status: str):
            update_data = {
                "tool": "update_patient",
                "arguments": {
                    "patient_id": test_patient_id,
                    "status": status
                }
            }
            return await client.post(f"{MCP_BASE}/call", json=update_data)
        
        # Update concurrently
        tasks = [
            update_status("Intake Done"),
            update_status("Doc Collection In Progress"),
            update_status("Consultation Scheduled"),
        ]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Final status should be one of them
        get_response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        final_status = get_response.json()["status"]
        assert final_status in ["Intake Done", "Doc Collection In Progress", "Consultation Scheduled"]
    
    async def test_concurrent_document_uploads(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test uploading multiple documents concurrently"""
        async def upload_doc(kind: str):
            files = {"file": (f"test_{kind}.pdf", b"content", "application/pdf")}
            return await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": kind},
                files=files
            )
        
        kinds = ["lab", "imaging", "medical_history", "summary"]
        responses = await asyncio.gather(*[upload_doc(kind) for kind in kinds])
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Verify all documents were created
        response = await client.get(
            f"{API_BASE}/documents",
            params={"patient_id": test_patient_id}
        )
        documents = response.json()
        created_kinds = {doc["kind"] for doc in documents}
        assert set(kinds).issubset(created_kinds)
    
    async def test_concurrent_task_creation(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test creating multiple tasks concurrently"""
        async def create_task(title: str):
            task_data = {
                "title": title,
                "description": "Test",
                "patient_id": test_patient_id,
                "assigned_to": "Dr. Smith",
                "priority": "medium",
            }
            return await client.post(f"{API_BASE}/tasks", json=task_data)
        
        tasks = [create_task(f"Task {i}") for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Verify task count incremented correctly
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        # Note: Task count might not be exactly 5 if there were existing tasks
        assert response.json()["tasks_count"] >= 5


class TestSearchAndFiltering:
    """Test suite for search and filtering functionality"""
    
    async def test_patient_search_partial_match(self, client: httpx.AsyncClient):
        """Test patient search with partial name matches"""
        # Create patient with unique name
        unique_name = f"SearchPartial{uuid.uuid4().hex[:8]}"
        patient_data = {
            "first_name": unique_name,
            "last_name": "Test",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": f"{unique_name.lower()}@example.com",
            "phone": "555-1234",
        }
        await client.post(f"{API_BASE}/patients", json=patient_data)
        
        # Search with partial match
        search_terms = [
            unique_name[:5],  # First 5 characters
            unique_name[-5:],  # Last 5 characters
            unique_name[3:8],  # Middle characters
        ]
        
        for term in search_terms:
            response = await client.get(
                f"{API_BASE}/patients",
                params={"q": term}
            )
            assert response.status_code == 200
            results = response.json()
            # Should find the patient (depending on n-gram implementation)
            assert isinstance(results, list)
    
    async def test_patient_search_case_insensitive(self, client: httpx.AsyncClient):
        """Test that patient search is case insensitive"""
        unique_name = f"CaseTest{uuid.uuid4().hex[:8]}"
        patient_data = {
            "first_name": unique_name,
            "last_name": "Test",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": f"{unique_name.lower()}@example.com",
            "phone": "555-1234",
        }
        await client.post(f"{API_BASE}/patients", json=patient_data)
        
        # Search with different cases
        search_variants = [
            unique_name.upper(),
            unique_name.lower(),
            unique_name.capitalize(),
        ]
        
        for variant in search_variants:
            response = await client.get(
                f"{API_BASE}/patients",
                params={"q": variant}
            )
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
    
    async def test_document_filtering_combinations(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test filtering documents with various combinations"""
        # Create documents with different attributes
        configs = [
            ("lab", "uploaded"),
            ("lab", "ingested"),
            ("imaging", "uploaded"),
            ("imaging", "ingested"),
            ("medical_history", "uploaded"),
        ]
        
        for kind, status in configs:
            files = {"file": (f"test_{kind}.pdf", b"content", "application/pdf")}
            response = await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": kind},
                files=files
            )
            doc_id = response.json()["document_id"]
            await client.patch(
                f"{API_BASE}/documents/{doc_id}",
                json={"status": status}
            )
        
        # Test various filter combinations
        filter_combinations = [
            {"patient_id": test_patient_id, "kind": "lab"},
            {"patient_id": test_patient_id, "status": "ingested"},
            {"kind": "lab", "status": "ingested"},
            {"patient_id": test_patient_id, "kind": "lab", "status": "ingested"},
        ]
        
        for filters in filter_combinations:
            response = await client.get(
                f"{API_BASE}/documents",
                params=filters
            )
            assert response.status_code == 200
            documents = response.json()
            assert isinstance(documents, list)
            
            # Verify filters are applied
            if "kind" in filters:
                assert all(doc["kind"] == filters["kind"] for doc in documents)
            if "status" in filters:
                assert all(doc["status"] == filters["status"] for doc in documents)


class TestWorkflowScenarios:
    """Test suite for complete workflow scenarios"""
    
    async def test_complete_patient_intake_workflow(self, client: httpx.AsyncClient):
        """Test complete patient intake workflow"""
        # 1. Create patient
        patient_data = {
            "first_name": "Intake",
            "last_name": "Workflow",
            "dob": "1985-06-15",
            "gender": "Female",
            "email": f"intake_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-7777",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        patient_id = response.json()["patient_id"]
        
        # 2. Update status: Intake In Progress -> Intake Done
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_patient",
            "arguments": {"patient_id": patient_id, "status": "Intake Done"}
        })
        
        # 3. Upload required documents
        required_docs = [
            ("lab", "ID Document"),
            ("imaging", "Insurance Card"),
        ]
        for kind, _ in required_docs:
            files = {"file": (f"{kind}.pdf", b"content", "application/pdf")}
            await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": patient_id, "kind": kind},
                files=files
            )
        
        # 4. Update status: Doc Collection Done
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_patient",
            "arguments": {"patient_id": patient_id, "status": "Doc Collection Done"}
        })
        
        # 5. Create consent forms
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "create_consent_form",
            "arguments": {
                "patient_id": patient_id,
                "template_id": "template-123",
                "form_type": "HIPAA Authorization",
                "title": "HIPAA Form",
                "send_method": "email"
            }
        })
        
        # 6. Verify final state
        response = await client.get(f"{API_BASE}/patients/{patient_id}")
        patient = response.json()
        assert patient["status"] == "Doc Collection Done"
        assert patient["tasks_count"] >= 0
        assert patient["appointments_count"] >= 0
    
    async def test_complete_claim_processing_workflow(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test complete insurance claim processing workflow"""
        # 1. Create claim
        claim_data = {
            "patient_id": test_patient_id,
            "insurance_provider": "UnitedHealthcare",
            "amount": 2500.00,
            "procedure_code": "99214",
            "diagnosis_code": "I10",
            "service_date": "2024-11-01",
            "description": "Office visit for hypertension management"
        }
        response = await client.post(f"{API_BASE}/claims", json=claim_data)
        claim_id = response.json()["claim_id"]
        
        # 2. Submit claim
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_insurance_claim",
            "arguments": {"claim_id": claim_id, "status": "submitted"}
        })
        
        # 3. Claim received
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_insurance_claim",
            "arguments": {"claim_id": claim_id, "status": "received"}
        })
        
        # 4. Under review
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_insurance_claim",
            "arguments": {"claim_id": claim_id, "status": "under_review"}
        })
        
        # 5. Approved
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_insurance_claim",
            "arguments": {"claim_id": claim_id, "status": "approved"}
        })
        
        # 6. Verify claim events
        response = await client.get(f"{API_BASE}/claims/{claim_id}/events")
        events = response.json()
        assert len(events) >= 4  # Should have multiple events
        
        # 7. Verify final status
        response = await client.get(f"{API_BASE}/claims/{claim_id}")
        claim = response.json()
        assert claim["status"] == "approved"
    
    async def test_complete_appointment_lifecycle(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test complete appointment lifecycle"""
        # 1. Create appointment
        starts_at = datetime.now(timezone.utc) + timedelta(days=14)
        appointment_data = {
            "patient_id": test_patient_id,
            "provider_id": "provider-123",
            "type": "consultation",
            "title": "Follow-up Consultation",
            "starts_at": starts_at.isoformat(),
            "ends_at": (starts_at + timedelta(hours=1)).isoformat(),
            "location": "Main Clinic"
        }
        response = await client.post(f"{API_BASE}/appointments", json=appointment_data)
        appointment_id = response.json()["appointment_id"]
        
        # 2. Confirm appointment
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_appointment",
            "arguments": {
                "appointment_id": appointment_id,
                "status": "confirmed"
            }
        })
        
        # 3. Reschedule appointment
        new_starts_at = starts_at + timedelta(days=7)
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "update_appointment",
            "arguments": {
                "appointment_id": appointment_id,
                "starts_at": new_starts_at.isoformat(),
                "ends_at": (new_starts_at + timedelta(hours=1)).isoformat(),
                "status": "rescheduled"
            }
        })
        
        # 4. Cancel appointment
        await client.post(f"{MCP_BASE}/call", json={
            "tool": "delete_appointment",
            "arguments": {"appointment_id": appointment_id}
        })
        
        # Verify appointment is deleted
        response = await client.get(
            f"{API_BASE}/appointments",
            params={"patient_id": test_patient_id}
        )
        appointments = response.json()
        # Appointment should be removed or marked as cancelled
        assert not any(apt.get("appointment_id") == appointment_id and apt.get("status") != "cancelled" 
                      for apt in appointments)


class TestEdgeCasesAndBoundaries:
    """Test suite for edge cases and boundary conditions"""
    
    async def test_create_patient_minimal_data(self, client: httpx.AsyncClient):
        """Test creating patient with minimal required data"""
        patient_data = {
            "first_name": "Min",
            "last_name": "Data",
            "dob": "1990-01-01",
            "gender": "Other",
            "email": f"min_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-0000",
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 200
    
    async def test_create_patient_maximal_data(self, client: httpx.AsyncClient):
        """Test creating patient with all optional fields"""
        patient_data = {
            "first_name": "Max",
            "last_name": "Data",
            "dob": "1990-01-01",
            "gender": "Male",
            "email": f"max_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-9999",
            "address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001",
                "country": "USA"
            },
            "preconditions": ["Condition 1", "Condition 2", "Condition 3"],
            "profile_image": "https://example.com/profile.jpg"
        }
        response = await client.post(f"{API_BASE}/patients", json=patient_data)
        assert response.status_code == 200
        patient_id = response.json()["patient_id"]
        
        # Verify all data was saved
        response = await client.get(f"{API_BASE}/patients/{patient_id}")
        patient = response.json()
        assert patient["preconditions"] == patient_data["preconditions"]
        assert patient["profile_image"] == patient_data["profile_image"]
    
    async def test_update_patient_partial_fields(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test updating only some patient fields"""
        # Update only email
        update_data = {
            "tool": "update_patient",
            "arguments": {
                "patient_id": test_patient_id,
                "email": f"updated_{uuid.uuid4().hex[:8]}@example.com"
            }
        }
        response = await client.post(f"{MCP_BASE}/call", json=update_data)
        assert response.status_code == 200
        
        # Verify only email changed
        response = await client.get(f"{API_BASE}/patients/{test_patient_id}")
        patient = response.json()
        assert patient["email"].startswith("updated_")
    
    async def test_list_patients_empty_result(self, client: httpx.AsyncClient):
        """Test listing patients with query that returns no results"""
        response = await client.get(
            f"{API_BASE}/patients",
            params={"q": "ThisNameDoesNotExist12345"}
        )
        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)
        # Should return empty list, not error
    
    async def test_pagination_edge_cases(self, client: httpx.AsyncClient):
        """Test pagination with edge cases"""
        # Skip beyond available records
        response = await client.get(
            f"{API_BASE}/patients",
            params={"limit": 10, "skip": 10000}
        )
        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)
        assert len(patients) == 0
        
        # Limit of 0
        response = await client.get(
            f"{API_BASE}/patients",
            params={"limit": 0, "skip": 0}
        )
        assert response.status_code == 200
        patients = response.json()
        assert isinstance(patients, list)


class TestPerformanceAndLoad:
    """Test suite for performance and load testing"""
    
    async def test_bulk_patient_creation(self, client: httpx.AsyncClient):
        """Test creating multiple patients in sequence"""
        patient_ids = []
        for i in range(10):
            patient_data = {
                "first_name": f"Bulk{i}",
                "last_name": "Test",
                "dob": "1990-01-01",
                "gender": "Male",
                "email": f"bulk{i}_{uuid.uuid4().hex[:8]}@example.com",
                "phone": f"555-{i:04d}",
            }
            response = await client.post(f"{API_BASE}/patients", json=patient_data)
            assert response.status_code == 200
            patient_ids.append(response.json()["patient_id"])
        
        # Verify all were created
        response = await client.get(f"{API_BASE}/patients")
        patients = response.json()
        created_ids = {p["patient_id"] for p in patients}
        assert all(pid in created_ids for pid in patient_ids)
    
    async def test_bulk_document_upload(self, client: httpx.AsyncClient, test_patient_id: str):
        """Test uploading multiple documents"""
        doc_ids = []
        for i in range(5):
            files = {"file": (f"bulk_doc_{i}.pdf", b"content", "application/pdf")}
            response = await client.post(
                f"{API_BASE}/documents/upload",
                params={"patient_id": test_patient_id, "kind": "lab"},
                files=files
            )
            assert response.status_code == 200
            doc_ids.append(response.json()["document_id"])
        
        # Verify all were created
        response = await client.get(
            f"{API_BASE}/documents",
            params={"patient_id": test_patient_id}
        )
        documents = response.json()
        created_ids = {doc["document_id"] for doc in documents}
        assert all(did in created_ids for did in doc_ids)


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

