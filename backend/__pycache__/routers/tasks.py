from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from typing import List
from datetime import date
from backend.database import get_db
from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.models.task import DailyTask, TaskSubmission
from backend.services.task_service import task_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/daily")
async def get_daily_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get today's tasks — generates fresh ones via AI if none exist for today."""
    today = date.today()
    existing = db.query(DailyTask).filter(
        DailyTask.is_random_event == False,
        cast(DailyTask.created_at, Date) == today
    ).all() if hasattr(DailyTask, 'created_at') else db.query(DailyTask).filter(DailyTask.is_random_event == False).all()

    if not existing:
        tasks = await task_service.generate_daily_tasks(db, current_user.id)
        return tasks

    # Optionally add a random event task
    event_task = db.query(DailyTask).filter(
        DailyTask.is_random_event == True,
        cast(DailyTask.created_at, Date) == today
    ).first() if hasattr(DailyTask, 'created_at') else None

    if not event_task:
        new_event = await task_service.generate_random_event_task(db, current_user.id)
        if new_event:
            existing.append(new_event)

    return existing

@router.post("/submit")
async def submit_task(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task_id = data.get("task_id")
    code = data.get("code")

    if not task_id or not code:
        raise HTTPException(status_code=400, detail="Task ID and code are required")

    result = await task_service.grade_submission(db, current_user.id, task_id, code)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

@router.get("/history")
async def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(TaskSubmission).filter(TaskSubmission.user_id == current_user.id).all()
