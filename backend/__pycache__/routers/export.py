from fastapi import APIRouter, Depends, BackgroundTasks, Query, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os, json
from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.models.progress import UserProgress
from backend.services.export_service import export_service
from backend.database import get_db
from sqlalchemy.orm import Session
from backend.utils.security import decode_access_token

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/report/pdf")
async def export_pdf(token: str = Query(None), db: Session = Depends(get_db)):
    current_user = None
    if token:
        payload = decode_access_token(token)
        if payload:
            username = payload.get("sub")
            current_user = db.query(User).filter(User.username == username).first()
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    data = {
        "Username": current_user.username,
        "Email": current_user.email or "N/A",
        "Level": str(progress.overall_level) if progress else "1",
        "Rank": progress.current_rank if progress else "Shadow Initiate",
        "Total XP": str(progress.total_xp) if progress else "0",
        "Powers Unlocked": str(len(progress.powers_unlocked)) if progress else "0",
        "Tasks Completed": str(progress.tasks_completed) if progress else "0",
        "Status": "Active"
    }
    file_path = f"exports/report_{current_user.id}.pdf"
    os.makedirs("exports", exist_ok=True)
    
    export_service.generate_pdf_report(current_user.id, data, file_path)
    return FileResponse(file_path, media_type='application/pdf', filename="darkx_report.pdf")

@router.get("/backup/json")
async def export_json(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    data = {
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "created_at": str(current_user.created_at) if current_user.created_at else None,
        },
        "progress": {
            "level": progress.overall_level if progress else 1,
            "xp": progress.total_xp if progress else 0,
            "rank": progress.current_rank if progress else "Shadow Initiate",
            "powers_unlocked": progress.powers_unlocked if progress else [],
            "tasks_completed": progress.tasks_completed if progress else 0,
            "streak_days": progress.streak_days if progress else 0,
        } if progress else {},
        "settings": current_user.settings or {}
    }
    return JSONResponse(content=data)
