from fastapi import APIRouter, Depends, HTTPException
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
        status="pending",
        agent_name=task_in.agent_name,
        input_data=task_in.input_data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    task_dict = TaskResponse.model_validate(task).model_dump(mode='json')
    publish_event("task_created", task_dict)
    create_log(
        db,
        task.workflow_id,
        f"Task '{task.name}' created",
        "info",
        task.id,
        agent_name=task.agent_name,
        pipeline_stage=task.pipeline_stage,
    )
    
    return task

@router.get("", response_model=List[TaskResponse])
def get_tasks(workflow_id: Optional[UUID] = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if workflow_id:
        query = query.filter(Task.workflow_id == workflow_id)
    tasks = query.order_by(Task.created_at.asc()).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.model_dump(exclude_unset=True)
    status_changed_to = update_data.get("status") if update_data.get("status") != task.status else None
    
    for key, value in update_data.items():
        setattr(task, key, value)
        
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    
    task_dict = TaskResponse.model_validate(task).model_dump(mode='json')
    publish_event("task_updated", task_dict)
    
    if status_changed_to == "running":
        create_log(
            db,
            task.workflow_id,
            f"Task '{task.name}' is now running",
            "info",
            task.id,
            agent_name=task.agent_name,
            pipeline_stage=task.pipeline_stage,
        )
    elif status_changed_to == "completed":
        create_log(
            db,
            task.workflow_id,
            f"Task '{task.name}' completed successfully",
            "info",
            task.id,
            agent_name=task.agent_name,
            pipeline_stage=task.pipeline_stage,
        )
    elif status_changed_to == "failed":
        create_log(
            db,
            task.workflow_id,
            f"Task '{task.name}' failed",
            "error",
            task.id,
            agent_name=task.agent_name,
            pipeline_stage=task.pipeline_stage,
        )
        
    return task

@router.get("/{task_id}/agent-output")
def get_agent_output(task_id: UUID, db: Session = Depends(get_db)):
    """
    P7-01: Return the full agent_output JSON for a task.
    Contains the raw results from each agent that processed this task
    (coder, tester, debugger, reviewer), including model_used metadata.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "task_id": str(task.id),
        "task_name": task.name,
        "status": task.status,
        "pipeline_stage": task.pipeline_stage,
        "agent_output": task.agent_output or {},
        "output_data": task.output_data or {},
    }


@router.delete("/{task_id}")
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    publish_event("task_deleted", {"id": str(task_id)})
    return {"message": "Task deleted"}
