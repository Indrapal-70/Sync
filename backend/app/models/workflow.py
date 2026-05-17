import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
