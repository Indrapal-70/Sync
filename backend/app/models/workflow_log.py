from sqlalchemy import Column, String, Integer
from app.models.base import Base

class WorkflowLog(Base):
    __tablename__ = 'workflow_logs'
    id = Column(String, primary_key=True, index=True)
    message = Column(String)
