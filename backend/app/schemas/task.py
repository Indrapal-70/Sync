from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class TaskCreate(BaseModel):
    workflow_id: UUID
    name: str
    description: Optional[str] = None
    agent_name: Optional[str] = None
    input_data: Optional[dict] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    output_data: Optional[dict] = None
    agent_name: Optional[str] = None

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    name: str
    description: Optional[str]
    status: str
    agent_name: Optional[str]
    input_data: Optional[dict]
    output_data: Optional[dict]
    current_agent: Optional[str] = None
    pipeline_stage: Optional[str] = None
    retry_count: int = 0
    agent_output: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
