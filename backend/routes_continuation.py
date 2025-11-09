# This file contains the remaining routes to be added to server_new.py
from datetime import datetime, timezone

# ==================== TASK ROUTES ====================


@app.get("/api/tasks")
async def list_tasks(
    state: Optional[str] = None,
    patient_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    query = {"tenant_id": tenant_id}
    if state:
        query["state"] = state
    if patient_id:
        query["patient_id"] = patient_id
    if assignee_id:
        query["assignee_id"] = assignee_id
    if priority:
        query["priority"] = priority

    cursor = db.tasks.find(query).skip(skip).limit(limit).sort("created_at", -1)
    tasks = await cursor.to_list(length=limit)

    return [
        {
            "task_id": task["task_id"],
            "title": task["title"],
            "description": task["description"],
            "patient_name": task.get("patient_name"),
            "assigned_to": task["assigned_to"],
            "agent_type": task["agent_type"],
            "priority": task["priority"],
            "state": task["state"],
            "confidence_score": task.get("confidence_score"),
            "waiting_minutes": task.get("waiting_minutes", 0),
            "created_at": task["created_at"],
        }
        for task in tasks
    ]


@app.post("/api/tasks")
async def create_task(
    task_data: TaskCreate, current_user: dict = Depends(get_current_user)
):
    from database import get_client

    db = get_db()
    client = get_client()
    tenant_id = current_user["tenant_id"]

    # Get patient name
    patient = await db.patients.find_one(
        {"_id": task_data.patient_id, "tenant_id": tenant_id}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    task_id = str(uuid.uuid4())
    task = {
        "_id": task_id,
        "task_id": f"T{random.randint(10000, 99999)}",
        "tenant_id": tenant_id,
        "source": "manual",
        "kind": task_data.kind or "general",
        "title": task_data.title,
        "description": task_data.description,
        "patient_id": task_data.patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "assigned_to": task_data.assigned_to,
        "agent_type": task_data.agent_type,
        "priority": task_data.priority,
        "state": TaskState.OPEN,
        "confidence_score": 1.0,
        "waiting_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": current_user["user_id"],
    }

    # Use transaction to ensure atomicity
    async with await client.start_session() as session:
        async with session.start_transaction():
            await db.tasks.insert_one(task, session=session)
            await db.patients.update_one(
                {"_id": task_data.patient_id},
                {"$inc": {"tasks_count": 1}},
                session=session,
            )

    # Broadcast event
    await broadcast_event(
        tenant_id, "task", "insert", {"task_id": task_id, "title": task["title"]}
    )

    return {"task_id": task_id, "message": "Task created successfully"}


@app.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    update_fields = {}
    if update_data.state:
        update_fields["state"] = update_data.state
    if update_data.comment:
        update_fields["$push"] = {
            "comments": {
                "user_id": current_user["user_id"],
                "text": update_data.comment,
                "created_at": datetime.now(timezone.utc),
            }
        }

    update_fields["updated_at"] = datetime.now(timezone.utc)

    result = await db.tasks.update_one(
        {"_id": task_id, "tenant_id": tenant_id}, {"$set": update_fields}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")

    # Broadcast event
    await broadcast_event(
        tenant_id, "task", "update", {"task_id": task_id, "state": update_data.state}
    )

    return {"message": "Task updated successfully"}


# ==================== CLAIM ROUTES ====================


@app.get("/api/claims")
async def list_claims(
    status: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    query = {"tenant_id": tenant_id}
    if status:
        query["status"] = status
    if patient_id:
        query["patient_id"] = patient_id

    cursor = db.claims.find(query).skip(skip).limit(limit).sort("last_event_at", -1)
    claims = await cursor.to_list(length=limit)

    return [
        {
            "claim_id": claim["_id"],
            "claim_id_display": claim["claim_id"],
            "patient_id": claim["patient_id"],
            "patient_name": claim["patient_name"],
            "insurance_provider": claim["insurance_provider"],
            "amount": claim["amount_display"],
            "status": claim["status"],
            "submitted_date": claim["submitted_date"],
            "last_event_at": claim.get("last_event_at"),
        }
        for claim in claims
    ]


@app.post("/api/claims")
async def create_claim(
    claim_data: ClaimCreate, current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    # Get patient
    patient = await db.patients.find_one(
        {"_id": claim_data.patient_id, "tenant_id": tenant_id}
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    claim_id = str(uuid.uuid4())
    claim_id_display = f"C{random.randint(10000, 99999)}"

    claim = {
        "_id": claim_id,
        "claim_id": claim_id_display,
        "tenant_id": tenant_id,
        "patient_id": claim_data.patient_id,
        "patient_name": f"{patient['first_name']} {patient['last_name']}",
        "insurance_provider": claim_data.insurance_provider,
        "amount": int(claim_data.amount * 100),  # Store in cents
        "amount_display": claim_data.amount,
        "procedure_code": claim_data.procedure_code,
        "diagnosis_code": claim_data.diagnosis_code,
        "service_date": claim_data.service_date,
        "submitted_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "description": claim_data.description,
        "status": ClaimStatus.PENDING,
        "last_event_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    await db.claims.insert_one(claim)

    # Create initial event
    event = {
        "_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "claim_id": claim_id,
        "event_type": "submitted",
        "description": f"Claim submitted to {claim_data.insurance_provider} for ${claim_data.amount:.2f}",
        "at": datetime.now(timezone.utc),
        "time": datetime.now(timezone.utc).strftime("%I:%M %p"),
        "created_at": datetime.now(timezone.utc),
    }

    await db.claim_events.insert_one(event)

    # Broadcast event
    await broadcast_event(
        tenant_id,
        "claim",
        "insert",
        {"claim_id": claim_id, "patient_name": claim["patient_name"]},
    )

    return {
        "claim_id": claim_id,
        "claim_id_display": claim_id_display,
        "status": ClaimStatus.PENDING,
        "message": "Claim created successfully",
    }


@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    claim = await db.claims.find_one({"_id": claim_id, "tenant_id": tenant_id})
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return {
        "claim_id": claim["_id"],
        "claim_id_display": claim["claim_id"],
        "patient_name": claim["patient_name"],
        "insurance_provider": claim["insurance_provider"],
        "amount": claim["amount_display"],
        "procedure_code": claim.get("procedure_code"),
        "diagnosis_code": claim.get("diagnosis_code"),
        "service_date": claim["service_date"],
        "submitted_date": claim["submitted_date"],
        "description": claim.get("description"),
        "status": claim["status"],
    }


@app.get("/api/claims/{claim_id}/events")
async def get_claim_events(
    claim_id: str, current_user: dict = Depends(get_current_user)
):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    cursor = db.claim_events.find({"claim_id": claim_id, "tenant_id": tenant_id}).sort(
        "at", 1
    )
    events = await cursor.to_list(length=100)

    return [
        {
            "event_id": event["_id"],
            "event_type": event["event_type"],
            "description": event["description"],
            "at": event["at"].strftime("%Y-%m-%d"),
            "time": event["time"],
        }
        for event in events
    ]


# ==================== APPOINTMENT ROUTES ====================


@app.get("/api/appointments")
async def list_appointments(
    date: Optional[str] = None,
    provider_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    query = {"tenant_id": tenant_id}
    if provider_id:
        query["provider_id"] = provider_id
    if patient_id:
        query["patient_id"] = patient_id

    if date == "today":
        today = datetime.now(timezone.utc).date()
        query["starts_at"] = {
            "$gte": datetime.combine(today, datetime.min.time()),
            "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()),
        }
    elif date:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        query["starts_at"] = {
            "$gte": datetime.combine(date_obj, datetime.min.time()),
            "$lt": datetime.combine(date_obj + timedelta(days=1), datetime.min.time()),
        }

    cursor = db.appointments.find(query).sort("starts_at", 1).limit(limit)
    appointments = await cursor.to_list(length=limit)

    # Get all unique patient IDs
    patient_ids = list(set(apt["patient_id"] for apt in appointments))

    # Batch fetch all patients
    patients_cursor = db.patients.find({"_id": {"$in": patient_ids}})
    patients_list = await patients_cursor.to_list(length=len(patient_ids))
    patients_map = {p["_id"]: p for p in patients_list}

    # Build result with patient data from map
    result = []
    for apt in appointments:
        patient = patients_map.get(apt["patient_id"])
        result.append(
            {
                "appointment_id": apt["_id"],
                "patient_name": (
                    f"{patient['first_name']} {patient['last_name']}"
                    if patient
                    else "Unknown"
                ),
                "provider_name": "Dr. James O'Brien",
                "type": apt["type"],
                "time": apt["starts_at"].strftime("%I:%M %p"),
                "starts_at": apt["starts_at"],
                "ends_at": apt["ends_at"],
                "status": apt["status"],
                "location": apt.get("location"),
                "title": apt.get("title"),
            }
        )

    return result


@app.post("/api/appointments")
async def create_appointment(
    appointment_data: AppointmentCreate, current_user: dict = Depends(get_current_user)
):
    from database import get_client

    db = get_db()
    client = get_client()
    tenant_id = current_user["tenant_id"]

    appointment_id = str(uuid.uuid4())

    appointment = {
        "_id": appointment_id,
        "tenant_id": tenant_id,
        "patient_id": appointment_data.patient_id,
        "provider_id": appointment_data.provider_id,
        "type": appointment_data.type,
        "title": appointment_data.title,
        "starts_at": appointment_data.starts_at,
        "ends_at": appointment_data.ends_at,
        "location": appointment_data.location,
        "status": "scheduled",
        "google_calendar": {
            "event_id": f"mock-event-{appointment_id[:8]}",
            "calendar_id": "primary",
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    # Use transaction to ensure atomicity
    async with await client.start_session() as session:
        async with session.start_transaction():
            await db.appointments.insert_one(appointment, session=session)
            await db.patients.update_one(
                {"_id": appointment_data.patient_id},
                {"$inc": {"appointments_count": 1}},
                session=session,
            )

    # Broadcast event
    await broadcast_event(
        tenant_id,
        "appointment",
        "insert",
        {"appointment_id": appointment_id, "patient_id": appointment_data.patient_id},
    )

    return {
        "appointment_id": appointment_id,
        "google_calendar": {
            "event_id": appointment["google_calendar"]["event_id"],
            "event_link": f"https://calendar.google.com/event?eid={appointment_id[:10]}",
        },
        "message": "Appointment created successfully",
    }


# ==================== DASHBOARD ROUTES ====================


@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    db = get_db()
    tenant_id = current_user["tenant_id"]

    pending_tasks = await db.tasks.count_documents(
        {"tenant_id": tenant_id, "state": TaskState.OPEN}
    )

    today = datetime.now(timezone.utc).date()
    appointments_today = await db.appointments.count_documents(
        {
            "tenant_id": tenant_id,
            "starts_at": {
                "$gte": datetime.combine(today, datetime.min.time()),
                "$lt": datetime.combine(today + timedelta(days=1), datetime.min.time()),
            },
        }
    )

    patients_total = await db.patients.count_documents({"tenant_id": tenant_id})

    claims_pending = await db.claims.count_documents(
        {"tenant_id": tenant_id, "status": ClaimStatus.PENDING}
    )

    return {
        "pending_tasks": pending_tasks,
        "appointments_today": appointments_today,
        "patients_total": patients_total,
        "claims_pending": claims_pending,
    }


# ==================== WEBSOCKET ROUTE ====================


@app.websocket("/ws/tenant/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str):
    await manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Handle subscriptions if needed
            message = json.loads(data)
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        await manager.disconnect(websocket, tenant_id)


# ==================== COPILOT ENDPOINT ====================


@app.post("/api/copilot")
async def copilot_endpoint(request: dict):
    """Simple CopilotKit endpoint"""
    return {
        "response": "I'm here to help with BacklineMD. How can I assist you today?",
        "context": "Dashboard",
    }
