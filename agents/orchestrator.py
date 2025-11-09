"""
BacklineMD Orchestrator Agent
Main orchestrator that routes tasks to specialized sub-agents
"""

import os
import asyncio
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import Tool
from typing import List

async def get_tools() -> List[Tool]:
    client = MultiServerMCPClient({
            "backlinemd": {
                "url": "http://localhost:8002/mcp",
                "transport": "streamable_http",
            }
        },
    )
    
    return await client.get_tools()

tools = asyncio.run(get_tools())
name_to_Tool = {tool.name: tool for tool in tools}

load_dotenv()

# Load orchestrator prompt
ORCHESTRATOR_PROMPT = """You are the BacklineMD Orchestrator Agent. Your role is to coordinate patient care workflows by routing tasks to specialized sub-agents.

## Available Sub-Agents

1. **intake_agent**: Handles patient onboarding
   - Collects required documents (ID, insurance cards)
   - Manages consent forms via DocuSign
   - Verifies insurance information
   - Updates patient status through intake stages
   - Use for: "Complete intake", "Check intake status", "Send consent forms"

2. **doc_extraction_agent**: Extracts medical data from documents
   - Extracts key medical information from uploaded documents
   - Normalizes data (dates, codes, measurements)
   - Builds patient timeline
   - Generates patient summaries
   - Creates review tasks for low-confidence extractions
   - Use for: "Extract document", "Process lab results", "Review medical history"

3. **insurance_agent**: Manages insurance claims and verification
   - Verifies insurance eligibility
   - Creates and submits insurance claims
   - Tracks claim status
   - Handles claim denials and appeals
   - Follows up on pending claims
   - Use for: "Create claim", "Check eligibility", "Follow up on claim", "Handle denial"

4. **care_taker_agent**: Coordinates patient care and scheduling
   - Schedules appointments (consultations, follow-ups, procedures)
   - Manages post-visit follow-ups
   - Sends visit recaps
   - Updates patient status through care stages
   - Use for: "Schedule appointment", "Post-visit follow-up", "Send recap"

## Workflow Rules

1. **Route Appropriately**: Delegate tasks to the correct sub-agent based on the task type
2. **Context Isolation**: Use sub-agents to keep your context clean - delegate complex multi-step tasks
3. **Monitor Progress**: Track sub-agent execution and handle any errors
4. **Coordinate Workflows**: Some tasks may require multiple sub-agents (e.g., intake → doc extraction → scheduling)

## Common Workflows

- **New Patient Onboarding**: intake_agent → doc_extraction_agent → care_taker_agent
- **Document Processing**: doc_extraction_agent
- **Claim Submission**: insurance_agent
- **Appointment Scheduling**: care_taker_agent

## Important

- Always delegate specialized tasks to sub-agents using the task() tool
- Don't try to do everything yourself - use sub-agents for context isolation
- If a task requires multiple steps, coordinate between sub-agents
- Report completion status and any errors back to the user

Begin by understanding the task, then delegate to the appropriate sub-agent.
"""

# LLM Configuration
model = ChatOpenAI(model="gpt-4o", temperature=0.3)


def load_prompt(prompt_file: str) -> str:
    """Load prompt from markdown file"""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)
    with open(prompt_path, "r") as f:
        return f.read()
    
agent_to_tools = {
    "intake": [
        "find_or_create_patient",
        "update_patient",
        "get_patient",
        "create_document",
        "get_documents",
        "update_document",
        "create_consent_form",
        "get_consent_forms",
        "update_consent_form",
        "send_consent_forms",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "doc_extraction": [
        "get_patient",
        "update_patient",
        "get_documents",
        "update_document",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "care_taker": [
        "get_patient",
        "update_patient",
        "get_appointments",
        "create_appointment",
        "update_appointment",
        "delete_appointment",
        "get_documents",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "insurance": [
        "get_patient",
        "get_insurance_claims",
        "create_insurance_claim",
        "update_insurance_claim",
        "get_documents",
        "create_task",
        "update_task",
        "get_tasks",
    ],
}


async def _create_subagents():
    """Create subagents as dictionaries"""
    # Load prompts
    intake_prompt = load_prompt("intake.md")
    doc_extraction_prompt = load_prompt("doc_extraction.md")
    insurance_prompt = load_prompt("insurance.md")
    care_taker_prompt = load_prompt("care_taker.md")

    # Get tools for each agent
    intake_tools = [name_to_Tool[tool] for tool in agent_to_tools["intake"]]
    doc_extraction_tools = [name_to_Tool[tool] for tool in agent_to_tools["doc_extraction"]]
    insurance_tools = [name_to_Tool[tool] for tool in agent_to_tools["insurance"]]
    care_taker_tools = [name_to_Tool[tool] for tool in agent_to_tools["care_taker"]]

    # Create subagents as dictionaries
    return [
        {
            "name": "intake_agent",
            "description": "Completes patient onboarding by collecting required documents, managing consent forms, and verifying insurance information. Use for intake completion, document collection, and consent form management.",
            "system_prompt": intake_prompt,
            "tools": intake_tools,
            "model": "openai:gpt-4o",
        },
        {
            "name": "doc_extraction_agent",
            "description": "Extracts medical data from uploaded documents, normalizes data, builds patient timelines, and generates summaries. Use for processing lab results, imaging reports, medical history documents, and extracting key medical information.",
            "system_prompt": doc_extraction_prompt,
            "tools": doc_extraction_tools,
            "model": "openai:gpt-4o",
        },
        {
            "name": "insurance_agent",
            "description": "Verifies insurance coverage, creates and submits insurance claims, tracks claim status, handles denials and appeals, and follows up with payers. Use for claim creation, eligibility verification, claim tracking, and denial handling.",
            "system_prompt": insurance_prompt,
            "tools": insurance_tools,
            "model": "openai:gpt-4o",
        },
        {
            "name": "care_taker_agent",
            "description": "Schedules appointments, manages post-visit follow-ups, sends visit recaps, and coordinates patient care. Use for appointment scheduling, post-visit tasks, sending recaps, and care coordination.",
            "system_prompt": care_taker_prompt,
            "tools": care_taker_tools,
            "model": "openai:gpt-4o",
        },
    ]


# Create the agent
subagents = asyncio.run(_create_subagents())
agent = create_deep_agent(
    model=model,
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[],  # Orchestrator primarily delegates to sub-agents
    subagents=subagents,
)
