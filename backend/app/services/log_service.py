from datetime import datetime
from typing import Optional
from uuid import UUID
import uuid

from app.models.workflow_log import WorkflowLog
from app.services.redis_client import publish_event

def create_log(
    db,
    workflow_id: UUID,
    message: str,
    level: str = "info",
    task_id: Optional[UUID] = None
) -> WorkflowLog:
    log = WorkflowLog(
        id=uuid.uuid4(),
        workflow_id=workflow_id,
        task_id=task_id,
        level=level,
        message=message,
        created_at=datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    publish_event("log_created", {
        "id": str(log.id),
        "workflow_id": str(log.workflow_id),
        "task_id": str(log.task_id) if log.task_id else None,
        "level": log.level,
        "message": log.message,
        "created_at": log.created_at.isoformat()
    })
    return log
