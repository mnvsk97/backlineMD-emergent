"""
MCP Tools Connector
Connects to FastMCP server and exposes tools as LangChain tools
"""

import os
from typing import List
import httpx
from langchain_core.tools import Tool
from pydantic import BaseModel


# MCP Server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


class MCPToolWrapper:
    """Wrapper to call MCP tools via HTTP"""

    def __init__(self, tool_name: str, description: str, parameters: dict):
        self.tool_name = tool_name
        self.description = description
        self.parameters = parameters
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __call__(self, **kwargs) -> dict:
        """Execute MCP tool via FastMCP server"""
        url = f"{BACKEND_URL}/api/mcp/call"
        payload = {"tool": self.tool_name, "arguments": kwargs}

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"error": str(e), "success": False}

    async def aclose(self):
        """Close HTTP client"""
        await self.client.aclose()


async def get_mcp_tools() -> List[Tool]:
    """
    Fetch MCP tools from server and convert to LangChain tools

    Returns list of LangChain Tool objects that can be used by agents
    """
    client = httpx.AsyncClient(timeout=30.0)

    try:
        # Fetch tool schemas from MCP server
        response = await client.get(f"{BACKEND_URL}/api/mcp/tools")
        response.raise_for_status()
        tools_data = response.json()

        langchain_tools = []

        for tool_info in tools_data.get("tools", []):
            tool_name = tool_info["name"]
            description = tool_info.get("description", "")
            parameters = tool_info.get("inputSchema", {})

            # Create wrapper
            wrapper = MCPToolWrapper(tool_name, description, parameters)

            # Convert to LangChain Tool
            lc_tool = Tool(
                name=tool_name,
                description=description,
                func=lambda **kwargs: None,  # Sync not used
                coroutine=wrapper,  # Async function
            )

            langchain_tools.append(lc_tool)

        return langchain_tools

    finally:
        await client.aclose()


# Define tool categories for agent permissions
TOOL_PERMISSIONS = {
    "intake": [
        "create_document",
        "get_documents",
        "update_document",
        "create_consent_form",
        "get_consent_forms",
        "update_consent_form",
        "send_consent_forms",
        "update_patient",
        "create_task",
        "update_task",
        "get_tasks",
    ],
    "doc_extraction": [
        "get_documents",
        "update_document",
        "get_patient",
        "update_patient",
        "create_task",
        "update_task",
    ],
    "care_taker": [
        "get_appointments",
        "create_appointment",
        "update_appointment",
        "delete_appointment",
        "get_patient",
        "get_documents",
        "create_task",
        "update_task",
    ],
    "insurance": [
        "create_insurance_claim",
        "update_insurance_claim",
        "get_insurance_claims",
        "get_patient",
        "get_documents",
        "create_task",
        "update_task",
    ],
}


async def get_agent_tools(agent_type: str) -> List[Tool]:
    """
    Get tools filtered by agent permissions

    Args:
        agent_type: One of 'intake', 'doc_extraction', 'care_taker', 'insurance'

    Returns:
        List of tools that this agent is allowed to use
    """
    all_tools = await get_mcp_tools()
    allowed_tool_names = TOOL_PERMISSIONS.get(agent_type, [])

    # Filter tools by permission
    agent_tools = [
        tool for tool in all_tools if tool.name in allowed_tool_names
    ]

    return agent_tools
