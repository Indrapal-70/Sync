from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database.session import get_db
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowResponse
from app.services.redis_client import publish_event
from app.services.log_service import create_log
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])

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
