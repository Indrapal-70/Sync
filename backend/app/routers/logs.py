from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database.session import get_db
from app.models.workflow_log import WorkflowLog
from app.schemas.log import LogCreate, LogResponse
from app.services.redis_client import publish_event
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/logs", tags=["Logs"])

@router.get("", response_model=List[LogResponse])
def get_logs(
    workflow_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(WorkflowLog)
    if workflow_id:
        query = query.filter(WorkflowLog.workflow_id == workflow_id)
    return query.order_by(WorkflowLog.created_at.desc()).limit(limit).all()

@router.post("", response_model=LogResponse)
def create_log_entry(log_in: LogCreate, db: Session = Depends(get_db)):
    log = WorkflowLog(
        id=uuid.uuid4(),
        workflow_id=log_in.workflow_id,
        task_id=log_in.task_id,
        level=log_in.level,
        message=log_in.message,
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
