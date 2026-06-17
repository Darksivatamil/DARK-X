from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from backend.database import Base

class ModuleChain(Base):
    __tablename__ = "module_chains"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String)
    description = Column(Text, default="")
    steps = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChainExecution(Base):
    __tablename__ = "chain_executions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    chain_id = Column(Integer, index=True)
    target = Column(String)
    results = Column(JSON, default=list)
    status = Column(String, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
