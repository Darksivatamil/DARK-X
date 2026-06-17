from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.sql import func
from backend.database import Base

class DailyTask(Base):
    __tablename__ = "daily_tasks"
    id = Column(Integer, primary_key=True, index=True)
    track = Column(String)
    difficulty = Column(String)
    difficulty_score = Column(Float, default=1.0)
    title = Column(String)
    description = Column(Text)
    based_on = Column(String, default="")
    full_question = Column(Text, default="")
    what_wanted = Column(Text, default="")
    what_we_learn = Column(Text, default="")
    time_estimate = Column(String, default="30 min")
    ease_rating = Column(String, default="Medium")
    powers_reward = Column(String, default="")
    xp_reward = Column(Integer, default=100)
    learning_objectives = Column(Text, default="")
    tags = Column(JSON, default=list)
    is_random_event = Column(Boolean, default=False)
    event_name = Column(String, default="")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TaskSubmission(Base):
    __tablename__ = "task_submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("daily_tasks.id"))
    submitted_code = Column(Text)
    score = Column(Float)
    feedback = Column(Text)
    xp_earned = Column(Integer)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
