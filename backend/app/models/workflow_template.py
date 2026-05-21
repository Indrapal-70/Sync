import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON

from app.database.session import Base

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # JSON array representing the predefined tasks in this template
    # Example: [{"name": "Task 1", "agent_name": "coder", "description": "...", "dependencies": []}]
    tasks_schema = Column(JSON, nullable=False, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
