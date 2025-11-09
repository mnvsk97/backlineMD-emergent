"""
Event Emission & Patient Updates
Emits SSE events and updates patient/task status
"""

import os
import httpx
from typing import Optional, Dict, Any


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
DEFAULT_TENANT = os.getenv("DEFAULT_TENANT", "hackathon-demo")


async def emit_agent_event(
    agent_type: str,
    patient_id: str,
    step: str,
    status: str,
    run_id: Optional[str] = None,
    message: Optional[str] = None,
    progress: Optional[int] = None,
    total_steps: Optional[int] = None,
    created_task_id: Optional[str] = None,
) -> bool:
    """
    Emit SSE event for agent activity

    Args:
        agent_type: Agent name (intake, doc_extraction, care_taker, insurance)
        patient_id: Patient ID
        step: Current step name
        status: Status (running, waiting, completed, failed)
        run_id: Agent execution run ID
        message: Human-readable message
        progress: Current step number
        total_steps: Total number of steps
        created_task_id: If agent created a task, include task ID

    Returns:
        True if event emitted successfully
    """
    client = httpx.AsyncClient(timeout=10.0)

    try:
        url = f"{BACKEND_URL}/api/events/emit"
        payload = {
            "tenant_id": DEFAULT_TENANT,
            "event_type": "agent_run",
            "data": {
                "run_id": run_id,
                "agent": agent_type,
                "patient_id": patient_id,
                "step": step,
                "status": status,
                "message": message,
                "progress": progress,
                "total_steps": total_steps,
                "created_task_id": created_task_id,
            },
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()
        return True

    except httpx.HTTPError:
        # Don't fail agent if event emission fails
        return False

    finally:
        await client.aclose()


async def update_patient_status(patient_id: str, new_status: str) -> bool:
    """
    Update patient status and emit SSE event

    Args:
        patient_id: Patient ID
        new_status: New status from PatientStatus enum

    Returns:
        True if successful
    """
    client = httpx.AsyncClient(timeout=30.0)

    try:
        url = f"{BACKEND_URL}/api/patients/{patient_id}"
        payload = {"status": new_status}

        response = await client.patch(url, json=payload)
        response.raise_for_status()
        return True

    except httpx.HTTPError:
        return False

    finally:
        await client.aclose()


async def create_human_task(
    patient_id: str,
    title: str,
    description: str,
    assigned_to: str = "Dr. James O'Brien",
    priority: str = "high",
    agent_type: str = "ai_agent",
    kind: Optional[str] = None,
) -> Optional[str]:
    """
    Create a task for human review

    Args:
        patient_id: Patient ID
        title: Task title
        description: Task description
        assigned_to: Who to assign to
        priority: urgent, high, medium, low
        agent_type: Agent that created this task
        kind: Task kind/category

    Returns:
        Task ID if successful, None otherwise
    """
    client = httpx.AsyncClient(timeout=30.0)

    try:
        url = f"{BACKEND_URL}/api/tasks"
        payload = {
            "patient_id": patient_id,
            "title": title,
            "description": description,
            "assigned_to": assigned_to,
            "priority": priority,
            "agent_type": agent_type,
            "kind": kind or "agent_review",
        }

        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("task_id")

    except httpx.HTTPError:
        return None

    finally:
        await client.aclose()


async def update_task_status(task_id: str, state: str, comment: Optional[str] = None) -> bool:
    """
    Update task status

    Args:
        task_id: Task ID
        state: New state (open, in_progress, done, cancelled)
        comment: Optional comment

    Returns:
        True if successful
    """
    client = httpx.AsyncClient(timeout=30.0)

    try:
        url = f"{BACKEND_URL}/api/tasks/{task_id}"
        payload = {"state": state}
        if comment:
            payload["comment"] = comment

        response = await client.patch(url, json=payload)
        response.raise_for_status()
        return True

    except httpx.HTTPError:
        return False

    finally:
        await client.aclose()
