"""
Insurance Agent
Verifies coverage, creates claims, tracks status, handles follow-ups
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
    create_human_task,
)

load_dotenv()

# Load system prompt
with open(os.path.join(os.path.dirname(__file__), "prompts/insurance.md")) as f:
    SYSTEM_PROMPT = f.read()

# LLM Configuration
model = ChatOpenAI(model="gpt-4o", temperature=0.2)


async def insurance_workflow(
    patient_id: str,
    action: str = "create_claim",
    claim_id: Optional[str] = None,
    run_id: Optional[str] = None,
):
    """
    Main insurance workflow

    Args:
        patient_id: Patient ID
        action: Action to perform (create_claim, check_eligibility, follow_up, handle_denial)
        claim_id: Claim ID (for follow_up or handle_denial actions)
        run_id: Optional run ID for tracking

    Returns:
        Result dictionary with status and claim details
    """
    # Step 1: Fetch context
    await emit_agent_event(
        agent_type="insurance",
        patient_id=patient_id,
        step="fetch_context",
        status="running",
        run_id=run_id,
        message=f"Preparing to {action}",
        progress=1,
        total_steps=4,
    )

    context = await get_patient_context(patient_id, aspect="insurance")

    # Step 2: Get tools
    tools = await get_agent_tools("insurance")

    # Step 3: Create agent
    agent = create_deep_agent(
        name="insurance_agent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    )

    # Step 4: Prepare input based on action
    if action == "create_claim":
        await emit_agent_event(
            agent_type="insurance",
            patient_id=patient_id,
            step="create_claim",
            status="running",
            run_id=run_id,
            message="Creating insurance claim",
            progress=2,
            total_steps=4,
        )

        input_message = f"""
Create insurance claim for patient {patient_id}:

**Patient Context:**
- Insurance: {context.get('patient_context', {}).get('insurance_provider', 'Unknown')}

**Documents Available:**
{len(context.get('timeline', []))} documents for evidence

**Instructions:**
1. Review recent documents to extract:
   - Procedure codes (CPT)
   - Diagnosis codes (ICD-10)
   - Service date
2. Create claim using create_insurance_claim:
   - Insurance provider from patient record
   - Amount (estimate or from documents)
   - Procedure and diagnosis codes
   - Description of service
3. Set initial status to "pending"
4. Create tracking task for follow-up
5. Report claim ID and details

Begin claim creation now.
"""

    elif action == "check_eligibility":
        await emit_agent_event(
            agent_type="insurance",
            patient_id=patient_id,
            step="verify_eligibility",
            status="running",
            run_id=run_id,
            message="Checking insurance eligibility",
            progress=2,
            total_steps=4,
        )

        input_message = f"""
Check insurance eligibility for patient {patient_id}:

**Patient Insurance:**
{context.get('patient_context', {}).get('insurance_provider', 'Unknown')}

**Instructions:**
1. Extract insurance details from patient record
2. For demo purposes, simulate eligibility check (assume covered)
3. Create summary of coverage:
   - Covered services
   - Co-pay/deductible
   - Pre-authorization requirements
4. Create task to notify patient of coverage details
5. Report eligibility status

Begin eligibility check now.
"""

    elif action == "follow_up":
        await emit_agent_event(
            agent_type="insurance",
            patient_id=patient_id,
            step="follow_up_claim",
            status="running",
            run_id=run_id,
            message=f"Following up on claim {claim_id}",
            progress=2,
            total_steps=4,
        )

        input_message = f"""
Follow up on claim {claim_id} for patient {patient_id}:

**Instructions:**
1. Fetch claim details using get_insurance_claims
2. Check current status
3. If status is "submitted" or "under_review" for >7 days:
   - Draft follow-up email to payer
   - Create task for billing team to send
4. Update claim with follow-up note
5. Report status

Begin follow-up now.
"""

    elif action == "handle_denial":
        await emit_agent_event(
            agent_type="insurance",
            patient_id=patient_id,
            step="handle_denial",
            status="running",
            run_id=run_id,
            message=f"Handling denial for claim {claim_id}",
            progress=2,
            total_steps=4,
        )

        input_message = f"""
Handle denial for claim {claim_id} for patient {patient_id}:

**Instructions:**
1. Fetch claim details
2. Review denial reason
3. Gather additional documentation if needed
4. Draft appeal letter with:
   - Medical necessity justification
   - Supporting evidence
   - Reference to policy coverage
5. Create high-priority task for doctor review
6. Report appeal status

Begin denial handling now.
"""

    else:
        return {"status": "failed", "error": f"Unknown action: {action}"}

    # Step 5: Run agent
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": input_message}]})

        await emit_agent_event(
            agent_type="insurance",
            patient_id=patient_id,
            step="completed",
            status="completed",
            run_id=run_id,
            message=f"Insurance {action} completed",
            progress=4,
            total_steps=4,
        )

        return {"status": "completed", "action": action, "claim_id": claim_id}

    except Exception as e:
        await emit_agent_event(
            agent_type="insurance",
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
insurance_agent = create_deep_agent(
    name="insurance_agent",
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[],  # Tools added dynamically in workflow
)
