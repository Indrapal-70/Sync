import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    workflow_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True
    )
    task_id = Column(PG_UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True, index=True)
    level = Column(String, nullable=False, default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
