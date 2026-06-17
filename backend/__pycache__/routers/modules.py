from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import random, json

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.services.module_service import module_service, TOOL_DEFINITIONS
from backend.services.ai_service import ai_service

router = APIRouter(prefix="/api/modules", tags=["modules"])

@router.get("/list")
async def list_modules(current_user: User = Depends(get_current_user)):
    return module_service.get_all_tools()

@router.get("/{module_id}/options")
async def get_module_options(module_id: str, current_user: User = Depends(get_current_user)):
    tool = module_service.get_tool(module_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")
    return {
        "id": module_id,
        "name": tool['name'],
        "icon": tool['icon'],
        "color": tool['color'],
        "desc": tool['desc'],
        "options": tool['options'],
    }

@router.post("/{module_id}/run")
async def run_module(module_id: str, params: Dict[str, Any],
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    target = params.get("target", "")
    if not target:
        raise HTTPException(status_code=400, detail="Target is required")

    tool = module_service.get_tool(module_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Module '{module_id}' not found")

    # Extract options from params
    options = {k: v for k, v in params.items() if k != 'target'}

    result = await module_service.run(db, current_user.id, module_id, target, options)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result

@router.get("/history")
async def get_module_history(limit: int = Query(20, le=100),
                             current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    return module_service.get_history(db, current_user.id, limit)
