"""
End-to-End Test Script for BacklineMD
Tests all CRUD operations and workflows
"""
import asyncio
import requests
import json
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8001/api"

def test_create_patient():
    """Test 1: Create a patient"""
    print("\n=== Test 1: Create Patient ===")
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "dob": "1985-05-15",
        "gender": "Male",
        "email": "john.doe@test.com",
        "phone": "+1-555-1234",
        "preconditions": ["Hypertension", "Diabetes"]
    }
    response = requests.post(f"{BASE_URL}/patients", json=data)
    assert response.status_code == 200, f"Failed to create patient: {response.text}"
    patient_id = response.json()["patient_id"]
    print(f"✓ Patient created: {patient_id}")
    return patient_id

def test_update_patient(patient_id):
    """Test 2: Update patient information"""
    print("\n=== Test 2: Update Patient ===")
    data = {
        "first_name": "John Updated",
        "age": 40,
        "status": "Intake Done"
    }
    response = requests.patch(f"{BASE_URL}/patients/{patient_id}", json=data)
    assert response.status_code == 200, f"Failed to update patient: {response.text}"
    print("✓ Patient updated successfully")
    return patient_id

def test_change_patient_status(patient_id):
    """Test 3: Change patient status"""
    print("\n=== Test 3: Change Patient Status ===")
    data = {"status": "Doc Collection In Progress"}
    response = requests.patch(f"{BASE_URL}/patients/{patient_id}", json=data)
    assert response.status_code == 200, f"Failed to change status: {response.text}"
    print("✓ Patient status changed")
    return patient_id

def test_create_ai_task_onboarding(patient_id):
    """Test 4: Create AI task for onboarding email"""
    print("\n=== Test 4: Create AI Task for Onboarding Email ===")
    data = {
        "title": "Send Onboarding Email - Request Documents",
        "description": "Send onboarding email to patient requesting medical history, insurance card, and lab results",
        "patient_id": patient_id,
        "assigned_to": "AI - Onboarding Agent",
        "agent_type": "ai_agent",
        "priority": "high",
        "kind": "onboarding_email"
    }
    response = requests.post(f"{BASE_URL}/tasks", json=data)
    assert response.status_code == 200, f"Failed to create task: {response.text}"
    task_id = response.json()["task_id"]
    print(f"✓ AI task created: {task_id}")
    return task_id

def test_create_document_extraction_task(patient_id):
    """Test 5: Create task for document extraction"""
    print("\n=== Test 5: Create Document Extraction Task ===")
    data = {
        "title": "Extract Documents from Email",
        "description": "Patient sent documents via email. Extract and process medical history, insurance card, and lab results.",
        "patient_id": patient_id,
        "assigned_to": "AI - Document Extractor",
        "agent_type": "ai_agent",
        "priority": "high",
        "kind": "document_extraction"
    }
    response = requests.post(f"{BASE_URL}/tasks", json=data)
    assert response.status_code == 200, f"Failed to create task: {response.text}"
    task_id = response.json()["task_id"]
    print(f"✓ Document extraction task created: {task_id}")
    return task_id

def test_get_patient_details(patient_id):
    """Test 6: Get patient details with all tabs"""
    print("\n=== Test 6: Get Patient Details ===")
    
    # Get patient
    response = requests.get(f"{BASE_URL}/patients/{patient_id}")
    assert response.status_code == 200, f"Failed to get patient: {response.text}"
    patient = response.json()
    print(f"✓ Patient retrieved: {patient['first_name']} {patient['last_name']}")
    
    # Get summary
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/summary")
    assert response.status_code == 200, f"Failed to get summary: {response.text}"
    print("✓ Patient summary retrieved")
    
    # Get tasks
    response = requests.get(f"{BASE_URL}/tasks?patient_id={patient_id}")
    assert response.status_code == 200, f"Failed to get tasks: {response.text}"
    tasks = response.json()
    print(f"✓ Tasks retrieved: {len(tasks)} tasks")
    
    # Get appointments
    response = requests.get(f"{BASE_URL}/appointments?patient_id={patient_id}")
    assert response.status_code == 200, f"Failed to get appointments: {response.text}"
    appointments = response.json()
    print(f"✓ Appointments retrieved: {len(appointments)} appointments")
    
    # Get documents
    response = requests.get(f"{BASE_URL}/documents?patient_id={patient_id}")
    assert response.status_code == 200, f"Failed to get documents: {response.text}"
    documents = response.json()
    print(f"✓ Documents retrieved: {len(documents)} documents")
    
    # Get notes
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/notes")
    assert response.status_code == 200, f"Failed to get notes: {response.text}"
    notes = response.json()
    print(f"✓ Notes retrieved: {len(notes)} notes")
    
    # Get activities
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/activities")
    assert response.status_code == 200, f"Failed to get activities: {response.text}"
    activities = response.json()
    print(f"✓ Activities retrieved: {len(activities)} activities")
    
    # Get documents summary
    response = requests.get(f"{BASE_URL}/patients/{patient_id}/documents/summary")
    assert response.status_code == 200, f"Failed to get documents summary: {response.text}"
    print("✓ Documents summary retrieved")
    
    return patient_id

def test_create_note(patient_id):
    """Test 7: Create note for patient"""
    print("\n=== Test 7: Create Note ===")
    data = {
        "content": "Patient called to confirm appointment. Discussed treatment options.",
        "author": "Dr. James O'Brien"
    }
    response = requests.post(f"{BASE_URL}/patients/{patient_id}/notes", json=data)
    assert response.status_code == 200, f"Failed to create note: {response.text}"
    print("✓ Note created successfully")
    return patient_id

def test_list_all_patients():
    """Test 8: List all patients"""
    print("\n=== Test 8: List All Patients ===")
    response = requests.get(f"{BASE_URL}/patients")
    assert response.status_code == 200, f"Failed to list patients: {response.text}"
    patients = response.json()
    print(f"✓ Retrieved {len(patients)} patients")
    return len(patients)

def test_list_all_claims():
    """Test 9: List all claims"""
    print("\n=== Test 9: List All Claims ===")
    response = requests.get(f"{BASE_URL}/claims")
    assert response.status_code == 200, f"Failed to list claims: {response.text}"
    claims = response.json()
    print(f"✓ Retrieved {len(claims)} claims")
    return len(claims)

def test_create_claim(patient_id):
    """Test 10: Create a claim"""
    print("\n=== Test 10: Create Claim ===")
    data = {
        "patient_id": patient_id,
        "insurance_provider": "Aetna",
        "amount": 1500.00,
        "procedure_code": "99213",
        "diagnosis_code": "Z00.00",
        "service_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": "Routine checkup and consultation"
    }
    response = requests.post(f"{BASE_URL}/claims", json=data)
    assert response.status_code == 200, f"Failed to create claim: {response.text}"
    claim_id = response.json()["claim_id"]
    print(f"✓ Claim created: {claim_id}")
    return claim_id

def test_update_task(task_id):
    """Test 11: Update task (accept/reject)"""
    print("\n=== Test 11: Update Task (Accept) ===")
    data = {"state": "done", "comment": "Task completed successfully"}
    response = requests.patch(f"{BASE_URL}/tasks/{task_id}", json=data)
    assert response.status_code == 200, f"Failed to update task: {response.text}"
    print("✓ Task updated (accepted)")
    return task_id

def test_regenerate_summary(patient_id):
    """Test 12: Regenerate patient summary"""
    print("\n=== Test 12: Regenerate Summary ===")
    response = requests.post(f"{BASE_URL}/patients/{patient_id}/summary/regenerate")
    if response.status_code == 200:
        print("✓ Summary regenerated successfully")
    else:
        print(f"⚠ Summary regeneration failed (may need OpenAI key): {response.text}")
    return patient_id

def run_all_tests():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("BACKLINEMD END-TO-END TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Create patient
        patient_id = test_create_patient()
        
        # Test 2: Update patient
        test_update_patient(patient_id)
        
        # Test 3: Change status
        test_change_patient_status(patient_id)
        
        # Test 4: Create AI onboarding task
        task_id1 = test_create_ai_task_onboarding(patient_id)
        
        # Test 5: Create document extraction task
        task_id2 = test_create_document_extraction_task(patient_id)
        
        # Test 6: Get patient details (all tabs)
        test_get_patient_details(patient_id)
        
        # Test 7: Create note
        test_create_note(patient_id)
        
        # Test 8: List all patients
        test_list_all_patients()
        
        # Test 9: List all claims
        test_list_all_claims()
        
        # Test 10: Create claim
        test_create_claim(patient_id)
        
        # Test 11: Update task
        test_update_task(task_id1)
        
        # Test 12: Regenerate summary
        test_regenerate_summary(patient_id)
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_all_tests()

