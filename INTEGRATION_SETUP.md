# CopilotKit AG-UI Integration Setup

This document explains how to set up and test the CopilotKit AG-UI integration with LangGraph using the FastAPI backend.

## Architecture

The integration consists of three components:

1. **Frontend (React)**: Uses `@copilotkit/react-core` and `@copilotkit/react-ui` to display the chat interface
2. **FastAPI Backend**: Uses `copilotkit` Python SDK to integrate CopilotKit runtime with LangGraph
3. **LangGraph Server (Python)**: Runs the orchestrator agent that handles the actual AI logic

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `copilotkit`: CopilotKit Python SDK for FastAPI integration
- All other required dependencies

### 2. Start the Services

You need to start two services:

#### a. Start LangGraph Server

```bash
# From the project root
langgraph dev
```

This will start the LangGraph server on `http://localhost:2024` by default.

#### b. Start FastAPI Backend

```bash
# From the project root
uvicorn server:app --reload --port 8001
```

The FastAPI server will:
- Start on `http://localhost:8001`
- Automatically integrate CopilotKit at `/api/copilotkit` endpoint
- Connect to the orchestrator agent from `orchestrator.py`

#### c. Start React Frontend

```bash
# From the frontend directory
cd frontend
npm start
# or
yarn start
```

This will start the frontend on `http://localhost:3000` by default.

### 3. Configuration

The frontend is configured to use the FastAPI backend. It's set up in `frontend/src/App.js`:

```javascript
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

<CopilotKit runtimeUrl={`${BACKEND_URL}/api/copilotkit`} agent="orchestrator">
```

You can override the backend URL by setting the `REACT_APP_BACKEND_URL` environment variable.

## Testing the Integration

1. Make sure all services are running:
   - LangGraph server on port 2024
   - FastAPI backend on port 8001
   - React frontend on port 3000

2. Open the frontend in your browser: `http://localhost:3000`

3. Open the chat popup (if it's not already open)

4. Send a test message, for example:
   - "Hello, can you help me?"
   - "What can you do?"
   - "List all patients"

5. You should see:
   - The message appear in the chat
   - A response from the orchestrator agent
   - The agent's state and tool calls (if enabled in the UI)

## How It Works

### FastAPI Integration

The FastAPI server (`server.py`) uses the CopilotKit Python SDK to integrate with LangGraph:

```python
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from orchestrator import agent as orchestrator_agent

# Create CopilotKit SDK with LangGraph agent
copilotkit_sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="orchestrator",
            description="BacklineMD orchestrator agent...",
            graph=orchestrator_agent,
        ),
    ],
)

# Add CopilotKit endpoint to FastAPI app
add_fastapi_endpoint(app, copilotkit_sdk, "/api/copilotkit")
```

This automatically:
- Creates a GraphQL endpoint at `/api/copilotkit`
- Handles CopilotKit protocol requests
- Connects to the orchestrator agent graph
- Manages agent state and tool calls

### Request Flow

1. User sends a message in the chat UI
2. Frontend sends a GraphQL request to `http://localhost:8001/api/copilotkit`
3. FastAPI server receives the request and uses CopilotKit SDK to process it
4. CopilotKit SDK invokes the orchestrator agent graph directly
5. Response streams back through the FastAPI server to the frontend
6. Frontend displays the response in the chat UI

## Troubleshooting

### Issue: Chat messages not sending

**Check:**
1. Is the FastAPI server running? Check `http://localhost:8001/docs`
2. Is the LangGraph server running? Check `http://localhost:2024/docs`
3. Are there any CORS errors in the browser console?
4. Check the FastAPI server logs for errors

### Issue: "Agent not found" error

**Solution:** Make sure the `agent` prop in `App.js` matches the agent name in `server.py`. Currently it's set to `"orchestrator"`.

### Issue: ImportError for copilotkit

**Solution:** 
1. Install the package: `pip install copilotkit`
2. Make sure you're using the correct Python environment
3. Check that `requirements.txt` includes `copilotkit`

### Issue: GraphQL errors

**Solution:** The CopilotKit runtime uses GraphQL. Make sure:
1. The FastAPI server is using the correct endpoint (`/api/copilotkit`)
2. The frontend is pointing to the correct URL
3. The agent name matches the agent configuration

### Issue: Orchestrator agent not found

**Solution:**
1. Make sure `orchestrator.py` exports the `agent` variable
2. Check that the import in `server.py` is correct: `from orchestrator import agent as orchestrator_agent`
3. Verify that the LangGraph server is running and the graph is compiled correctly

## Notes

- The old `/api/copilot` endpoint is kept as a fallback if CopilotKit is not installed
- The CopilotKit SDK automatically handles the GraphQL protocol
- The orchestrator agent is imported directly from `orchestrator.py`, so it runs in the same process as the FastAPI server
- No separate proxy server is needed - everything runs through FastAPI

## Migration from Express Proxy

If you were previously using the Express proxy server (`copilotkit-proxy/`), you can now remove it. The FastAPI backend handles everything directly.

To migrate:
1. Install `copilotkit` Python package: `pip install copilotkit`
2. Update frontend to use FastAPI endpoint: `http://localhost:8001/api/copilotkit`
3. Remove or ignore the `copilotkit-proxy/` directory
