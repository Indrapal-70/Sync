from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database.session import get_db
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.redis_client import publish_event
from app.services.log_service import create_log
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.post("", response_model=TaskResponse)
def create_task(task_in: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        id=uuid.uuid4(),
        workflow_id=task_in.workflow_id,
        name=task_in.name,
        description=task_in.description,
        agent_name=task_in.agent_name,
        input_data=task_in.input_data,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    publish_event("task_created", {
        "id": str(task.id),
        "workflow_id": str(task.workflow_id),
        "name": task.name,
        "status": task.status
    })
    create_log(db, task.workflow_id, f"Task '{task.name}' created", "info", task.id)
    return task

@router.get("", response_model=List[TaskResponse])
def get_tasks(workflow_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if workflow_id:
        query = query.filter(Task.workflow_id == workflow_id)
    return query.order_by(Task.created_at.asc()).all()

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, task_in: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    old_status = task.status
    update_data = task_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
        
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    publish_event("task_updated", {
        "id": str(task.id),
        "workflow_id": str(task.workflow_id),
        "status": task.status,
        "name": task.name,
        "output_data": task.output_data
    })
    
    if old_status != task.status:
        if task.status == "running":
            create_log(db, task.workflow_id, f"Task '{task.name}' is now running", "info", task.id)
        elif task.status == "completed":
            create_log(db, task.workflow_id, f"Task '{task.name}' completed successfully", "info", task.id)
        elif task.status == "failed":
            create_log(db, task.workflow_id, f"Task '{task.name}' failed", "error", task.id)
            
    return task

@router.delete("/{task_id}")
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}
