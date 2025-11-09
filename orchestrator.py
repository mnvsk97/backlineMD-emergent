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
from prompts import ORCHESTRATOR_PROMPT
import aiofiles

async def get_tools() -> List[Tool]:
    client = MultiServerMCPClient({
            "backlinemd": {
                "url": "http://localhost:8002/sse",
                "transport": "sse",
            }
        },
    )
    
    return await client.get_tools()


load_dotenv()


# LLM Configuration
model = ChatOpenAI(model="gpt-4.1", temperature=0.3)


async def load_prompt(prompt_file: str) -> str:
    """Load prompt from markdown file"""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)
    async with aiofiles.open(prompt_path, "r") as f:
        return await f.read()
    
agent_to_tools = {
    "admin": [
        "get_all_patients",
    ],
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
        "send_email",
        "send_welcome_email_to_patient",
    ],
    "doc_extraction": [
        "get_patient",
        "update_patient",
        "get_documents",
        "update_document",
        "create_task",
        "update_task",
        "get_tasks",
        "send_email",
        "send_document_confirmation_email",
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
        "send_email",
        "call_patient_to_schedule_appointment",
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
        "send_email",
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
    admin_prompt = await load_prompt("admin.md")
    # Get tools for each agent
    intake_tools = [name_to_Tool[tool] for tool in agent_to_tools["intake"]]
    doc_extraction_tools = [name_to_Tool[tool] for tool in agent_to_tools["doc_extraction"]]
    insurance_tools = [name_to_Tool[tool] for tool in agent_to_tools["insurance"]]
    care_taker_tools = [name_to_Tool[tool] for tool in agent_to_tools["care_taker"]]
    admin_tools = [name_to_Tool[tool] for tool in agent_to_tools["admin"]]
    # Create subagents as dictionaries
    return [
        {
            "name": "admin_agent",
            "description": "Administers the system, manages users, and performs administrative tasks. Use for system management, user management, and administrative tasks.",
            "system_prompt": admin_prompt,
            "tools": admin_tools,
            "model": "openai:gpt-4.1",
        },
        {
            "name": "intake_agent",
            "description": "Completes patient onboarding by collecting required documents, managing consent forms, and verifying insurance information. Use for intake completion, document collection, and consent form management.",
            "system_prompt": intake_prompt,
            "tools": intake_tools,
            "model": "openai:gpt-4.1",
        },
        {
            "name": "doc_extraction_agent",
            "description": "Extracts medical data from uploaded documents, normalizes data, builds patient timelines, and generates summaries. Use for processing lab results, imaging reports, medical history documents, and extracting key medical information.",
            "system_prompt": doc_extraction_prompt,
            "tools": doc_extraction_tools,
            "model": "openai:gpt-4.1",
        },
        {
            "name": "insurance_agent",
            "description": "Verifies insurance coverage, creates and submits insurance claims, tracks claim status, handles denials and appeals, and follows up with payers. Use for claim creation, eligibility verification, claim tracking, and denial handling.",
            "system_prompt": insurance_prompt,
            "tools": insurance_tools,
            "model": "openai:gpt-4.1",
        },
        {
            "name": "care_taker_agent",
            "description": "Schedules appointments, manages post-visit follow-ups, sends visit recaps, and coordinates patient care. Use for appointment scheduling, post-visit tasks, sending recaps, and care coordination.",
            "system_prompt": care_taker_prompt,
            "tools": care_taker_tools,
            "model": "openai:gpt-4.1",
        },
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
