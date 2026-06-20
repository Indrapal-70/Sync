from uuid import uuid4
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class HealingEvent(Base):
    __tablename__ = "healing_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(String, index=True, nullable=False)
    cycle = Column(Integer, nullable=False)
    failed_agent = Column(String, nullable=False)
    error_summary = Column(Text, nullable=True)        # truncate to 500 chars before insert
    injected_node_ids = Column(JSON, nullable=False, default=list)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
