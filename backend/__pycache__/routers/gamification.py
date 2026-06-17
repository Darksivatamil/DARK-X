from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.services.gamification import gamification_service

router = APIRouter(prefix="/api/gamification", tags=["gamification"])

@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.models.progress import UserProgress
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    return progress

@router.post("/add-xp")
async def add_xp(xp: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = gamification_service.add_xp(db, current_user.id, xp)
    return result

@router.get("/powers")
async def get_powers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.models.progress import UserProgress
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    all_powers = gamification_service.load_powers()
    return {
        "unlocked": progress.powers_unlocked if progress else [],
        "all_powers": all_powers
    }

@router.get("/events")
async def get_events(current_user: User = Depends(get_current_user)):
    events = gamification_service.load_events()
    return {"events": events}

@router.post("/reset")
async def reset_progress(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from backend.models.progress import UserProgress
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    if progress:
        progress.overall_level = 1
        progress.total_xp = 0
        progress.powers_unlocked = []
        progress.current_rank = "Shadow Initiate"
        progress.python_level = 1
        progress.kali_level = 1
        progress.ai_level = 1
        progress.industry_level = 1
        progress.tasks_completed = 0
        progress.streak_days = 0
        db.commit()
    return {"message": "Progress reset successfully"}
