from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database.session import get_db
from app.models.workflow import Workflow
from app.models.task import Task
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from app.services.redis_client import publish_event
from app.services.log_service import create_log
from app.agents.planner_agent import plan_workflow
from app.agents.mock_agent import run_mock_agent
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

def run_mock_agent_sync(workflow_id: UUID, db: Session):
    import asyncio
    asyncio.run(run_mock_agent(workflow_id, db))

@router.post("", response_model=WorkflowResponse)
def create_workflow(workflow_in: WorkflowCreate, db: Session = Depends(get_db)):
    workflow = Workflow(
        id=uuid.uuid4(),
        name=workflow_in.name,
        description=workflow_in.description,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    response_data = {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "created_at": workflow.created_at.isoformat(),
        "updated_at": workflow.updated_at.isoformat()
    }
    
    publish_event("workflow_created", response_data)
    create_log(db, workflow.id, "Workflow created", "info")
    return workflow

@router.get("", response_model=List[WorkflowResponse])
def get_workflows(db: Session = Depends(get_db)):
    return db.query(Workflow).order_by(Workflow.created_at.desc()).all()

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.patch("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: UUID, workflow_in: WorkflowUpdate, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    update_data = workflow_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
        
    workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    
    publish_event("workflow_updated", {
        "id": str(workflow.id),
        **update_data
    })
    
    return workflow

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    db.delete(workflow)
    db.commit()
    
    publish_event("workflow_deleted", {"id": str(workflow_id)})
    return {"message": "Workflow deleted successfully"}

@router.post("/{workflow_id}/execute")
async def execute_workflow(workflow_id: UUID, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    task_plan = await plan_workflow(workflow.description or workflow.name)
    
    for plan in task_plan:
        task = Task(
            id=uuid.uuid4(),
            workflow_id=workflow_id,
            name=plan["name"],
            description=plan.get("description"),
            agent_name=plan.get("agent_name"),
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
            "description": task.description,
            "agent_name": task.agent_name,
            "status": task.status
        })

    background_tasks.add_task(run_mock_agent_sync, workflow_id, db)
    
    return {
        "message": "Workflow execution started",
        "workflow_id": str(workflow_id),
        "tasks_created": len(task_plan)
    }
