# BacklineMD - Healthcare Management Platform

BacklineMD is a healthcare management platform that automates patient care workflows using AI agents. The system manages patient intake, document processing, appointment scheduling, insurance claims, and care coordination through specialized AI agents orchestrated by a main orchestrator.

## Architecture

The application consists of four main components:

1. **Frontend**: Next.js 15 application with CopilotKit integration
2. **Backend**: FastAPI REST API server
3. **MCP Server**: FastMCP server providing tools for AI agents
4. **LangGraph Agents**: AI agent system with orchestrator and specialized sub-agents

## Prerequisites

- Python 3.12+
- Node.js 18+ and Yarn
- MongoDB (running on `localhost:27017`)
- OpenAI API key (for agents)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd backlineMD-emergent
```

### 2. Python Environment Setup

```bash
# Create virtual environment
uv venv
# or
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install Python dependencies
uv pip install -r requirements.txt
# or
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```env
MONGO_URL=mongodb://localhost:27017
DEFAULT_TENANT=hackathon-demo
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here  # Optional
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
rm -rf node_modules
yarn install

# Create .env.local file
echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:8001" > .env.local
echo "NEXT_PUBLIC_LANGGRAPH_DEPLOYMENT_URL=http://localhost:2024" >> .env.local
```

## Running the Application

You need to run all four services simultaneously. Open four terminal windows:

### Terminal 1: MongoDB

Make sure MongoDB is running:

```bash
# If using Homebrew on macOS
brew services start mongodb-community

# Or start manually
mongod
```

### Terminal 2: FastAPI Backend

```bash
# Activate virtual environment
source .venv/bin/activate

# Start FastAPI server
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

The backend will be available at `http://localhost:8001`

### Terminal 3: MCP Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start MCP server
python mcp_server.py
```

The MCP server will be available at `http://localhost:8002`

### Terminal 4: LangGraph Agents

```bash
# Activate virtual environment
source .venv/bin/activate

# Start LangGraph dev server
langgraph dev
```

The LangGraph server will be available at `http://localhost:2024`

### Terminal 5: Next.js Frontend

```bash
cd frontend

# Start Next.js dev server
yarn dev
# or
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Quick Start Script

You can also create a script to start all services. Create a `start.sh` file:

```bash
#!/bin/bash

# Start MongoDB (if not already running)
# brew services start mongodb-community

# Activate virtual environment
source .venv/bin/activate

# Start all services in background
echo "Starting FastAPI backend..."
uvicorn server:app --host 0.0.0.0 --port 8001 --reload &

echo "Starting MCP server..."
python mcp_server.py &

echo "Starting LangGraph agents..."
langgraph dev &

echo "Starting Next.js frontend..."
cd frontend
yarn dev &

echo "All services starting..."
echo "Backend: http://localhost:8001"
echo "MCP Server: http://localhost:8002"
echo "LangGraph: http://localhost:2024"
echo "Frontend: http://localhost:3000"
```

Make it executable:

```bash
chmod +x start.sh
./start.sh
```

## Service URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **MCP Server**: http://localhost:8002
- **LangGraph Server**: http://localhost:2024
- **API Documentation**: http://localhost:8001/docs

## Features

### Frontend Features

- **Dashboard**: Overview of tasks, appointments, and patients
- **Patient Management**: Create, view, and manage patients
- **Task Management**: View and manage tasks with filtering
- **Insurance Claims**: View and manage insurance claims
- **AI Chat**: Context-aware chat interface powered by CopilotKit
  - Provides page-specific context (patients, patient details, claims)
  - Connects to LangGraph orchestrator agent
  - Real-time chat with AI assistance

### Backend Features

- REST API for all entities
- Patient fuzzy search
- Document upload and processing
- Task management with transactions
- Insurance claim management
- Appointment scheduling

### Agent Features

- Orchestrator agent routes tasks to specialized sub-agents
- Intake agent for patient onboarding
- Document extraction agent for medical data extraction
- Insurance agent for claim management
- Care taker agent for appointment scheduling

## Development

### Project Structure

```
backlineMD-emergent/
├── server.py              # FastAPI backend
├── mcp_server.py          # MCP server for agents
├── orchestrator.py        # LangGraph orchestrator agent
├── models.py              # Pydantic models
├── database.py            # MongoDB connection
├── requirements.txt       # Python dependencies
├── langgraph.json         # LangGraph configuration
├── prompts/               # Agent prompts
├── frontend/              # Next.js frontend
│   ├── app/               # Next.js App Router
│   ├── src/               # Source files
│   └── package.json       # Node dependencies
└── README.md              # This file
```

### Key Technologies

- **Frontend**: Next.js 15, React 19, CopilotKit, TailwindCSS
- **Backend**: FastAPI, Motor (MongoDB), Pydantic
- **Agents**: LangGraph, DeepAgents, LangChain, FastMCP
- **Database**: MongoDB

## Troubleshooting

### Port Already in Use

If a port is already in use, you can:

1. Change the port in the service configuration
2. Kill the process using the port:
   ```bash
   # Find process using port
   lsof -i :8001
   # Kill process
   kill -9 <PID>
   ```

### MongoDB Connection Issues

Make sure MongoDB is running:

```bash
# Check if MongoDB is running
brew services list  # macOS
# or
sudo systemctl status mongod  # Linux
```

### Frontend Build Issues

If you encounter build issues:

```bash
cd frontend
rm -rf .next node_modules
yarn install
yarn dev
```

### CopilotKit Connection Issues

Make sure:
1. LangGraph server is running on port 2024
2. `NEXT_PUBLIC_LANGGRAPH_DEPLOYMENT_URL` is set correctly
3. The orchestrator agent is properly configured

## Documentation

For detailed documentation, see [SPEC.md](./SPEC.md)

## License

[Add your license here]
