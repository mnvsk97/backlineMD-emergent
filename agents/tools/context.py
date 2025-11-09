"""
Context Builder Service
Fetches patient context and memory for agents
"""

import os
import httpx
from typing import Optional, Dict, Any


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")


async def get_patient_context(
    patient_id: str, aspect: Optional[str] = None, tenant_id: str = "hackathon-demo"
) -> Dict[str, Any]:
    """
    Fetch patient context from backend

    Args:
        patient_id: Patient ID to fetch context for
        aspect: Memory aspect filter (intake, docs, scheduling, insurance, general)
        tenant_id: Tenant ID (default: hackathon-demo)

    Returns:
        Dictionary with:
        - summary: Latest AI-generated patient summary
        - citations: List of source documents
        - timeline: Document timeline sorted by date
        - relevant_tasks: Open/waiting tasks for this aspect
        - recent_actions: Recent actions on this patient
        - patient_context: Current patient status and details
    """
    client = httpx.AsyncClient(timeout=30.0)

    try:
        # Build URL
        url = f"{BACKEND_URL}/api/context/{patient_id}"
        params = {}
        if aspect:
            params["aspect"] = aspect
        if tenant_id:
            params["tenant_id"] = tenant_id

        # Fetch context
        response = await client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    except httpx.HTTPError as e:
        # Return empty context on error
        return {
            "summary": "",
            "citations": [],
            "timeline": [],
            "relevant_tasks": [],
            "recent_actions": [],
            "patient_context": {},
            "error": str(e),
        }

    finally:
        await client.aclose()


async def update_patient_summary(
    patient_id: str, summary: str, aspect: str, citations: list = None
) -> bool:
    """
    Update AI-generated patient summary

    Args:
        patient_id: Patient ID
        summary: New summary text
        aspect: Memory aspect (docs, intake, etc.)
        citations: List of source document IDs

    Returns:
        True if successful, False otherwise
    """
    client = httpx.AsyncClient(timeout=30.0)

    try:
        url = f"{BACKEND_URL}/api/ai-artifacts"
        payload = {
            "subject": {"type": "patient", "patient_id": patient_id},
            "kind": f"{aspect}_summary",
            "content": summary,
            "metadata": {"citations": citations or [], "aspect": aspect},
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()
        return True

    except httpx.HTTPError:
        return False

    finally:
        await client.aclose()
