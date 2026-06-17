from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, default="", index=True)
    password_hash = Column(String, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    total_login_time = Column(Integer, default=0)
    
    api_keys = Column(JSON, default={})
    settings = Column(JSON, default={})
    is_online = Column(Boolean, default=False)
