from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from backend.database import Base

class ModuleRun(Base):
    __tablename__ = "module_runs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_id = Column(String, index=True)
    target = Column(String)
    options = Column(JSON, default=dict)
    output = Column(Text)
    ai_analysis = Column(Text, default="")
    score = Column(Float, default=0.0)
    status = Column(String, default="completed")
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
