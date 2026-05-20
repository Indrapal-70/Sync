from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func

from app.models.base import Base


class SkillAssignment(Base):
    __tablename__ = "skill_assignments"

    skill_name = Column(String, primary_key=True)
    model_key  = Column(String, nullable=False)   # "thinker" or "builder"
    model_name = Column(String, nullable=False)   # "mistral:latest" etc.
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    updated_by = Column(String, default="system")
