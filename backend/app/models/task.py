from sqlalchemy import Column, String, Integer
from app.models.base import Base

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True, index=True)
    title = Column(String)
    workflow_id = Column(String)
