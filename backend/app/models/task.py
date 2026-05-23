import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    workflow_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    agent_name = Column(String, nullable=True)
    node_id = Column(String, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    subtasks = Column(JSON, nullable=True)
    current_agent = Column(String, nullable=True)
    agent_output = Column(JSON, nullable=True)
    test_results = Column(JSON, nullable=True)
    review_results = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    pipeline_stage = Column(String, nullable=True)
    error_log = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
