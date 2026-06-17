from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from backend.database import Base

class SimulationMatch(Base):
    __tablename__ = "simulation_matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scenario = Column(String)
    scenario_title = Column(String)
    scenario_description = Column(Text, default="")
    status = Column(String, default="in_progress")
    current_round = Column(Integer, default=0)
    max_rounds = Column(Integer, default=7)
    red_score = Column(Integer, default=0)
    blue_score = Column(Integer, default=0)
    red_kills = Column(Integer, default=0)
    blue_kills = Column(Integer, default=0)
    red_agents_json = Column(JSON, default=list)
    blue_agents_json = Column(JSON, default=list)
    round_history_json = Column(JSON, default=list)
    winner = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

class AgentStats(Base):
    __tablename__ = "agent_stats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_name = Column(String)
    team = Column(String)
    attack = Column(Integer, default=50)
    defense = Column(Integer, default=50)
    speed = Column(Integer, default=50)
    special = Column(Integer, default=30)
    hp = Column(Integer, default=100)
    max_hp = Column(Integer, default=100)
    xp = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    kills = Column(Integer, default=0)
    level = Column(Integer, default=1)
    special_move = Column(String, default="")
    special_move_unlocked = Column(String, default="")
