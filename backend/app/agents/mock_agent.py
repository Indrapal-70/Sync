import asyncio
import random
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.workflow import Workflow
from app.services.log_service import create_log
from app.services.redis_client import publish_event
from datetime import datetime

async def run_mock_agent(workflow_id: UUID, db: Session):
    """
    Simulates an AI agent running through workflow tasks.
    Updates statuses and logs in real time via WebSocket.
    """
    # Set workflow to running
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id).first()
    if not workflow:
        return

    workflow.status = "running"
    workflow.updated_at = datetime.utcnow()
    db.commit()
    publish_event("workflow_updated", {
        "id": str(workflow.id),
        "status": "running"
    })
    create_log(db, workflow_id,
        f"Workflow '{workflow.name}' started execution", "info")

    # Get all tasks for this workflow
    tasks = db.query(Task).filter(
        Task.workflow_id == workflow_id
    ).order_by(Task.created_at.asc()).all()

    all_passed = True

    for task in tasks:
        # Mark task as running
        task.status = "running"
        task.updated_at = datetime.utcnow()
        db.commit()
        publish_event("task_updated", {
            "id": str(task.id),
            "workflow_id": str(task.workflow_id),
            "status": "running",
            "name": task.name
        })
        create_log(db, workflow_id,
            f"Agent starting task: {task.name}", "info", task.id)

        # Simulate work with realistic delay (2-5 seconds per task)
        work_duration = random.uniform(2, 5)
        steps = int(work_duration * 2)
        for i in range(steps):
            await asyncio.sleep(0.5)
            progress = int(((i + 1) / steps) * 100)
            # Log progress every few steps
            if i % 3 == 0:
                create_log(db, workflow_id,
                    f"[{task.name}] Processing... {progress}% complete",
                    "debug", task.id)

        # 85% chance of success, 15% chance of failure
        success = random.random() > 0.15

        if success:
            task.status = "completed"
            task.output_data = {
                "result": "success",
                "execution_time_ms": int(work_duration * 1000)
            }
            create_log(db, workflow_id,
                f"Task '{task.name}' completed successfully",
                "info", task.id)
        else:
            task.status = "failed"
            task.output_data = {"error": "Simulated agent failure"}
            create_log(db, workflow_id,
                f"Task '{task.name}' failed - retrying not implemented yet",
                "error", task.id)
            all_passed = False

        task.updated_at = datetime.utcnow()
        db.commit()
        publish_event("task_updated", {
            "id": str(task.id),
            "workflow_id": str(task.workflow_id),
            "status": task.status,
            "name": task.name,
            "output_data": task.output_data
        })

        # Short pause between tasks
        await asyncio.sleep(0.5)

    # Set final workflow status
    final_status = "completed" if all_passed else "failed"
    workflow.status = final_status
    workflow.updated_at = datetime.utcnow()
    db.commit()
    publish_event("workflow_updated", {
        "id": str(workflow.id),
        "status": final_status
    })
    create_log(db, workflow_id,
        f"Workflow '{workflow.name}' {final_status}", "info")
