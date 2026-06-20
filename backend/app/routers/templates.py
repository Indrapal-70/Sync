from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.database.session import get_db
from app.models.workflow_template import WorkflowTemplate

router = APIRouter(prefix="/api/templates", tags=["Templates"])
router_v1 = APIRouter(prefix="/api/v1/templates", tags=["Templates"])

class TaskSchema(BaseModel):
    name: str
    description: str
    agent_name: Optional[str] = None
    agent_hint: Optional[str] = None
    priority: int = 1
    dependencies: List[str] = []
    node_id: Optional[str] = None
    expected_output: Optional[str] = None
    max_retries_override: Optional[int] = None

class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tasks_schema: List[TaskSchema]
    category: Optional[str] = "custom"
    model_hints: Optional[dict] = {}
    source: Optional[str] = None
    version: Optional[str] = "1.0.0"
    parent_template_id: Optional[str] = None
    is_public: Optional[bool] = False
    tags: Optional[List[str]] = []
    author: Optional[str] = None

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tasks_schema: List[TaskSchema]
    version: str
    parent_template_id: Optional[str] = None
    is_public: bool
    tags: Optional[List[str]] = []
    author: Optional[str] = None
    usage_count: int
    
    class Config:
        from_attributes = True

class TemplatePublish(BaseModel):
    tags: Optional[List[str]] = None

class TemplateFork(BaseModel):
    name: Optional[str] = None
    author: Optional[str] = None

@router.get("/", response_model=List[TemplateResponse])
@router_v1.get("/", response_model=List[TemplateResponse])
def get_templates(db: Session = Depends(get_db)):
    """List all workflow templates."""
    return db.query(WorkflowTemplate).order_by(WorkflowTemplate.created_at.desc()).all()

@router.post("/", response_model=TemplateResponse)
@router_v1.post("/", response_model=TemplateResponse)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """Create a new workflow template."""
    db_template = WorkflowTemplate(
        name=template.name,
        description=template.description,
        tasks_schema=[task.model_dump() for task in template.tasks_schema],
        version=template.version or "1.0.0",
        parent_template_id=template.parent_template_id,
        is_public=template.is_public or False,
        tags=template.tags or [],
        author=template.author,
        usage_count=0
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/marketplace", response_model=List[TemplateResponse])
@router_v1.get("/marketplace", response_model=List[TemplateResponse])
def get_marketplace_templates(db: Session = Depends(get_db)):
    """List all public templates."""
    return db.query(WorkflowTemplate).filter(WorkflowTemplate.is_public == True).order_by(WorkflowTemplate.created_at.desc()).all()

@router.get("/{template_id}", response_model=TemplateResponse)
@router_v1.get("/{template_id}", response_model=TemplateResponse)
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Get a specific template by ID."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.delete("/{template_id}")
@router_v1.delete("/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Delete a workflow template."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    db.delete(template)
    db.commit()
    return {"status": "deleted"}

@router.post("/{template_id}/publish", response_model=TemplateResponse)
@router_v1.post("/{template_id}/publish", response_model=TemplateResponse)
def publish_template(template_id: str, payload: Optional[TemplatePublish] = None, db: Session = Depends(get_db)):
    """Publish a template to the marketplace."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.is_public = True
    if payload and payload.tags is not None:
        template.tags = payload.tags
    db.commit()
    db.refresh(template)
    return template

@router.post("/{template_id}/fork", response_model=TemplateResponse)
@router_v1.post("/{template_id}/fork", response_model=TemplateResponse)
def fork_template(template_id: str, payload: Optional[TemplateFork] = None, db: Session = Depends(get_db)):
    """Fork a template to create a new template."""
    parent = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Template not found")
    
    fork_name = (payload.name if payload and payload.name) else f"Fork of {parent.name}"
    fork_author = payload.author if payload else None
    
    fork = WorkflowTemplate(
        name=fork_name,
        description=parent.description,
        tasks_schema=parent.tasks_schema,
        version="1.0.0",
        parent_template_id=parent.id,
        is_public=False,
        tags=parent.tags,
        author=fork_author,
        usage_count=0
    )
    db.add(fork)
    db.commit()
    db.refresh(fork)
    return fork

@router.post("/{template_id}/use", response_model=TemplateResponse)
@router_v1.post("/{template_id}/use", response_model=TemplateResponse)
def use_template(template_id: str, db: Session = Depends(get_db)):
    """Increment template usage count."""
    template = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    template.usage_count += 1
    db.commit()
    db.refresh(template)
    return template

