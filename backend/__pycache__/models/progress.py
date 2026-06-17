from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from backend.database import Base

class UserProgress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    
    overall_level = Column(Integer, default=1)
    total_xp = Column(Integer, default=0)
    
    python_level = Column(Integer, default=1)
    python_xp = Column(Integer, default=0)
    
    kali_level = Column(Integer, default=1)
    kali_xp = Column(Integer, default=0)
    
    ai_level = Column(Integer, default=1)
    ai_xp = Column(Integer, default=0)
    
    industry_level = Column(Integer, default=1)
    industry_xp = Column(Integer, default=0)
    
    powers_unlocked = Column(JSON, default=[]) # Array of power IDs
    current_rank = Column(String, default="Shadow Initiate")
    
    streak_days = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_submitted = Column(Integer, default=0)
