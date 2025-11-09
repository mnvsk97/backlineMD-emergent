"""
Care Taker Agent
Schedules appointments, sends recaps, manages follow-up care
"""

import os
from typing import Optional
from datetime import datetime, timedelta
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from tools import (
    get_agent_tools,
    get_patient_context,
    emit_agent_event,
    update_patient_status,
    create_human_task,
)

load_dotenv()

# Load system prompt
with open(os.path.join(os.path.dirname(__file__), "prompts/care_taker.md")) as f:
    SYSTEM_PROMPT = f.read()

# LLM Configuration
model = ChatOpenAI(model="gpt-4o", temperature=0.4)


async def care_taker_workflow(
    patient_id: str,
    action: str = "schedule_visit",
    visit_type: str = "consultation",
    run_id: Optional[str] = None,
):
    """
    Main care coordination workflow

    Args:
        patient_id: Patient ID
        action: Action to perform (schedule_visit, post_visit_followup)
        visit_type: Type of visit (consultation, follow_up, procedure, review)
        run_id: Optional run ID for tracking

    Returns:
        Result dictionary with status and appointment details
    """
    # Step 1: Fetch context
    await emit_agent_event(
        agent_type="care_taker",
        patient_id=patient_id,
        step="fetch_context",
        status="running",
        run_id=run_id,
        message=f"Preparing to {action}",
        progress=1,
        total_steps=4,
    )

    context = await get_patient_context(patient_id, aspect="scheduling")

    # Step 2: Get tools
    tools = await get_agent_tools("care_taker")

    # Step 3: Create agent
    agent = create_deep_agent(
        name="care_taker_agent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    )

    # Step 4: Prepare input based on action
    if action == "schedule_visit":
        await emit_agent_event(
            agent_type="care_taker",
            patient_id=patient_id,
            step="schedule_appointment",
            status="running",
            run_id=run_id,
            message=f"Scheduling {visit_type}",
            progress=2,
            total_steps=4,
        )

        # Suggest date 3-5 days from now
        suggested_date = (datetime.now() + timedelta(days=4)).isoformat()

        input_message = f"""
Schedule a {visit_type} for patient {patient_id}:

**Patient Context:**
- Status: {context.get('patient_context', {}).get('status', 'Unknown')}
- Preconditions: {', '.join(context.get('patient_context', {}).get('preconditions', []))}

**Patient Summary:**
{context.get('summary', 'No summary available')}

**Existing Appointments:**
{len(context.get('appointments', []))} appointments scheduled

**Instructions:**
1. Create appointment using create_appointment:
   - Type: {visit_type}
   - Suggested date: {suggested_date}
   - Duration: 1 hour
   - Location: "Room 101" (or appropriate location)
   - Title: "{visit_type.replace('_', ' ').title()} - {context.get('patient_context', {}).get('first_name', '')} {context.get('patient_context', {}).get('last_name', '')}"
2. Update patient status:
   - If initial consultation → "Consultation Scheduled"
   - If review → "Review Scheduled"
   - If procedure → "Procedure Scheduled"
3. Create confirmation task to notify patient
4. Generate pre-visit summary based on patient context
5. Report completion with appointment details

Begin scheduling now.
"""

    elif action == "post_visit_followup":
        await emit_agent_event(
            agent_type="care_taker",
            patient_id=patient_id,
            step="post_visit_tasks",
            status="running",
            run_id=run_id,
            message="Creating post-visit follow-up tasks",
            progress=2,
            total_steps=4,
        )

        input_message = f"""
Complete post-visit follow-up for patient {patient_id}:

**Patient Context:**
- Status: {context.get('patient_context', {}).get('status', 'Unknown')}

**Instructions:**
1. Generate visit recap summary
2. Create follow-up tasks based on typical {visit_type} outcomes:
   - Review lab results (if ordered)
   - Schedule follow-up visit
   - Medication refill (if applicable)
3. Update patient status:
   - If consultation → "Review Scheduled" or "Awaiting Response"
   - If procedure → "Procedure Done"
   - If review → "Review Done"
4. Create task to send recap to patient
5. Report completion

Begin post-visit follow-up now.
"""

    else:
        return {"status": "failed", "error": f"Unknown action: {action}"}

    # Step 5: Run agent
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": input_message}]})

        await emit_agent_event(
            agent_type="care_taker",
            patient_id=patient_id,
            step="completed",
            status="completed",
            run_id=run_id,
            message=f"Care coordination {action} completed",
            progress=4,
            total_steps=4,
        )

        return {"status": "completed", "action": action, "visit_type": visit_type}

    except Exception as e:
        await emit_agent_event(
            agent_type="care_taker",
            patient_id=patient_id,
            step="error",
            status="failed",
            run_id=run_id,
            message=f"Error: {str(e)}",
            progress=0,
            total_steps=4,
        )

        return {"status": "failed", "error": str(e)}


# Create the DeepAgent graph
care_taker_agent = create_deep_agent(
    name="care_taker_agent",
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[],  # Tools added dynamically in workflow
)
