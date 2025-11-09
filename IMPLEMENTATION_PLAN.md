# BacklineMD - Complete Implementation Plan
**Date:** 2025-11-09
**Tech Stack:** FastAPI · MongoDB · React · CopilotKit · AGUI · LangGraph · VAPI

---

## 1. UI Flow Review Against Requirements

### ✅ Current UI Status

| Feature | UI Ready | Backend Ready | Integration Ready |
|---------|----------|---------------|-------------------|
| Patient List | ✅ | ❌ | ❌ |
| Patient Details | ✅ | ❌ | ❌ |
| AI Patient Summary | ✅ (UI only) | ❌ | ❌ |
| Document Upload | ❌ | ❌ | ❌ |
| Document Status Tracking | ✅ (mock data) | ❌ | ❌ |
| Consent Forms Management | ✅ (UI only) | ❌ | ❌ |
| Send Forms Modal | ✅ | ❌ | ❌ |
| Task Management | ✅ | ❌ | ❌ |
| Create Task Modal | ✅ | ❌ | ❌ |
| Treasury/Claims List | ✅ (mock data) | ❌ | ❌ |
| Create Claim Modal | ✅ | ❌ | ❌ |
| Claim Detail Timeline | ✅ | ❌ | ❌ |
| Dashboard Actions Feed | ✅ (mock data) | ❌ | ❌ |
| Today's Schedule | ✅ (mock data) | ❌ | ❌ |
| CopilotKit Chat | ✅ | ⚠️ (basic endpoint) | ❌ |
| AGUI Monitoring | ❌ | ❌ | ❌ |

### ❌ Missing UI Components

1. **Create Patient Modal** - For Step 1 (Onboarding)
2. **Document Upload Component** - Drag & drop or file picker
3. **AGUI Agent Status Component** - Show agent execution state
4. **Voice Call Trigger** - VAPI integration UI
5. **Calendar Integration** - Google Calendar sync
6. **Real-time Notifications** - Toast for WebSocket events

---

## 2. Complete Data Model (MongoDB)

### Collections Schema

```javascript
// Common fields for all collections
{
  tenant_id: ObjectId,
  created_at: ISODate,
  updated_at: ISODate,
  created_by: String,
  updated_by: String
}

// 1. users
{
  _id: UUID,
  tenant_id: UUID,
  email: String (unique per tenant),
  name: String,
  password_hash: String,
  roles: ["doctor", "admin", "staff"],
  profile: {
    phone: String,
    title: String,
    specialty: String
  },
  created_at: ISODate,
  updated_at: ISODate
}
Index: {tenant_id: 1, email: 1} unique

// 2. patients
{
  _id: UUID,
  tenant_id: UUID,
  mrn: String (Medical Record Number),
  first_name: String,
  last_name: String,
  dob: String (CSFLE encrypted),
  gender: String,
  contact: {
    email: String,
    phone: String (CSFLE encrypted),
    address: Object
  },
  preconditions: [String],
  flags: [String],
  latest_vitals: {
    bp: String,
    hr: Number,
    weight: Number,
    height: Number,
    blood_type: String
  },
  profile_image: String,
  status: String (Active, Pending, Archived),
  tasks_count: Number,
  appointments_count: Number,
  flagged_count: Number,
  search: {
    ngrams: [String] // for fuzzy search
  },
  created_at: ISODate,
  updated_at: ISODate,
  created_by: String,
  updated_by: String
}
Indexes:
  - {tenant_id: 1, "search.ngrams": 1}
  - {tenant_id: 1, mrn: 1} unique

// 3. documents
{
  _id: UUID,
  tenant_id: UUID,
  patient_id: UUID,
  kind: String (lab, imaging, summary, medical_history, consent_form),
  file: {
    url: String,
    sha256: String,
    mime: String,
    size: Number,
    name: String
  },
  ocr: {
    done: Boolean,
    engine: String
  },
  extracted: {
    fields: Object,
    confidence: Number,
    needs_review: [String]
  },
  status: String (uploaded, ingesting, ingested, not_ingested, approved, rejected),
  agent_run_id: String, // Link to agent_executions
  created_at: ISODate,
  updated_at: ISODate
}
Indexes:
  - {tenant_id: 1, patient_id: 1, kind: 1, created_at: -1}
  - {tenant_id: 1, status: 1, created_at: -1}

// 4. consent_forms
{
  _id: UUID,
  tenant_id: UUID,
  patient_id: UUID,
  form_template_id: UUID,
  name: String,
  description: String,
  purpose: String,
  status: String (to_do, sent, in_progress, signed),
  sent_date: ISODate,
  signed_date: ISODate,
  docusign: {
    envelope_id: String,
    status: String,
    signed_document_url: String
  },
  created_at: ISODate,
  updated_at: ISODate
}
Index: {tenant_id: 1, patient_id: 1, status: 1}

// 5. form_templates
{
  _id: UUID,
  tenant_id: UUID,
  name: String,
  description: String,
  purpose: String,
  template_url: String,
  is_active: Boolean,
  created_at: ISODate,
  updated_at: ISODate
}

// 6. appointments
{
  _id: UUID,
  tenant_id: UUID,
  patient_id: UUID,
  provider_id: UUID,
  type: String (consultation, follow_up, procedure),
  title: String,
  starts_at: ISODate,
  ends_at: ISODate,
  location: String,
  status: String (scheduled, completed, cancelled),
  notes: String,
  google_calendar: {
    event_id: String,
    calendar_id: String
  },
  created_at: ISODate,
  updated_at: ISODate
}
Indexes:
  - {tenant_id: 1, provider_id: 1, starts_at: 1}
  - {tenant_id: 1, patient_id: 1, starts_at: 1}

// 7. claims
{
  _id: UUID,
  claim_id: String (generated),
  tenant_id: UUID,
  patient_id: UUID,
  patient_name: String,
  insurance_provider: String,
  amount: Number (cents),
  amount_display: Number (dollars),
  procedure_code: String,
  diagnosis_code: String,
  service_date: ISODate,
  submitted_date: ISODate,
  description: String,
  status: String (pending, submitted, received, under_review, approved, denied),
  last_event_at: ISODate,
  created_at: ISODate,
  updated_at: ISODate
}
Indexes:
  - {tenant_id: 1, status: 1, last_event_at: -1}
  - {tenant_id: 1, patient_id: 1}

// 8. claim_events
{
  _id: UUID,
  tenant_id: UUID,
  claim_id: UUID,
  event_type: String (submitted, received, under_review, approved, denied, pending_review),
  description: String,
  at: ISODate,
  time: String,
  payload: Object,
  created_at: ISODate
}
Index: {tenant_id: 1, claim_id: 1, at: 1}

// 9. tasks
{
  _id: UUID,
  task_id: String,
  tenant_id: UUID,
  source: String (agent, manual),
  kind: String (document_review, insurance_verification, follow_up, call_patient),
  assignee_id: UUID,
  assigned_to: String (name),
  agent_type: String (ai_agent, human),
  patient_id: UUID,
  patient_name: String,
  claim_id: UUID,
  doc_id: UUID,
  title: String,
  description: String,
  due_at: ISODate,
  priority: String (urgent, high, medium, low),
  state: String (open, in_progress, done, cancelled),
  confidence_score: Number,
  waiting_minutes: Number,
  ai_resume_hook: String, // URL or agent run ID to resume
  links: [String],
  comments: [Object],
  created_at: ISODate,
  updated_at: ISODate
}
Indexes:
  - {tenant_id: 1, assignee_id: 1, state: 1, due_at: 1}
  - {tenant_id: 1, source: 1, state: 1, created_at: -1}
  - {tenant_id: 1, patient_id: 1, state: 1}

// 10. conversations
{
  _id: UUID,
  tenant_id: UUID,
  channel: String (copilot, email, sms),
  subject: {
    patient_id: UUID,
    claim_id: UUID,
    appointment_id: UUID
  },
  participants: [UUID],
  last_msg_at: ISODate,
  created_at: ISODate,
  updated_at: ISODate
}
Index: {tenant_id: 1, "subject.patient_id": 1, last_msg_at: -1}

// 11. messages
{
  _id: UUID,
  tenant_id: UUID,
  conversation_id: UUID,
  sender: String (user_id or "agent"),
  sender_name: String,
  text: String,
  rich: {
    draft_email: Object,
    citation_ids: [UUID],
    suggested_actions: [Object]
  },
  attachments: [Object],
  agent_tags: [String],
  created_at: ISODate
}
Index: {tenant_id: 1, conversation_id: 1, created_at: 1}

// 12. agent_executions
{
  _id: UUID,
  run_id: String (UUID),
  tenant_id: UUID,
  agent: String (doc_extractor, insurance_verifier, onboarding_agent),
  subject: {
    patient_id: UUID,
    document_id: UUID,
    claim_id: UUID
  },
  status: String (queued, running, waiting_input, completed, failed),
  graph_step: String,
  state: Object,
  inputs: Object,
  outputs: Object,
  error: Object,
  waiting_for_task_id: UUID,
  created_at: ISODate,
  updated_at: ISODate
}
Indexes:
  - {tenant_id: 1, agent: 1, status: 1, updated_at: -1}
  - {tenant_id: 1, run_id: 1} unique

// 13. ai_artifacts (TTL collection)
{
  _id: UUID,
  tenant_id: UUID,
  kind: String (patient_summary, claim_draft),
  subject: {
    patient_id: UUID,
    claim_id: UUID
  },
  payload: Object,
  model: String,
  score: Number,
  expires_at: ISODate,
  created_at: ISODate
}
Index: {expires_at: 1} (TTL index)

// 14. voice_calls
{
  _id: UUID,
  tenant_id: UUID,
  vapi_call_id: String,
  patient_id: UUID,
  task_id: UUID,
  purpose: String (follow_up, insurance_inquiry, appointment_reminder),
  status: String (pending, initiated, in_progress, completed, failed),
  started_at: ISODate,
  ended_at: ISODate,
  duration_seconds: Number,
  transcript: String,
  summary: String,
  recording_url: String,
  created_at: ISODate,
  updated_at: ISODate
}
Index: {tenant_id: 1, patient_id: 1, created_at: -1}
```

---

## 3. Complete REST API Design

### Authentication & Headers
```
Authorization: Bearer <JWT>
X-Tenant-Id: <tenant_uuid>
Content-Type: application/json
```

### 3.1 Authentication APIs

```python
POST /api/auth/register
Body: {email, password, name, tenant_name}
Response: {user, tenant, token}

POST /api/auth/login
Body: {email, password}
Response: {user, token, tenant_id}

GET /api/auth/me
Response: {user, permissions}
```

### 3.2 Patient APIs

```python
GET /api/patients?q=&limit=20&skip=0
Response: [{patient_id, first_name, last_name, email, phone, status, tasks_count, appointments_count, flagged_count, profile_image}]

POST /api/patients
Body: {first_name, last_name, dob, gender, contact: {email, phone, address}, preconditions, latest_vitals}
Response: {patient_id, message: "Patient created"}

GET /api/patients/{patient_id}
Response: {patient object with all details}

PATCH /api/patients/{patient_id}
Body: {fields to update}
Response: {updated patient}

GET /api/patients/{patient_id}/summary
Response: {
  summary: "AI-generated summary text",
  citations: [{doc_id, kind, page, excerpt}],
  generated_at: ISO date,
  model: "gpt-4"
}
```

### 3.3 Document APIs

```python
POST /api/documents/upload
Body: {
  patient_id: UUID,
  kind: "lab" | "imaging" | "medical_history",
  file: File (multipart/form-data)
}
Response: {
  document_id: UUID,
  status: "uploaded",
  message: "Document uploaded successfully"
}
// Triggers document extraction agent

GET /api/documents?patient_id=&kind=&status=&limit=&skip=
Response: [{document_id, patient_id, kind, file: {name, url, size}, status, created_at}]

GET /api/documents/{document_id}
Response: {document object with extracted fields}

PATCH /api/documents/{document_id}
Body: {status: "approved"}
Response: {updated document}
```

### 3.4 Consent Form APIs

```python
GET /api/consent-forms?patient_id=
Response: [{form_id, name, description, status, sent_date, signed_date}]

GET /api/form-templates
Response: [{template_id, name, description, purpose}]

POST /api/consent-forms/send
Body: {
  patient_id: UUID,
  form_template_ids: [UUID]
}
Response: {
  sent_forms: [{form_id, name, status: "sent"}],
  message: "X forms sent via DocuSign"
}
// Triggers DocuSign envelope creation

PATCH /api/consent-forms/{form_id}/webhook
Body: {docusign webhook payload}
Response: {message: "Status updated"}
// DocuSign webhook endpoint
```

### 3.5 Appointment APIs

```python
GET /api/appointments?date=YYYY-MM-DD&provider_id=&patient_id=
Response: [{appointment_id, patient_name, provider_name, type, time, status, location}]

POST /api/appointments
Body: {
  patient_id: UUID,
  provider_id: UUID,
  type: "consultation",
  title: String,
  starts_at: ISO date,
  ends_at: ISO date,
  location: String
}
Response: {
  appointment_id: UUID,
  google_calendar: {event_id, event_link},
  message: "Appointment created and added to Google Calendar"
}

PATCH /api/appointments/{appointment_id}
Body: {status: "completed", notes: "..."}
Response: {updated appointment}
```

### 3.6 Claim APIs

```python
GET /api/claims?status=&patient_id=&limit=&skip=
Response: [{claim_id, claim_id_display, patient_name, insurance_provider, amount, status, submitted_date, last_event_at}]

POST /api/claims
Body: {
  patient_id: UUID,
  insurance_provider: String,
  amount: Number,
  procedure_code: String,
  diagnosis_code: String,
  service_date: ISO date,
  description: String
}
Response: {
  claim_id: UUID,
  claim_id_display: "C12345",
  status: "pending",
  message: "Claim created"
}

GET /api/claims/{claim_id}
Response: {claim object}

GET /api/claims/{claim_id}/events
Response: [{event_id, event_type, description, at, time}]

POST /api/claims/{claim_id}/draft-email
Body: {}
Response: {
  draft: "Dear insurance provider...",
  citations: [{doc_id, excerpt}],
  suggested_subject: "Follow up on Claim C12345"
}
```

### 3.7 Task APIs

```python
GET /api/tasks?state=&assignee_id=&patient_id=&priority=&limit=&skip=&sort=
Response: [{task_id, title, description, patient_name, assigned_to, agent_type, priority, state, confidence_score, waiting_minutes, created_at}]

POST /api/tasks
Body: {
  title: String,
  description: String,
  patient_id: UUID,
  assigned_to: String,
  agent_type: "ai_agent" | "human",
  priority: "urgent" | "high" | "medium" | "low",
  kind: String
}
Response: {task_id: UUID, message: "Task created"}

GET /api/tasks/{task_id}
Response: {task object}

PATCH /api/tasks/{task_id}
Body: {state: "done", comment: "Reviewed and approved"}
Response: {updated task}
// If ai_resume_hook present, triggers agent resume
```

### 3.8 Conversation & Message APIs

```python
GET /api/conversations?patient_id=&channel=copilot
Response: [{conversation_id, subject, participants, last_msg_at}]

POST /api/conversations
Body: {channel: "copilot", subject: {patient_id}}
Response: {conversation_id}

GET /api/conversations/{conversation_id}/messages?limit=50
Response: [{message_id, sender, sender_name, text, rich, created_at}]

POST /api/messages
Body: {
  conversation_id: UUID,
  text: String,
  rich: {draft_email: {}, citations: []}
}
Response: {message_id}
```

### 3.9 Agent APIs (Mock for now)

```python
POST /api/agents/{agent_name}/start
Body: {
  subject: {patient_id, document_id, claim_id},
  inputs: {}
}
Response: {
  run_id: UUID,
  status: "queued",
  message: "Agent started"
}

GET /api/agents/runs/{run_id}
Response: {
  run_id: UUID,
  agent: String,
  status: "running" | "waiting_input" | "completed" | "failed",
  graph_step: String,
  outputs: {},
  error: null
}

POST /api/agents/runs/{run_id}/resume
Body: {
  task_id: UUID,
  resolution: "approved"
}
Response: {message: "Agent resumed"}
```

### 3.10 Voice Call APIs (VAPI Integration)

```python
POST /api/voice/initiate-call
Body: {
  patient_id: UUID,
  task_id: UUID,
  purpose: "follow_up" | "insurance_inquiry",
  phone_number: String
}
Response: {
  call_id: UUID,
  vapi_call_id: String,
  status: "initiated"
}

GET /api/voice/calls?patient_id=&status=
Response: [{call_id, patient_name, purpose, status, started_at, duration_seconds}]

POST /api/voice/webhook
Body: {vapi webhook payload}
Response: {message: "Webhook processed"}
```

### 3.11 Real-time APIs

```python
WS /ws/tenant/{tenant_id}
Client → Server: {type: "subscribe", channels: ["tasks", "documents", "agent_runs"]}
Server → Client: {
  type: "task" | "document" | "agent_run" | "message",
  op: "insert" | "update",
  doc: {...}
}

GET /api/events/stream
Response: SSE stream of events
```

### 3.12 Dashboard Analytics APIs

```python
GET /api/dashboard/stats
Response: {
  pending_tasks: Number,
  appointments_today: Number,
  patients_total: Number,
  claims_pending: Number
}

GET /api/dashboard/appointments?date=today
Response: [{appointment object}]

GET /api/dashboard/recent-activity?limit=10
Response: [{activity_type, description, patient_name, timestamp}]
```

---

## 4. Agent System Architecture (Mock → Real)

### Mock Agent Implementation

```python
# Mock agent that simulates document extraction
@app.post("/api/agents/doc_extractor/start")
async def start_doc_extraction(body: dict):
    run_id = str(uuid.uuid4())
    
    # Create agent execution record
    agent_exec = {
        "run_id": run_id,
        "agent": "doc_extractor",
        "status": "queued",
        "subject": body.get("subject"),
        "inputs": body.get("inputs"),
        "created_at": datetime.utcnow()
    }
    await db.agent_executions.insert_one(agent_exec)
    
    # Simulate async processing
    asyncio.create_task(mock_extraction_process(run_id, body["subject"]["document_id"]))
    
    return {"run_id": run_id, "status": "queued"}

async def mock_extraction_process(run_id, document_id):
    # Wait 2 seconds
    await asyncio.sleep(2)
    
    # Update agent to running
    await db.agent_executions.update_one(
        {"run_id": run_id},
        {"$set": {"status": "running", "graph_step": "extracting"}}
    )
    
    # Wait 3 more seconds
    await asyncio.sleep(3)
    
    # Simulate extraction with random confidence
    confidence = random.uniform(0.75, 0.95)
    
    extracted_data = {
        "blood_type": "O+",
        "cholesterol": "205 mg/dL",
        "bp": "125/80",
        "confidence": confidence
    }
    
    # Update document
    await db.documents.update_one(
        {"_id": document_id},
        {"$set": {
            "status": "ingested" if confidence > 0.9 else "not_ingested",
            "extracted": {
                "fields": extracted_data,
                "confidence": confidence,
                "needs_review": [] if confidence > 0.9 else ["cholesterol"]
            }
        }}
    )
    
    # If low confidence, create task
    if confidence < 0.9:
        task = {
            "task_id": f"T{random.randint(10000, 99999)}",
            "source": "agent",
            "kind": "document_review",
            "title": "Verify Medical History Extraction",
            "description": f"Review extracted data - confidence: {int(confidence*100)}%",
            "agent_type": "ai_agent",
            "priority": "high",
            "state": "open",
            "confidence_score": confidence,
            "waiting_minutes": 0,
            "ai_resume_hook": run_id,
            "created_at": datetime.utcnow()
        }
        await db.tasks.insert_one(task)
        
        # Update agent to waiting_input
        await db.agent_executions.update_one(
            {"run_id": run_id},
            {"$set": {
                "status": "waiting_input",
                "graph_step": "waiting_human_review",
                "waiting_for_task_id": task["_id"]
            }}
        )
        
        # Send WebSocket notification
        await websocket_manager.broadcast({
            "type": "task",
            "op": "insert",
            "doc": task
        })
    else:
        # Mark agent as completed
        await db.agent_executions.update_one(
            {"run_id": run_id},
            {"$set": {
                "status": "completed",
                "graph_step": "done",
                "outputs": extracted_data
            }}
        )
    
    # Send WebSocket notification
    await websocket_manager.broadcast({
        "type": "document",
        "op": "update",
        "doc": {"document_id": document_id, "status": "ingested" if confidence > 0.9 else "not_ingested"}
    })
```

---

## 5. Implementation Phases

### Phase 1: Backend Foundation (Days 1-2)
**Priority: CRITICAL**

1. **MongoDB Setup**
   - [ ] Create all collections with indexes
   - [ ] Set up CSFLE for PHI fields
   - [ ] Create seed data for demo

2. **Core API Implementation**
   - [ ] Authentication (register, login, JWT)
   - [ ] Patient CRUD
   - [ ] Document CRUD (without upload)
   - [ ] Task CRUD
   - [ ] Claim CRUD
   - [ ] Appointment CRUD

3. **Mock Agent System**
   - [ ] Document extractor agent (mock)
   - [ ] Agent execution tracking
   - [ ] Task creation by agents
   - [ ] Agent resume logic

4. **WebSocket Foundation**
   - [ ] WebSocket connection manager
   - [ ] Event broadcasting
   - [ ] Subscribe/unsubscribe logic

**Deliverable:** Fully functional backend with mock agents

---

### Phase 2: Frontend Integration (Days 2-3)
**Priority: HIGH**

1. **API Integration**
   - [ ] Axios setup with interceptors
   - [ ] Authentication context
   - [ ] API service layer (patients, tasks, claims, etc.)

2. **New UI Components**
   - [ ] Create Patient Modal
   - [ ] Document Upload Component (drag & drop)
   - [ ] AGUI Agent Status Component
   - [ ] Real-time notification system

3. **Connect Existing UI**
   - [ ] Patients page → GET /api/patients
   - [ ] Patient details → GET /api/patients/{id}
   - [ ] Docs tab → GET /api/documents
   - [ ] Tasks page → GET /api/tasks
   - [ ] Treasury → GET /api/claims
   - [ ] Dashboard → GET /api/dashboard/stats

4. **WebSocket Integration**
   - [ ] WebSocket hook (useWebSocket)
   - [ ] Real-time task updates
   - [ ] Real-time document status updates
   - [ ] Toast notifications for events

**Deliverable:** Fully connected UI with real data

---

### Phase 3: Agent System Enhancement (Day 4)
**Priority: MEDIUM**

1. **Enhanced Mock Agents**
   - [ ] Insurance verification agent
   - [ ] Onboarding agent
   - [ ] Claim status checker agent
   - [ ] Patient summary generator

2. **AGUI Integration**
   - [ ] Display agent execution status
   - [ ] Show graph steps
   - [ ] Display agent outputs
   - [ ] Error handling

3. **CopilotKit Enhancement**
   - [ ] Tool calling for agents
   - [ ] Context enrichment
   - [ ] Action suggestions

**Deliverable:** Rich agent monitoring and interaction

---

### Phase 4: External Integrations (Day 5-6)
**Priority: MEDIUM**

1. **File Upload & Storage**
   - [ ] S3/Cloud Storage setup
   - [ ] File upload endpoint
   - [ ] Secure URL generation

2. **Email Integration (SendGrid)**
   - [ ] Send welcome emails
   - [ ] Send consent form emails
   - [ ] Send reminder emails

3. **DocuSign Integration**
   - [ ] Create envelopes
   - [ ] Webhook handling
   - [ ] Status updates

4. **Google Calendar Integration**
   - [ ] OAuth2 setup
   - [ ] Create events
   - [ ] Sync appointments

5. **VAPI Voice Integration**
   - [ ] Initiate calls
   - [ ] Webhook handling
   - [ ] Call transcripts

**Deliverable:** All external services integrated

---

### Phase 5: Polish & Demo Preparation (Day 6-7)
**Priority: HIGH**

1. **Demo Flow Setup**
   - [ ] Seed comprehensive demo data
   - [ ] Test complete flow
   - [ ] Fix bugs

2. **UI/UX Polish**
   - [ ] Loading states
   - [ ] Error states
   - [ ] Success animations
   - [ ] Smooth transitions

3. **Performance**
   - [ ] Optimize API calls
   - [ ] Implement caching
   - [ ] Lazy loading

4. **Documentation**
   - [ ] API documentation
   - [ ] Demo script
   - [ ] User guide

**Deliverable:** Demo-ready application

---

## 6. Demo Script (5 Minutes)

### Storyline: Alex Rodriguez's Journey

**Setup:**
- Pre-seeded patient: Alex Rodriguez
- 1 uploaded but not-ingested document
- 1 pending claim

**Flow:**

1. **Dashboard View (30s)**
   - Show Actions Feed with pending task
   - Show Today's Schedule
   - Point out AI Assistant

2. **Patient Onboarding (45s)**
   - Click "Patients" → "Create Patient"
   - Fill form for new patient "Maria Garcia"
   - Submit → Patient created
   - Show in patients list

3. **Document Upload & Processing (60s)**
   - Click Alex Rodriguez → Go to Docs tab
   - Upload "Blood Test Results - Nov 2024"
   - Watch status: uploaded → ingesting → ingested (or not_ingested)
   - If not_ingested: Show task created for review
   - Approve document → Status changes to approved

4. **AI Summary Generation (30s)**
   - Go to Summary tab
   - Show AI-generated patient summary with citations
   - Click citation → Jump to document

5. **Schedule Appointment (45s)**
   - Create appointment for Alex Rodriguez
   - Fill details: Consultation, Tomorrow 9:00 AM
   - Submit → Shows in Dashboard schedule
   - Mention Google Calendar integration

6. **Task Management (30s)**
   - Go to Tasks page
   - Show task created by agent
   - Click task → Review details
   - Approve task → Agent resumes
   - Task status changes to "done"

7. **Treasury & Claims (45s)**
   - Go to Treasury
   - Click pending claim for Alex Rodriguez
   - Show claim timeline
   - Click "AI Email" → Create task for insurance agent
   - Show task created

8. **Voice Call Demo (30s)**
   - From task → Click "AI Call"
   - Show VAPI integration
   - Mention call will be transcribed

9. **Chat Interaction (30s)**
   - Use CopilotKit chat
   - Ask: "What needs review today?"
   - Show context-aware response
   - Ask: "Create a follow-up task for Alex"
   - Show task created via chat

**Closing (15s)**
- Mention agent orchestration via LangGraph
- Mention monitoring via LangSmith
- Thank audience

---

## 7. Technical Notes

### Environment Variables

```bash
# Backend .env
MONGO_URL=mongodb://localhost:27017/backlinemd
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# External APIs
OPENAI_API_KEY=sk-...
SENDGRID_API_KEY=SG...
DOCUSIGN_CLIENT_ID=...
DOCUSIGN_CLIENT_SECRET=...
GOOGLE_CALENDAR_CLIENT_ID=...
GOOGLE_CALENDAR_CLIENT_SECRET=...
VAPI_API_KEY=...
S3_BUCKET_NAME=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# LangSmith
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=backlinemd

# Frontend .env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_WS_URL=ws://localhost:8001
```

### Polling Intervals (Fallback)
- Tasks: 20-30 seconds
- Documents: 5 seconds (while uploading)
- Agent runs: 10 seconds (while running)

### WebSocket Events
```javascript
{
  type: "task" | "document" | "agent_run" | "message" | "appointment" | "claim",
  op: "insert" | "update" | "delete",
  doc: {...}
}
```

---

## 8. Success Criteria

- [ ] Complete patient onboarding flow working
- [ ] Document upload with status tracking working
- [ ] Agent creates tasks when needed
- [ ] Tasks can be resolved and agents resume
- [ ] AI patient summary generation working
- [ ] Appointment scheduling working
- [ ] Claim creation and tracking working
- [ ] Real-time updates via WebSocket working
- [ ] CopilotKit chat context-aware
- [ ] All modals and forms functional
- [ ] Demo flow can be completed in 5 minutes
- [ ] No critical bugs

---

## 9. Next Steps After Hackathon

1. **Real Agent Implementation**
   - Deploy LangGraph agents
   - Connect to Hyperspell MCP
   - Implement all agent tools

2. **Security Hardening**
   - CSFLE for all PHI
   - Proper authentication & authorization
   - Rate limiting
   - Input validation

3. **Production Readiness**
   - Error handling
   - Logging & monitoring
   - Performance optimization
   - Load testing

4. **Advanced Features**
   - Multi-tenancy
   - Audit trails
   - Advanced analytics
   - Mobile app

---

**This plan provides a clear roadmap from current UI to fully functional demo-ready application.**
