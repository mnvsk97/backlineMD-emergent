# BacklineMD - Complete Status Definitions & Reference

## 📋 Table of Contents
1. [Patient Statuses](#patient-statuses)
2. [Document Statuses](#document-statuses)
3. [Consent Form Statuses](#consent-form-statuses)
4. [Insurance Claim Statuses](#insurance-claim-statuses)
5. [Task States](#task-states)
6. [Task Priorities](#task-priorities)
7. [Appointment Types](#appointment-types)
8. [AI Agents](#ai-agents)
9. [Staff Members](#staff-members)

---

## 1. Patient Statuses

| Status | Description | UI Color | Meaning |
|--------|-------------|----------|---------|
| **Active - Routine Care** | Normal, ongoing treatment | 🟢 Green | Patient is stable, routine checkups |
| **Active - Under Treatment** | Active treatment plan | 🟡 Yellow | Patient undergoing active treatment |
| **Pending - Awaiting Documentation** | Waiting for docs | 🟠 Orange | Missing documents or forms |
| **Pending - Insurance Verification** | Insurance pending | 🟠 Orange | Insurance verification in progress |
| **Urgent - Requires Immediate Attention** | Critical/urgent | 🔴 Red | Needs immediate medical attention |
| **Follow-up Required** | Needs follow-up | 🟣 Purple | Requires follow-up visit or action |

### Patient Status Flow:
```
New Patient → Pending - Awaiting Documentation
           → Pending - Insurance Verification
           → Active - Under Treatment
           → Active - Routine Care
           ↘ Urgent - Requires Immediate Attention (if needed)
           ↘ Follow-up Required (periodic)
```

---

## 2. Document Statuses

| Status | Description | UI Indicator | Meaning |
|--------|-------------|--------------|---------|
| **uploaded** | Just uploaded | 🔵 Blue | Document received, not processed yet |
| **ingesting** | AI processing | 🟡 Yellow (spinner) | AI agent actively extracting data |
| **ingested** | Successfully processed | 🟢 Green | Data extracted, high confidence |
| **not_ingested** | Needs review | 🟠 Orange | Low confidence, human review needed |
| **approved** | Human approved | ✅ Green checkmark | Doctor verified the extraction |
| **rejected** | Rejected by human | ❌ Red X | Doctor rejected, needs re-upload |

### Document Status Flow:
```
uploaded → ingesting (2-5 seconds)
        → ingested (confidence >= 90%)
        → not_ingested (confidence < 90%) → creates task
        → (after review) → approved OR rejected
```

### Triggers:
- **uploaded → ingesting**: Automatic (on upload)
- **ingesting → ingested/not_ingested**: AI agent decides based on confidence
- **not_ingested → task created**: Automatic (for human review)

---

## 3. Consent Form Statuses

| Status | Description | UI Indicator | Meaning |
|--------|-------------|--------------|---------|
| **to_do** | Not sent yet | ⚪ Gray | Form needs to be sent to patient |
| **sent** | Sent via DocuSign | 🔵 Blue (envelope icon) | Email sent, awaiting signature |
| **in_progress** | Patient viewing/signing | 🟡 Yellow | Patient opened the form |
| **signed** | Completed | 🟢 Green (checkmark) | Patient signed, DocuSign complete |

### Consent Form Flow:
```
to_do → (click "Send Forms")
     → sent (via DocuSign API)
     → in_progress (patient opens email)
     → signed (patient completes)
```

### Form Types:
1. **Insurance Information Release** - For insurance verification
2. **Medical Records Request** - To obtain external records

---

## 4. Insurance Claim Statuses

| Status | Description | Timeline | Meaning |
|--------|-------------|----------|---------|
| **pending** | Created, not submitted | Day 0 | Claim created internally |
| **submitted** | Sent to insurance | Day 0-1 | Submitted to insurance provider |
| **received** | Insurance acknowledged | Day 1-2 | Insurance received the claim |
| **under_review** | Being reviewed | Day 2-7 | Claims department reviewing |
| **approved** | Claim approved | Day 7-14 | Payment approved, processing |
| **denied** | Claim denied | Day 7-14 | Denied, needs action |

### Claim Status Flow:
```
pending → submitted (manual/automatic)
       → received (insurance acknowledgment)
       → under_review (claims department)
       → approved OR denied
```

### Timeline Events:
Each claim has a timeline showing:
- Submission date & time
- Received confirmation
- Review started
- Final decision (approved/denied)
- Payment processing (if approved)

---

## 5. Task States

| State | Description | UI Color | Meaning |
|-------|-------------|----------|---------|
| **open** | New, unassigned | 🟡 Yellow | Task created, needs attention |
| **in_progress** | Being worked on | 🔵 Blue | Someone is actively working |
| **done** | Completed | 🟢 Green | Task finished successfully |
| **cancelled** | Cancelled | ⚫ Gray | Task no longer needed |

### Task State Flow:
```
open → (assign) → in_progress
    → (complete) → done
    → (cancel) → cancelled
```

---

## 6. Task Priorities

| Priority | Color | Use Case | SLA |
|----------|-------|----------|-----|
| **urgent** | 🔴 Red | Immediate medical attention needed | < 1 hour |
| **high** | 🟠 Orange | Important, needs quick action | < 4 hours |
| **medium** | 🟡 Yellow | Normal priority | < 24 hours |
| **low** | 🟢 Green | Routine, no rush | < 48 hours |

### Priority Guidelines:
- **Urgent**: Abnormal lab results, missed critical appointment, urgent follow-up
- **High**: Document review needed, insurance resubmission, medication interactions
- **Medium**: Send consent forms, schedule consultation, routine prior auth
- **Low**: Annual checkup scheduling, routine paperwork

---

## 7. Appointment Types

| Type | Duration | Location | Description |
|------|----------|----------|-------------|
| **initial_consultation** | 60 min | Office | First visit with patient |
| **follow_up** | 30 min | Office | Follow-up visit |
| **procedure** | 90 min | Office | Minor procedures |
| **telehealth** | 20 min | Virtual | Video consultation |
| **lab_review** | 30 min | Office | Review test results |
| **consultation** | 45 min | Office | Specialist consultation |

### Composio Integration:
- All appointments create Google Calendar events
- Metadata: `composio_metadata.action_id`, `calendar_service: "google"`
- Calendar link: Auto-generated for invites

---

## 8. AI Agents

| Agent Name | Purpose | Task Type | When Triggered |
|------------|---------|-----------|----------------|
| **AI - Document Extractor** | Extract data from medical documents | `document_review` | On document upload |
| **AI - Insurance Verifier** | Verify insurance coverage | `insurance_verification` | New patient or policy change |
| **AI - Onboarding Agent** | Guide new patient onboarding | `onboarding` | New patient creation |
| **AI - Prior Auth Agent** | Submit prior authorization | `prior_authorization` | Procedure requires auth |
| **AI - Claim Status Checker** | Check claim status with insurance | `claim_follow_up` | Claim pending > 7 days |

### Agent Behavior:
- **Confidence Threshold**: 90%
- If confidence < 90% → Creates task for human review
- If confidence >= 90% → Proceeds automatically
- All agents broadcast WebSocket events
- State tracking in `agent_executions` collection

---

## 9. Staff Members

### Doctors:
1. **Dr. James O'Brien** - Medical Director
   - Specialties: General practice, cardiology
   - Reviews: Blood tests, medication interactions
   
2. **Dr. Sarah Chen** - Primary Care Physician
   - Specialties: Diabetes, preventive care
   - Reviews: Chronic disease management
   
3. **Dr. Michael Rodriguez** - Specialist
   - Specialties: Urgent care, follow-ups
   - Reviews: Urgent cases, abnormal results

### Back Office Staff:
1. **Emily Parker - Insurance Coordinator**
   - Responsibilities: Prior auth, claim submissions, insurance verification
   - Handles: All insurance-related tasks
   
2. **David Kim - Records Manager**
   - Responsibilities: Document management, consent forms, scheduling
   - Handles: Administrative tasks, patient records

---

## 10. Task Assignment Logic

| Task Type | Default Assignee | Agent Type |
|-----------|------------------|------------|
| Document review | Dr. James O'Brien | ai_agent |
| Consent forms | Emily Parker | human |
| Schedule consultation | David Kim | human |
| Insurance verification | Emily Parker | ai_agent |
| Urgent follow-up | Dr. Sarah Chen | human |
| Medication review | Dr. James O'Brien | ai_agent |
| Prior authorization | Emily Parker | ai_agent |
| Routine checkup | David Kim | human |

---

## 11. Color Scheme Reference

### Status Colors:
- 🔴 **Red** (#EF4444): Urgent, denied, critical
- 🟠 **Orange** (#F97316): High priority, pending
- 🟡 **Yellow** (#EAB308): Medium priority, in progress
- 🟢 **Green** (#10B981): Success, completed, approved
- 🔵 **Blue** (#3B82F6): Sent, info
- 🟣 **Purple** (#8B5CF6): Primary brand color
- ⚫ **Gray** (#6B7280): Cancelled, inactive

### UI Elements:
- **Primary Actions**: Purple (#8B5CF6)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#EAB308)
- **Danger**: Red (#EF4444)
- **Info**: Blue (#3B82F6)

---

## 12. API Query Parameters

### Patients:
```
GET /api/patients?q=alex&limit=20&skip=0
- q: Search by name (uses n-grams)
- limit: Max results (default: 20)
- skip: Pagination offset
```

### Documents:
```
GET /api/documents?patient_id={id}&kind=lab&status=ingested
- patient_id: Filter by patient
- kind: lab, imaging, medical_history, summary
- status: uploaded, ingesting, ingested, not_ingested, approved, rejected
```

### Tasks:
```
GET /api/tasks?state=open&priority=urgent&patient_id={id}
- state: open, in_progress, done, cancelled
- priority: urgent, high, medium, low
- patient_id: Filter by patient
```

### Claims:
```
GET /api/claims?status=pending&patient_id={id}
- status: pending, submitted, received, under_review, approved, denied
- patient_id: Filter by patient
```

### Appointments:
```
GET /api/appointments?date=today&provider_id={id}
- date: today, YYYY-MM-DD, or omit
- provider_id: Filter by doctor
- patient_id: Filter by patient
```

---

## 13. WebSocket Events

### Event Types:
- `patient` - Patient created/updated
- `document` - Document uploaded/status changed
- `task` - Task created/updated/completed
- `claim` - Claim created/status changed
- `appointment` - Appointment scheduled/updated
- `agent_run` - Agent execution updates

### Event Structure:
```json
{
  "type": "task",
  "op": "insert" | "update" | "delete",
  "doc": {
    "task_id": "uuid",
    "title": "Task title",
    "patient_name": "John Doe",
    "priority": "high",
    "state": "open"
  }
}
```

---

**This document serves as the single source of truth for all statuses, workflows, and system behavior in BacklineMD.**
