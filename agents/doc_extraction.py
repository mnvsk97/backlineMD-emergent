"""
Document Extraction Agent
Extracts medical data from uploaded documents, builds timelines, generates summaries
"""

import os
from datetime import datetime
from typing import Optional
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from dotenv import load_dotenv

from tools import (
    get_agent_tools,
    get_patient_context,
    emit_agent_event,
    update_patient_status,
    create_human_task,
    update_patient_summary,
)

load_dotenv()

# Load system prompt
with open(os.path.join(os.path.dirname(__file__), "prompts/doc_extraction.md")) as f:
    SYSTEM_PROMPT = f.read()

# LLM Configuration
model = ChatOpenAI(model="gpt-4o", temperature=0.2)


async def doc_extraction_workflow(patient_id: str, document_id: str, run_id: Optional[str] = None):
    """
    Main document extraction workflow

    Args:
        patient_id: Patient ID
        document_id: Document ID to process
        run_id: Optional run ID for tracking

    Returns:
        Result dictionary with status and extracted data
    """
    # Step 1: Fetch context
    await emit_agent_event(
        agent_type="doc_extraction",
        patient_id=patient_id,
        step="fetch_context",
        status="running",
        run_id=run_id,
        message="Fetching patient context and document",
        progress=1,
        total_steps=6,
    )

    context = await get_patient_context(patient_id, aspect="docs")

    # Step 2: Get tools
    tools = await get_agent_tools("doc_extraction")

    # Step 3: Create agent
    agent = create_deep_agent(
        name="doc_extraction_agent",
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
    )

    # Step 4: Prepare input
    await emit_agent_event(
        agent_type="doc_extraction",
        patient_id=patient_id,
        step="extract_data",
        status="running",
        run_id=run_id,
        message="Extracting medical data from document",
        progress=2,
        total_steps=6,
    )

    input_message = f"""
Process this document for patient {patient_id}:

**Patient Context:**
- Status: {context.get('patient_context', {}).get('status', 'Unknown')}
- Preconditions: {', '.join(context.get('patient_context', {}).get('preconditions', []))}

**Previous Summary:**
{context.get('summary', 'No previous summary')}

**Document to Process:**
Document ID: {document_id}

**Instructions:**
1. Fetch the document details using get_documents
2. Extract all key medical information (dates, results, diagnoses)
3. Update the document with extracted fields using update_document
4. If confidence < 90%, create a human review task
5. Update the patient summary with new findings
6. Report completion

Begin extraction now.
"""

    # Step 5: Run agent
    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": input_message}]})

        # Step 6: Check if human review needed
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else None

        # Parse result to see if task was created
        task_created = False
        task_id = None

        if last_message and "create_task" in str(last_message):
            task_created = True
            # Extract task ID from tool call result
            # This is a simplified version - actual implementation would parse tool results

        if task_created:
            await emit_agent_event(
                agent_type="doc_extraction",
                patient_id=patient_id,
                step="awaiting_review",
                status="waiting_input",
                run_id=run_id,
                message="Document extraction complete - awaiting doctor review",
                progress=5,
                total_steps=6,
                created_task_id=task_id,
            )

            return {
                "status": "waiting_input",
                "task_id": task_id,
                "confidence": "low",
                "message": "Human review required",
            }
        else:
            # High confidence - no review needed
            await emit_agent_event(
                agent_type="doc_extraction",
                patient_id=patient_id,
                step="completed",
                status="completed",
                run_id=run_id,
                message="Document extraction complete - high confidence",
                progress=6,
                total_steps=6,
            )

            return {
                "status": "completed",
                "confidence": "high",
                "message": "Document processed successfully",
            }

    except Exception as e:
        await emit_agent_event(
            agent_type="doc_extraction",
            patient_id=patient_id,
            step="error",
            status="failed",
            run_id=run_id,
            message=f"Error: {str(e)}",
            progress=0,
            total_steps=6,
        )

        return {"status": "failed", "error": str(e)}


# Create the DeepAgent graph
doc_extraction_agent = create_deep_agent(
    name="doc_extraction_agent",
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[],  # Tools will be added dynamically in workflow
)
