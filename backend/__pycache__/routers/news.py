from fastapi import APIRouter, Depends
from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.services.news_service import news_service

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("/{category}")
async def get_news(category: str, current_user: User = Depends(get_current_user)):
    if category not in ["hacking", "ai"]:
        return {"error": "Invalid category. Use 'hacking' or 'ai'"}
        
    return await news_service.fetch_latest_news(category)
