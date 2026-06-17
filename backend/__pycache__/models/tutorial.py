from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from backend.database import Base

class Tutorial(Base):
    __tablename__ = "tutorials"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    tool = Column(String, index=True)
    description = Column(Text)
    difficulty = Column(String, default="Beginner")
    xp_reward = Column(Integer, default=100)
    steps = Column(JSON, default=list)
    commands = Column(JSON, default=list)
    expected_output = Column(Text, default="")
    tags = Column(JSON, default=list)
    icon = Column(String, default="📚")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TutorialProgress(Base):
    __tablename__ = "tutorial_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tutorial_id = Column(Integer, index=True)
    current_step = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    xp_earned = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
