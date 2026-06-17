from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from backend.database import Base

class ApiProvider(Base):
    __tablename__ = "api_providers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String, default="OpenAI")
    provider_type = Column(String, default="openai")
    api_key = Column(Text, default="")
    model_name = Column(String, default="gpt-4")
    base_url = Column(String, default="https://api.openai.com/v1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
