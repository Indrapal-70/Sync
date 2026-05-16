from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database.session import get_db
from app.models.workflow_log import WorkflowLog
from app.schemas.log import LogCreate, LogResponse
from app.services.log_service import create_log

router = APIRouter(prefix="/api/logs", tags=["Logs"])

@router.get("", response_model=List[LogResponse])
def get_logs(workflow_id: Optional[UUID] = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(WorkflowLog)
    if workflow_id:
        query = query.filter(WorkflowLog.workflow_id == workflow_id)
    logs = query.order_by(WorkflowLog.created_at.desc()).limit(limit).all()
    return logs

@router.post("", response_model=LogResponse)
def create_log_entry(log_in: LogCreate, db: Session = Depends(get_db)):
    log = create_log(
        db=db,
        workflow_id=log_in.workflow_id,
        message=log_in.message,
        level=log_in.level,
        task_id=log_in.task_id
    )
    return log
