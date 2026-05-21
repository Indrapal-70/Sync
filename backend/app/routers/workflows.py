from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database.session import get_db
from app.models.workflow import Workflow
from app.models.task import Task
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from app.services.redis_client import publish_event
from app.services.log_service import create_log
from app.agents.pipeline_orchestrator import run_pipeline
from app.agents.planner_agent import plan_workflow
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


def run_pipeline_sync(workflow_id: UUID):
    import asyncio

    from app.database.session import SessionLocal

    db = SessionLocal()
    try:
        asyncio.run(run_pipeline(workflow_id, db))
    finally:
        db.close()

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
    
    workflow_dict = WorkflowResponse.model_validate(workflow).model_dump(mode='json')
    publish_event("workflow_created", workflow_dict)
    create_log(db, workflow.id, "Workflow created", "info")
    
    return workflow

@router.get("", response_model=List[WorkflowResponse])
def get_workflows(db: Session = Depends(get_db)):
    workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
    return workflows

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.patch("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(workflow_id: UUID, workflow_update: WorkflowUpdate, db: Session = Depends(get_db)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    update_data = workflow_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workflow, key, value)
        
    workflow.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workflow)
    
    workflow_dict = WorkflowResponse.model_validate(workflow).model_dump(mode='json')
    publish_event("workflow_updated", workflow_dict)
    
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
async def execute_workflow(
    workflow_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    task_plan = await plan_workflow(workflow.description or workflow.name)
    created_tasks = []
    for item in task_plan:
        task = Task(
            id=uuid.uuid4(),
            workflow_id=workflow_id,
            name=item.get("name", "Untitled Task"),
            description=item.get("description", ""),
            agent_name=item.get("agent_name", "coder"),
            input_data={
                "dependencies": item.get("dependencies", []),
                "priority": item.get("priority", 1),
            },
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        created_tasks.append(task)
        publish_event(
            "task_created",
            {
                "id": str(task.id),
                "name": task.name,
                "workflow_id": str(workflow_id),
                "status": task.status,
                "agent_name": task.agent_name,
                "input_data": task.input_data,
                "output_data": task.output_data,
                "current_agent": task.current_agent,
                "pipeline_stage": task.pipeline_stage,
                "retry_count": task.retry_count,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            },
        )

    background_tasks.add_task(run_pipeline_sync, workflow_id)

    return {
        "message": "Pipeline started",
        "workflow_id": str(workflow_id),
        "tasks_created": len(created_tasks),
    }

@router.post("/{workflow_id}/save-as-template")
def save_workflow_as_template(workflow_id: UUID, db: Session = Depends(get_db)):
    """Convert an existing workflow and its tasks into a reusable template."""
    from app.models.workflow_template import WorkflowTemplate
    
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    tasks = db.query(Task).filter(Task.workflow_id == workflow_id).all()
    if not tasks:
        raise HTTPException(status_code=400, detail="Cannot save a workflow with no tasks as a template")
        
    tasks_schema = []
    for t in tasks:
        tasks_schema.append({
            "name": t.name,
            "description": t.description,
            "agent_name": t.agent_name,
            "priority": t.input_data.get("priority", 1) if t.input_data else 1,
            "dependencies": t.input_data.get("dependencies", []) if t.input_data else []
        })
        
    template = WorkflowTemplate(
        name=f"Template: {workflow.name}",
        description=f"Generated from workflow '{workflow.name}'",
        tasks_schema=tasks_schema
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "message": "Template saved successfully",
        "template_id": template.id,
        "tasks_saved": len(tasks_schema)
    }
