#!/usr/bin/env python3
"""
Backend API Test Suite for BacklineMD
Tests all CRUD operations systematically
"""

import requests
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import time

# Configuration
BACKEND_URL = "https://backmd-suite.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BacklineMDTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = {}
        self.created_resources = {
            'patients': [],
            'documents': [],
            'tasks': [],
            'appointments': [],
            'claims': []
        }

    def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.test_results[test_name] = {
            'success': success,
            'details': details,
            'response_data': response_data,
            'timestamp': datetime.now().isoformat()
        }
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")

    def test_patient_crud(self):
        """Test all Patient CRUD operations"""
        print("\n=== TESTING PATIENT CRUD OPERATIONS ===")
        
        # Test 1: Create Patient
        try:
            patient_data = {
                "first_name": "John",
                "last_name": "Doe",
                "dob": "1990-01-15",
                "gender": "male",
                "email": f"john.doe.{uuid.uuid4().hex[:8]}@example.com",
                "phone": "555-1234",
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001"
                },
                "preconditions": ["Hypertension", "Diabetes"]
            }
            
            response = self.session.post(f"{API_BASE}/patients", json=patient_data)
            if response.status_code == 200:
                data = response.json()
                patient_id = data.get("patient_id")
                if patient_id:
                    self.created_resources['patients'].append(patient_id)
                    self.log_result("Create Patient", True, f"Created patient with ID: {patient_id}", data)
                else:
                    self.log_result("Create Patient", False, "No patient_id in response", data)
            else:
                self.log_result("Create Patient", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Create Patient", False, f"Exception: {str(e)}")

        # Test 2: List Patients
        try:
            response = self.session.get(f"{API_BASE}/patients")
            if response.status_code == 200:
                patients = response.json()
                if isinstance(patients, list):
                    self.log_result("List Patients", True, f"Retrieved {len(patients)} patients")
                else:
                    self.log_result("List Patients", False, "Response is not a list", patients)
            else:
                self.log_result("List Patients", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("List Patients", False, f"Exception: {str(e)}")

        # Test 3: Get Specific Patient
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                response = self.session.get(f"{API_BASE}/patients/{patient_id}")
                if response.status_code == 200:
                    patient = response.json()
                    if patient.get("patient_id") == patient_id:
                        self.log_result("Get Patient by ID", True, f"Retrieved patient: {patient.get('first_name')} {patient.get('last_name')}")
                    else:
                        self.log_result("Get Patient by ID", False, "Patient ID mismatch", patient)
                else:
                    self.log_result("Get Patient by ID", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Get Patient by ID", False, f"Exception: {str(e)}")

        # Test 4: Search Patients
        try:
            response = self.session.get(f"{API_BASE}/patients", params={"q": "John"})
            if response.status_code == 200:
                patients = response.json()
                self.log_result("Search Patients", True, f"Search returned {len(patients)} results")
            else:
                self.log_result("Search Patients", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Search Patients", False, f"Exception: {str(e)}")

        # Test 5: Get Patient Summary
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                response = self.session.get(f"{API_BASE}/patients/{patient_id}/summary")
                if response.status_code == 200:
                    summary = response.json()
                    if "summary" in summary:
                        self.log_result("Get Patient Summary", True, "Summary generated successfully")
                    else:
                        self.log_result("Get Patient Summary", False, "No summary field in response", summary)
                else:
                    self.log_result("Get Patient Summary", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Get Patient Summary", False, f"Exception: {str(e)}")

    def test_task_crud(self):
        """Test all Task CRUD operations"""
        print("\n=== TESTING TASK CRUD OPERATIONS ===")
        
        # Test 1: Create Task
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                task_data = {
                    "title": "Review Lab Results",
                    "description": "Review and verify recent lab results for patient",
                    "patient_id": patient_id,
                    "assigned_to": "Dr. James O'Brien",
                    "agent_type": "human",
                    "priority": "high",
                    "kind": "review"
                }
                
                response = self.session.post(f"{API_BASE}/tasks", json=task_data)
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("task_id")
                    if task_id:
                        self.created_resources['tasks'].append(task_id)
                        self.log_result("Create Task", True, f"Created task with ID: {task_id}", data)
                    else:
                        self.log_result("Create Task", False, "No task_id in response", data)
                else:
                    self.log_result("Create Task", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Create Task", False, f"Exception: {str(e)}")
        else:
            self.log_result("Create Task", False, "No patients available for task creation")

        # Test 2: List Tasks
        try:
            response = self.session.get(f"{API_BASE}/tasks")
            if response.status_code == 200:
                tasks = response.json()
                if isinstance(tasks, list):
                    self.log_result("List Tasks", True, f"Retrieved {len(tasks)} tasks")
                else:
                    self.log_result("List Tasks", False, "Response is not a list", tasks)
            else:
                self.log_result("List Tasks", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("List Tasks", False, f"Exception: {str(e)}")

        # Test 3: Update Task Status
        if self.created_resources['tasks']:
            try:
                task_id = self.created_resources['tasks'][0]
                update_data = {
                    "state": "in_progress",
                    "comment": "Started reviewing lab results"
                }
                
                response = self.session.patch(f"{API_BASE}/tasks/{task_id}", json=update_data)
                if response.status_code == 200:
                    self.log_result("Update Task Status", True, "Task status updated successfully")
                else:
                    self.log_result("Update Task Status", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Update Task Status", False, f"Exception: {str(e)}")

        # Test 4: Filter Tasks by Patient
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                response = self.session.get(f"{API_BASE}/tasks", params={"patient_id": patient_id})
                if response.status_code == 200:
                    tasks = response.json()
                    self.log_result("Filter Tasks by Patient", True, f"Found {len(tasks)} tasks for patient")
                else:
                    self.log_result("Filter Tasks by Patient", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Filter Tasks by Patient", False, f"Exception: {str(e)}")

    def test_appointment_crud(self):
        """Test all Appointment CRUD operations"""
        print("\n=== TESTING APPOINTMENT CRUD OPERATIONS ===")
        
        # Test 1: Create Appointment
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                starts_at = datetime.now(timezone.utc) + timedelta(days=7)
                ends_at = starts_at + timedelta(hours=1)
                
                appointment_data = {
                    "patient_id": patient_id,
                    "provider_id": "provider-123",
                    "type": "consultation",
                    "title": "Initial Consultation",
                    "starts_at": starts_at.isoformat(),
                    "ends_at": ends_at.isoformat(),
                    "location": "Main Clinic - Room 101"
                }
                
                response = self.session.post(f"{API_BASE}/appointments", json=appointment_data)
                if response.status_code == 200:
                    data = response.json()
                    appointment_id = data.get("appointment_id")
                    if appointment_id:
                        self.created_resources['appointments'].append(appointment_id)
                        self.log_result("Create Appointment", True, f"Created appointment with ID: {appointment_id}", data)
                    else:
                        self.log_result("Create Appointment", False, "No appointment_id in response", data)
                else:
                    self.log_result("Create Appointment", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Create Appointment", False, f"Exception: {str(e)}")
        else:
            self.log_result("Create Appointment", False, "No patients available for appointment creation")

        # Test 2: List Appointments
        try:
            response = self.session.get(f"{API_BASE}/appointments")
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    self.log_result("List Appointments", True, f"Retrieved {len(appointments)} appointments")
                else:
                    self.log_result("List Appointments", False, "Response is not a list", appointments)
            else:
                self.log_result("List Appointments", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("List Appointments", False, f"Exception: {str(e)}")

        # Test 3: Filter Appointments by Patient
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                response = self.session.get(f"{API_BASE}/appointments", params={"patient_id": patient_id})
                if response.status_code == 200:
                    appointments = response.json()
                    self.log_result("Filter Appointments by Patient", True, f"Found {len(appointments)} appointments for patient")
                else:
                    self.log_result("Filter Appointments by Patient", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Filter Appointments by Patient", False, f"Exception: {str(e)}")

        # Test 4: Filter Appointments by Date
        try:
            response = self.session.get(f"{API_BASE}/appointments", params={"date": "today"})
            if response.status_code == 200:
                appointments = response.json()
                self.log_result("Filter Appointments by Date", True, f"Found {len(appointments)} appointments for today")
            else:
                self.log_result("Filter Appointments by Date", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Filter Appointments by Date", False, f"Exception: {str(e)}")

    def test_document_crud(self):
        """Test all Document CRUD operations"""
        print("\n=== TESTING DOCUMENT CRUD OPERATIONS ===")
        
        # Test 1: Upload Document
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                
                # Create a mock file for upload
                files = {
                    'file': ('test_lab_report.pdf', b'Mock PDF content for lab report', 'application/pdf')
                }
                data = {
                    'patient_id': patient_id,
                    'kind': 'lab'
                }
                
                # Note: Using requests for file upload, not session.post with json
                response = requests.post(f"{API_BASE}/documents/upload", params=data, files=files)
                if response.status_code == 200:
                    doc_data = response.json()
                    document_id = doc_data.get("document_id")
                    if document_id:
                        self.created_resources['documents'].append(document_id)
                        self.log_result("Upload Document", True, f"Uploaded document with ID: {document_id}", doc_data)
                    else:
                        self.log_result("Upload Document", False, "No document_id in response", doc_data)
                else:
                    self.log_result("Upload Document", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Upload Document", False, f"Exception: {str(e)}")
        else:
            self.log_result("Upload Document", False, "No patients available for document upload")

        # Test 2: List Documents
        try:
            response = self.session.get(f"{API_BASE}/documents")
            if response.status_code == 200:
                documents = response.json()
                if isinstance(documents, list):
                    self.log_result("List Documents", True, f"Retrieved {len(documents)} documents")
                else:
                    self.log_result("List Documents", False, "Response is not a list", documents)
            else:
                self.log_result("List Documents", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("List Documents", False, f"Exception: {str(e)}")

        # Test 3: Get Document by ID
        if self.created_resources['documents']:
            try:
                document_id = self.created_resources['documents'][0]
                response = self.session.get(f"{API_BASE}/documents/{document_id}")
                if response.status_code == 200:
                    document = response.json()
                    if document.get("document_id") == document_id:
                        self.log_result("Get Document by ID", True, f"Retrieved document: {document.get('kind')}")
                    else:
                        self.log_result("Get Document by ID", False, "Document ID mismatch", document)
                else:
                    self.log_result("Get Document by ID", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Get Document by ID", False, f"Exception: {str(e)}")

        # Test 4: Update Document Status
        if self.created_resources['documents']:
            try:
                document_id = self.created_resources['documents'][0]
                update_data = {
                    "status": "ingested",
                    "extracted": {
                        "fields": {"blood_pressure": "120/80", "heart_rate": "72"},
                        "confidence": 0.95
                    }
                }
                
                response = self.session.patch(f"{API_BASE}/documents/{document_id}", json=update_data)
                if response.status_code == 200:
                    self.log_result("Update Document Status", True, "Document status updated successfully")
                else:
                    self.log_result("Update Document Status", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Update Document Status", False, f"Exception: {str(e)}")

        # Test 5: Filter Documents by Patient
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                response = self.session.get(f"{API_BASE}/documents", params={"patient_id": patient_id})
                if response.status_code == 200:
                    documents = response.json()
                    self.log_result("Filter Documents by Patient", True, f"Found {len(documents)} documents for patient")
                else:
                    self.log_result("Filter Documents by Patient", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Filter Documents by Patient", False, f"Exception: {str(e)}")

    def test_claims_crud(self):
        """Test all Claims CRUD operations"""
        print("\n=== TESTING CLAIMS CRUD OPERATIONS ===")
        
        # Test 1: Create Claim
        if self.created_resources['patients']:
            try:
                patient_id = self.created_resources['patients'][0]
                claim_data = {
                    "patient_id": patient_id,
                    "insurance_provider": "Blue Cross Blue Shield",
                    "amount": 1500.00,
                    "procedure_code": "99213",
                    "diagnosis_code": "E11.9",
                    "service_date": "2024-11-01",
                    "description": "Office visit for diabetes management"
                }
                
                response = self.session.post(f"{API_BASE}/claims", json=claim_data)
                if response.status_code == 200:
                    data = response.json()
                    claim_id = data.get("claim_id")
                    if claim_id:
                        self.created_resources['claims'].append(claim_id)
                        self.log_result("Create Claim", True, f"Created claim with ID: {claim_id}", data)
                    else:
                        self.log_result("Create Claim", False, "No claim_id in response", data)
                else:
                    self.log_result("Create Claim", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Create Claim", False, f"Exception: {str(e)}")
        else:
            self.log_result("Create Claim", False, "No patients available for claim creation")

        # Test 2: List Claims
        try:
            response = self.session.get(f"{API_BASE}/claims")
            if response.status_code == 200:
                claims = response.json()
                if isinstance(claims, list):
                    self.log_result("List Claims", True, f"Retrieved {len(claims)} claims")
                else:
                    self.log_result("List Claims", False, "Response is not a list", claims)
            else:
                self.log_result("List Claims", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("List Claims", False, f"Exception: {str(e)}")

        # Test 3: Get Claim by ID
        if self.created_resources['claims']:
            try:
                claim_id = self.created_resources['claims'][0]
                response = self.session.get(f"{API_BASE}/claims/{claim_id}")
                if response.status_code == 200:
                    claim = response.json()
                    if claim.get("claim_id") == claim_id:
                        self.log_result("Get Claim by ID", True, f"Retrieved claim: {claim.get('insurance_provider')}")
                    else:
                        self.log_result("Get Claim by ID", False, "Claim ID mismatch", claim)
                else:
                    self.log_result("Get Claim by ID", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Get Claim by ID", False, f"Exception: {str(e)}")

        # Test 4: Get Claim Events
        if self.created_resources['claims']:
            try:
                claim_id = self.created_resources['claims'][0]
                response = self.session.get(f"{API_BASE}/claims/{claim_id}/events")
                if response.status_code == 200:
                    events = response.json()
                    if isinstance(events, list):
                        self.log_result("Get Claim Events", True, f"Retrieved {len(events)} events for claim")
                    else:
                        self.log_result("Get Claim Events", False, "Response is not a list", events)
                else:
                    self.log_result("Get Claim Events", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result("Get Claim Events", False, f"Exception: {str(e)}")

        # Test 5: Filter Claims by Status
        try:
            response = self.session.get(f"{API_BASE}/claims", params={"status": "pending"})
            if response.status_code == 200:
                claims = response.json()
                self.log_result("Filter Claims by Status", True, f"Found {len(claims)} pending claims")
            else:
                self.log_result("Filter Claims by Status", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Filter Claims by Status", False, f"Exception: {str(e)}")

    def test_dashboard_endpoints(self):
        """Test Dashboard endpoints"""
        print("\n=== TESTING DASHBOARD ENDPOINTS ===")
        
        # Test 1: Get Dashboard Stats
        try:
            response = self.session.get(f"{API_BASE}/dashboard/stats")
            if response.status_code == 200:
                stats = response.json()
                required_fields = ["pending_tasks", "appointments_today", "patients_total", "claims_pending"]
                if all(field in stats for field in required_fields):
                    self.log_result("Get Dashboard Stats", True, f"Retrieved stats: {stats}")
                else:
                    self.log_result("Get Dashboard Stats", False, "Missing required fields in stats", stats)
            else:
                self.log_result("Get Dashboard Stats", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Get Dashboard Stats", False, f"Exception: {str(e)}")

        # Test 2: Get Dashboard Appointments
        try:
            response = self.session.get(f"{API_BASE}/dashboard/appointments")
            if response.status_code == 200:
                appointments = response.json()
                if isinstance(appointments, list):
                    self.log_result("Get Dashboard Appointments", True, f"Retrieved {len(appointments)} appointments for dashboard")
                else:
                    self.log_result("Get Dashboard Appointments", False, "Response is not a list", appointments)
            else:
                self.log_result("Get Dashboard Appointments", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Get Dashboard Appointments", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all test suites"""
        print(f"Starting BacklineMD API Tests against: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all test suites
        self.test_patient_crud()
        self.test_task_crud()
        self.test_appointment_crud()
        self.test_document_crud()
        self.test_claims_crud()
        self.test_dashboard_endpoints()
        
        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\nFAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"❌ {test_name}: {result['details']}")
        
        print("\nCREATED RESOURCES:")
        for resource_type, resources in self.created_resources.items():
            if resources:
                print(f"{resource_type.title()}: {len(resources)} created")

if __name__ == "__main__":
    tester = BacklineMDTester()
    tester.run_all_tests()