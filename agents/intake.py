"""
Intake Agent
Completes patient onboarding by collecting documents and consent forms
"""

import os
from typing import Optional
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
with open(os.path.join(os.path.dirname(__file__), "prompts/intake.md")) as f:
    SYSTEM_PROMPT = f.read()

# LLM Configuration
model = ChatOpenAI(model="gpt-4o", temperature=0.3)


async def intake_workflow(patient_id: str, run_id: Optional[str] = None):
    """
    Main intake workflow

    Args:
        patient_id: Patient ID
        run_id: Optional run ID for tracking

    Returns:
        Result dictionary with status
    """
    # Step 1: Fetch context
    await emit_agent_event(
        agent_type="intake",
        patient_id=patient_id,
        step="assess_status",
        status="running",
        run_id=run_id,
        message="Assessing intake completion status",
        progress=1,
        total_steps=5,
    )

    context = await get_patient_context(patient_id, aspect="intake")

    # Step 2: Get tools
    tools = await get_agent_tools("intake")

    # Step 3: Create agent
    agent = create_deep_agent(
        name="intake_agent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    )

    # Step 4: Prepare input
    await emit_agent_event(
        agent_type="intake",
        patient_id=patient_id,
        step="check_requirements",
        status="running",
        run_id=run_id,
        message="Checking required documents and consents",
        progress=2,
        total_steps=5,
    )

    input_message = f"""
Complete intake process for patient {patient_id}:

**Patient Context:**
- Status: {context.get('patient_context', {}).get('status', 'Unknown')}
- Email: {context.get('patient_context', {}).get('email', 'Unknown')}

**Current Documents:**
{len(context.get('timeline', []))} documents uploaded

**Current Tasks:**
{len(context.get('relevant_tasks', []))} open tasks

**Instructions:**
1. Check what documents are uploaded (use get_documents)
2. Check consent form status (use get_consent_forms)
3. Identify what's missing:
   - Government ID
   - Insurance card (front & back)
   - Consent forms not signed
4. For missing items:
   - Create tasks for document uploads
   - Send consent forms via DocuSign (use send_consent_forms)
5. If everything is complete:
   - Update patient status to "Intake Done"
   - Then update to "Doc Collection In Progress"
   - Report completion
6. If items are pending:
   - Report what's waiting and create tasks

Begin intake assessment now.
"""

    # Step 5: Run agent
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": input_message}]})

        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None

        # Check if intake is complete or waiting
        content = str(last_message).lower() if last_message else ""

        if "intake done" in content or "complete" in content:
            # Intake complete
            await update_patient_status(patient_id, "Intake Done")
            await update_patient_status(patient_id, "Doc Collection In Progress")

            await emit_agent_event(
                agent_type="intake",
                patient_id=patient_id,
                step="completed",
                status="completed",
                run_id=run_id,
                message="Intake complete - advanced to document collection",
                progress=5,
                total_steps=5,
            )

            return {"status": "completed", "message": "Intake complete"}

        else:
            # Waiting for patient action
            await emit_agent_event(
                agent_type="intake",
                patient_id=patient_id,
                step="awaiting_patient",
                status="waiting_input",
                run_id=run_id,
                message="Waiting for patient to complete intake items",
                progress=4,
                total_steps=5,
            )

            return {"status": "waiting_input", "message": "Pending patient action"}

    except Exception as e:
        await emit_agent_event(
            agent_type="intake",
            patient_id=patient_id,
            step="error",
            status="failed",
            run_id=run_id,
            message=f"Error: {str(e)}",
            progress=0,
            total_steps=5,
        )

        return {"status": "failed", "error": str(e)}


# Create the DeepAgent graph
intake_agent = create_deep_agent(
    name="intake_agent",
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[],  # Tools added dynamically in workflow
)
