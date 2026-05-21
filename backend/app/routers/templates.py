from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database.session import get_db
from app.models.workflow_template import WorkflowTemplate

router = APIRouter(prefix="/api/templates", tags=["Templates"])

class TaskSchema(BaseModel):
    name: str
    description: str
    agent_name: str
    priority: int
    dependencies: List[str]

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tasks_schema: List[TaskSchema]

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tasks_schema: List[TaskSchema]
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[TemplateResponse])
def get_templates(db: Session = Depends(get_db)):
    """List all workflow templates."""
    return db.query(WorkflowTemplate).order_by(WorkflowTemplate.created_at.desc()).all()

@router.post("/", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new workflow template."""
    db_template = WorkflowTemplate(
        name=template.name,
        description=template.description,
        tasks_schema=[task.model_dump() for task in template.tasks_schema]
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a specific template by ID."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.delete("/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete a workflow template."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"status": "deleted"}
