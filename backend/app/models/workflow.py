from sqlalchemy import Column, String, Integer
from app.models.base import Base

class Workflow(Base):
    __tablename__ = 'workflows'
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
