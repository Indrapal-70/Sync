from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class AgentMetric(Base):
    __tablename__ = "agent_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    task_id = Column(String, index=True, nullable=False)
    agent_name = Column(String, index=True, nullable=False)
    step = Column(Integer, nullable=False)
    status = Column(String, nullable=False)            # passed | failed | skipped
    duration_ms = Column(Float, nullable=False)
    healing_cycle = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
