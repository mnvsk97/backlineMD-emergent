# BacklineMD - Specification Document

## Project Overview

BacklineMD is a healthcare management platform that automates patient care workflows using AI agents. The system manages patient intake, document processing, appointment scheduling, insurance claims, and care coordination through specialized AI agents orchestrated by a main orchestrator.

## Architecture

The application follows a three-tier architecture:

1. **Frontend**: React-based web application with CopilotKit integration
2. **Backend**: FastAPI REST API server
3. **Agents**: LangGraph-based AI agent system with MCP (Model Context Protocol) server

### Technology Stack

- **Frontend**: React 19, React Router, CopilotKit, TailwindCSS, Radix UI
- **Backend**: FastAPI, Motor (MongoDB async driver), Pydantic
- **Agents**: LangGraph, DeepAgents, LangChain, FastMCP
- **Database**: MongoDB
- **AI Models**: OpenAI GPT-4o

## Backend

All backend files are located at the root level of the project.

### Server (`server.py`)

FastAPI application providing REST API endpoints for:

#### Patient Management
- `GET /api/patients` - List patients with search (n-gram based fuzzy search)
- `POST /api/patients` - Create new patient
- `GET /api/patients/{patient_id}` - Get patient details
- `GET /api/patients/{patient_id}/summary` - Get AI-generated patient summary (cached)

#### Document Management
- `GET /api/documents` - List documents (filterable by patient, kind, status)
- `POST /api/documents/upload` - Upload document (triggers async extraction)
- `GET /api/documents/{document_id}` - Get document details
- `PATCH /api/documents/{document_id}` - Update document status/extracted data

**Document Processing Flow**:
1. Document uploaded → status: `uploaded`
2. Async extraction triggered → status: `ingesting`
3. Extraction completes → status: `ingested` or `not_ingested`
4. Low confidence extractions create review tasks

#### Task Management
- `GET /api/tasks` - List tasks (filterable by state, patient, assignee, priority)
- `POST /api/tasks` - Create task (with transaction to update patient task count)
- `PATCH /api/tasks/{task_id}` - Update task state/add comments

#### Insurance Claims
- `GET /api/claims` - List claims (filterable by status, patient)
- `POST /api/claims` - Create new claim
- `GET /api/claims/{claim_id}` - Get claim details
- `GET /api/claims/{claim_id}/events` - Get claim event timeline

#### Appointments
- `GET /api/appointments` - List appointments (filterable by date, provider, patient)
- `POST /api/appointments` - Create appointment (with transaction to update patient count)

#### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics (pending tasks, appointments today, total patients, pending claims)
- `GET /api/dashboard/appointments` - Get today's appointments

#### Copilot
- `POST /api/copilot` - Simple CopilotKit endpoint (placeholder)

### Models (`models.py`)

Pydantic models defining:

**Enums**:
- `PatientStatus` - Patient workflow statuses (Intake In Progress, Intake Done, Doc Collection In Progress, etc.)
- `DocumentKind` - Document types (lab, imaging, medical_history, summary, consent_form)
- `DocumentStatus` - Document processing statuses (uploaded, ingesting, ingested, not_ingested)
- `TaskState` - Task states (open, in_progress, done, cancelled)
- `TaskPriority` - Task priorities (urgent, high, medium, low)
- `ClaimStatus` - Insurance claim statuses (pending, submitted, received, under_review, approved, denied, settlement_in_progress, settlement_done)
- `AgentType` - Agent types (intake, doc_extraction, care_taker, insurance)
- `AgentStatus` - Agent execution statuses (queued, running, waiting_input, completed, failed)

**Request Models**:
- `PatientCreate`, `PatientUpdate`
- `DocumentUpdate`
- `AppointmentCreate`
- `ClaimCreate`
- `TaskCreate`, `TaskUpdate`
- `AgentStart`, `AgentResume`

**Response Models**:
- `PatientResponse`, `DocumentResponse`, `TaskResponse`, `ClaimResponse`

### Database (`database.py`)

MongoDB connection management with:
- Connection pooling (min: 10, max: 50)
- Automatic index creation on startup
- Indexes for:
  - Patients: tenant_id + search.ngrams, tenant_id + mrn (unique)
  - Documents: tenant_id + patient_id + kind + created_at
  - Appointments: tenant_id + provider_id + starts_at, tenant_id + patient_id + starts_at
  - Claims: tenant_id + status + last_event_at
  - Tasks: tenant_id + assignee_id + state + due_at
  - AI Artifacts: TTL index on expires_at

**Collections**:
- `patients` - Patient records
- `documents` - Uploaded documents
- `tasks` - Task management
- `claims` - Insurance claims
- `claim_events` - Claim event timeline
- `appointments` - Appointment scheduling
- `consent_forms` - Consent form management
- `users` - User accounts (indexed but not actively used)
- `conversations`, `messages` - Chat/conversation history
- `agent_executions` - Agent execution tracking
- `ai_artifacts` - Cached AI-generated content (with TTL)
- `voice_calls` - Voice call records
- `form_templates` - Consent form templates

### Features

- **Multi-tenancy**: All operations scoped to `DEFAULT_TENANT = "hackathon-demo"`
- **Fuzzy Search**: N-gram based patient search
- **Transactions**: MongoDB transactions for atomic operations (task/appointment creation)
- **Async Processing**: Document extraction runs asynchronously
- **Caching**: Patient summaries cached in `ai_artifacts` collection with TTL
- **Logging**: Structured logging via `logger.py`

## Frontend (`frontend/`)

### Application Structure

React application with:
- **Routing**: React Router (Dashboard, Patients, Patient Details, Tasks, Treasury)
- **UI Components**: Radix UI components (shadcn/ui style)
- **Styling**: TailwindCSS
- **State Management**: React Context (`ChatContext`)
- **AI Integration**: CopilotKit for chat interface

### Pages

1. **DashboardPage** (`pages/DashboardPage.jsx`)
   - Displays statistics (pending tasks, appointments today, total patients, pending claims)
   - Shows today's appointments
   - Quick actions

2. **PatientsPage** (`pages/PatientsPage.jsx`)
   - Patient list with search
   - Create patient modal
   - Patient cards with status, task counts, appointment counts

3. **PatientDetailsPage** (`pages/PatientDetailsPage.jsx`)
   - Patient profile information
   - Documents list
   - Tasks list
   - Appointments list
   - Patient summary (AI-generated)

4. **TasksPage** (`pages/TasksPage.jsx`)
   - Task list with filtering
   - Create task modal
   - Task status management

5. **TreasuryPage** (`pages/TreasuryPage.jsx`)
   - Insurance claims list
   - Claim details modal with event timeline
   - Create claim modal

### Components

- **CopilotChatPopup** - CopilotKit chat interface
- **CreatePatientModal** - Patient creation form
- **CreateTaskModal** - Task creation form
- **CreateClaimModal** - Claim creation form
- **ClaimDetailModal** - Claim details with event timeline
- **SendFormsModal** - Consent form sending interface
- **Sidebar** - Navigation sidebar
- **Header** - Application header

### API Service (`services/api.js`)

Axios-based API client with:
- Base URL configuration (`REACT_APP_BACKEND_URL`)
- Endpoints for all backend routes
- Error handling

## Agents

All agent files are located at the root level of the project.

### Orchestrator (`orchestrator.py`)

Main orchestrator agent using DeepAgents that routes tasks to specialized sub-agents:

**Sub-Agents**:
1. **intake_agent** - Patient onboarding, document collection, consent forms, insurance verification
2. **doc_extraction_agent** - Medical data extraction from documents, normalization, timeline building, summaries
3. **insurance_agent** - Insurance verification, claim creation/submission, claim tracking, denial handling
4. **care_taker_agent** - Appointment scheduling, post-visit follow-ups, visit recaps, care coordination

**Architecture**:
- Uses LangGraph with DeepAgents framework
- Connects to MCP server at `http://localhost:8002/mcp`
- Each sub-agent has specific tool permissions
- Orchestrator delegates tasks to appropriate sub-agents

**Configuration** (`langgraph.json`):
- Graph: `orchestrator` → `./orchestrator.py:agent`
- Dependencies: `requirements.txt`
- Environment: `../.env`

### MCP Server (`mcp_server.py`)

FastMCP server providing tools for AI agents:

**Tool Categories**:

1. **Patient Tools**:
   - `find_or_create_patient` - Find existing or create new patient
   - `update_patient` - Update patient information
   - `get_patient` - Get patient details

2. **Appointment Tools**:
   - `get_appointments` - List appointments
   - `create_appointment` - Create appointment (with transaction)
   - `update_appointment` - Update appointment
   - `delete_appointment` - Delete appointment (with transaction)

3. **Insurance Claim Tools**:
   - `get_insurance_claims` - List claims
   - `create_insurance_claim` - Create claim with event
   - `update_insurance_claim` - Update claim status (creates event)

4. **Document Tools**:
   - `create_document` - Create document record
   - `update_document` - Update document status/extracted data
   - `get_documents` - List documents

5. **Consent Form Tools**:
   - `create_consent_form` - Create consent form
   - `get_consent_forms` - List consent forms
   - `update_consent_form` - Update consent form status
   - `send_consent_forms` - Send forms via DocuSign/email

6. **Task Tools**:
   - `create_task` - Create task (with transaction)
   - `update_task` - Update task state/priority/add comments
   - `get_tasks` - List tasks

**Tool Permissions**:
- Each agent type has specific tool access permissions
- Defined in `TOOL_PERMISSIONS` dictionary
- Enforced per agent type (intake, doc_extraction, care_taker, insurance)

**Server Configuration**:
- Runs on HTTP transport at port 8002
- Connects to same MongoDB instance as backend
- Uses same `DEFAULT_TENANT` for multi-tenancy

### Agent Prompts (`prompts/`)

Markdown files containing system prompts for each sub-agent:
- `intake.md` - Intake agent prompt
- `doc_extraction.md` - Document extraction agent prompt
- `insurance.md` - Insurance agent prompt
- `care_taker.md` - Care taker agent prompt

## Database Schema

### Patients Collection
```javascript
{
  _id: String (UUID),
  tenant_id: String,
  mrn: String (format: "MRN{6 digits}"),
  first_name: String,
  last_name: String,
  dob: String (YYYY-MM-DD),
  gender: String,
  contact: {
    email: String,
    phone: String,
    address: Object
  },
  preconditions: [String],
  flags: [String],
  latest_vitals: Object,
  profile_image: String (URL),
  status: String (PatientStatus enum),
  tasks_count: Number,
  appointments_count: Number,
  flagged_count: Number,
  search: {
    ngrams: [String]
  },
  created_at: DateTime,
  updated_at: DateTime,
  created_by: String
}
```

### Documents Collection
```javascript
{
  _id: String (UUID),
  tenant_id: String,
  patient_id: String,
  kind: String (DocumentKind enum),
  file: {
    url: String,
    name: String,
    mime: String,
    size: Number,
    sha256: String
  },
  ocr: {
    done: Boolean,
    engine: String
  },
  extracted: Object,
  status: String (DocumentStatus enum),
  created_at: DateTime,
  updated_at: DateTime
}
```

### Tasks Collection
```javascript
{
  _id: String (UUID),
  task_id: String (format: "T{5 digits}"),
  tenant_id: String,
  source: String ("manual" | "agent"),
  kind: String,
  title: String,
  description: String,
  patient_id: String,
  patient_name: String,
  assigned_to: String,
  agent_type: String,
  priority: String (TaskPriority enum),
  state: String (TaskState enum),
  confidence_score: Number (0-1),
  waiting_minutes: Number,
  ai_resume_hook: String (optional),
  doc_id: String (optional),
  comments: [{
    user_id: String,
    text: String,
    created_at: DateTime
  }],
  created_at: DateTime,
  updated_at: DateTime,
  created_by: String
}
```

### Claims Collection
```javascript
{
  _id: String (UUID),
  claim_id: String (format: "C{5 digits}"),
  tenant_id: String,
  patient_id: String,
  patient_name: String,
  insurance_provider: String,
  amount: Number (cents),
  amount_display: Number (dollars),
  procedure_code: String,
  diagnosis_code: String,
  service_date: String (YYYY-MM-DD),
  submitted_date: String (YYYY-MM-DD),
  description: String,
  status: String (ClaimStatus enum),
  last_event_at: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

### Appointments Collection
```javascript
{
  _id: String (UUID),
  tenant_id: String,
  patient_id: String,
  provider_id: String,
  type: String,
  title: String,
  starts_at: DateTime,
  ends_at: DateTime,
  location: String,
  status: String (AppointmentStatus enum),
  google_calendar: {
    event_id: String,
    calendar_id: String
  },
  created_at: DateTime,
  updated_at: DateTime
}
```

## Current State / Status

### Implemented Features

✅ **Backend API**:
- Complete REST API for all entities
- Patient management with fuzzy search
- Document upload and processing workflow
- Task management with transactions
- Insurance claim management with event timeline
- Appointment scheduling
- Dashboard statistics

✅ **Frontend**:
- React application with routing
- Patient management UI
- Task management UI
- Claim management UI
- Dashboard with statistics
- CopilotKit integration (basic)

✅ **Agents**:
- Orchestrator agent with sub-agent delegation
- MCP server with comprehensive tool set
- Agent prompts for specialized workflows
- Tool permission system

✅ **Database**:
- MongoDB schema with proper indexes
- Multi-tenancy support
- Transaction support for atomic operations

### Known Limitations / Placeholders

⚠️ **Mock/Incomplete Features**:
- Document extraction is mocked (simulates async processing)
- Patient summaries are generated with mock data
- Google Calendar integration is mocked
- DocuSign integration is mocked
- File uploads don't actually store files (metadata only)
- CopilotKit endpoint is a placeholder
- No actual authentication/authorization (uses `DEFAULT_TENANT`)
- No real AI model integration in backend (uses mock data)

⚠️ **Missing Features**:
- Real document OCR and extraction
- Actual file storage (S3/local)
- Real DocuSign integration
- Real Google Calendar integration
- User authentication/authorization
- WebSocket/SSE for real-time updates
- Agent execution tracking UI
- Voice call integration
- Real-time chat with agents

### Configuration

**Environment Variables**:
- `MONGO_URL` - MongoDB connection string (default: `mongodb://localhost:27017`)
- `DEFAULT_TENANT` - Tenant ID for multi-tenancy (default: `"hackathon-demo"`)
- `REACT_APP_BACKEND_URL` - Backend API URL (default: `http://localhost:8001`)
- OpenAI API key (for agents) - should be in `.env`

**Ports**:
- Backend API: `8001` (default FastAPI port)
- MCP Server: `8002`
- Frontend: `3000` (default React dev server)

## Dependencies

### Backend & Agents (`requirements.txt`)

Single requirements file at root level shared by both backend and agents:
- FastAPI
- Motor (MongoDB async driver)
- Pydantic
- Python-dotenv
- Uvicorn
- FastMCP
- LangGraph
- LangChain (OpenAI, Anthropic, Community, Core)
- DeepAgents
- LangChain MCP Adapters

### Frontend (`frontend/package.json`)
- React 19
- React Router 7
- CopilotKit
- Radix UI components
- TailwindCSS
- Axios

## Development Notes

### Project Structure
```
backlineMD-emergent/
├── server.py         # FastAPI backend server
├── models.py         # Pydantic models
├── database.py       # MongoDB connection management
├── logger.py         # Logging utilities
├── orchestrator.py  # Main orchestrator agent
├── mcp_server.py    # MCP server for agent tools
├── langgraph.json   # LangGraph configuration
├── requirements.txt  # Python dependencies (shared)
├── prompts/          # Agent prompt files
│   ├── intake.md
│   ├── doc_extraction.md
│   ├── insurance.md
│   └── care_taker.md
├── frontend/         # React frontend application
│   ├── src/
│   │   ├── pages/    # Page components
│   │   ├── components/  # UI components
│   │   ├── services/    # API client
│   │   └── ...
│   └── package.json
├── tests/            # Test files (placeholder)
├── seed_data.py      # Database seeding script
├── test_api.py       # API tests
├── db.sh             # Database setup script
├── SPEC.md           # This specification document
└── README.md         # Project README
```

### Key Design Decisions

1. **Multi-tenancy**: All operations scoped to tenant_id for future multi-tenant support
2. **Async Processing**: Document extraction runs asynchronously to avoid blocking API
3. **Transaction Support**: Critical operations (task/appointment creation) use MongoDB transactions
4. **Agent Architecture**: Orchestrator delegates to specialized sub-agents for context isolation
5. **MCP Protocol**: Agents communicate via MCP server for tool access
6. **Fuzzy Search**: N-gram based search for patient lookup
7. **Caching**: AI-generated summaries cached with TTL to reduce API calls

### Next Steps / Recommendations

1. Implement real document extraction (OCR, NLP)
2. Add file storage (S3 or local filesystem)
3. Implement authentication/authorization
4. Add WebSocket support for real-time updates
5. Integrate real DocuSign API
6. Integrate real Google Calendar API
7. Add agent execution monitoring UI
8. Implement voice call features
9. Add comprehensive error handling and retry logic
10. Add unit and integration tests

