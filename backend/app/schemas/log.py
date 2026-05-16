from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class LogCreate(BaseModel):
    workflow_id: UUID
    task_id: Optional[UUID] = None
    level: str = "info"
    message: str

class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    task_id: Optional[UUID]
    level: str
    message: str
    created_at: datetime
