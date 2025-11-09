"""
BacklineMD Orchestrator Agent
Main orchestrator that routes tasks to specialized sub-agents
"""

import os
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import Tool
from typing import List
from prompts import ORCHESTRATOR_PROMPT
import aiofiles

async def get_tools() -> List[Tool]:
    client = MultiServerMCPClient({
            "backlinemd": {
                "url": "https://patient-flow-19.preview.emergentagent.com/api/special/mcp",
                "transport": "streamable_http",
            }
        },
    )
    
    return await client.get_tools()


load_dotenv()


# LLM Configuration
model = ChatOpenAI(model="gpt-4o", temperature=0.3)


async def load_prompt(prompt_file: str) -> str:
    """Load prompt from markdown file"""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)
    async with aiofiles.open(prompt_path, "r") as f:
        return await f.read()
    
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
    "admin": [
        "get_patients",
        "find_or_create_patient",
        "update_patient",
        "get_patient",
        "create_task",
        "update_task",
        "get_tasks",
        "get_appointments",
        "create_appointment",
        "update_appointment",
        "delete_appointment",
        "get_insurance_claims",
    ],
}


async def _create_subagents():
    """Create subagents as dictionaries"""
    tools = await get_tools()
    name_to_Tool = {tool.name: tool for tool in tools}
    # Load prompts
    intake_prompt = await load_prompt("intake.md")
    doc_extraction_prompt = await load_prompt("doc_extraction.md")
    insurance_prompt = await load_prompt("insurance.md")
    care_taker_prompt = await load_prompt("care_taker.md")

    # Get tools for each agent
    intake_tools = [name_to_Tool[tool] for tool in agent_to_tools["intake"]]
    doc_extraction_tools = [name_to_Tool[tool] for tool in agent_to_tools["doc_extraction"]]
    insurance_tools = [name_to_Tool[tool] for tool in agent_to_tools["insurance"]]
    care_taker_tools = [name_to_Tool[tool] for tool in agent_to_tools["care_taker"]]
    admin_tools = [name_to_Tool[tool] for tool in agent_to_tools["admin"]]
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
        {
            "name": "admin_agent",
            "description": "Manages patients, appointments, insurance claims, and documents. Use for patient management, appointment management, insurance claim management, and document management.",
            "system_prompt": "You are an admin agent. You are responsible for managing patients, appointments, insurance claims, and documents. You are also responsible for managing the system and the users.",
            "tools": admin_tools,
            "model": "openai:gpt-4o",
        }
    ]


async def agent():
    subagents = await _create_subagents()
    tools = await get_tools()
    agent = create_deep_agent(
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=tools,
        subagents=subagents,
    )
    return agent
