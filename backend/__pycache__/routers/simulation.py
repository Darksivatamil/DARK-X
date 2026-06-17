from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.database import get_db
from backend.models.user import User
from backend.routers.auth import get_current_user
from backend.services.simulation_service import simulation_service

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/scenarios")
async def get_scenarios():
    return simulation_service.get_scenarios()


@router.get("/agents")
async def get_agent_definitions():
    return simulation_service.get_agent_definitions(include_overlord=True)


@router.post("/start")
async def start_match(data: Dict[str, str],
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    scenario = data.get('scenario', '')
    if not scenario:
        raise HTTPException(status_code=400, detail="Scenario is required")
    try:
        match = await simulation_service.create_match(db, current_user.id, scenario)
        return simulation_service.get_match(db, match.id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{match_id}/round")
async def run_round(match_id: int,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    result = await simulation_service.run_round(db, match_id, current_user.id)
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.get("/{match_id}")
async def get_match(match_id: int,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    match = simulation_service.get_match(db, match_id, current_user.id)
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.post("/agent/upgrade")
async def upgrade_agent_standalone(data: Dict[str, Any],
                                   current_user: User = Depends(get_current_user),
                                   db: Session = Depends(get_db)):
    agent_name = data.get('agent_name', '')
    stat = data.get('stat', '')
    if not agent_name or not stat:
        raise HTTPException(status_code=400, detail="agent_name and stat are required")
    result = simulation_service.upgrade_agent(db, current_user.id, agent_name, stat)
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.post("/{match_id}/upgrade")
async def upgrade_agent(match_id: int,
                        data: Dict[str, Any],
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    agent_name = data.get('agent_name', '')
    stat = data.get('stat', '')
    if not agent_name or not stat:
        raise HTTPException(status_code=400, detail="agent_name and stat are required")
    result = simulation_service.upgrade_agent(db, current_user.id, agent_name, stat)
    if 'error' in result:
        raise HTTPException(status_code=400, detail=result['error'])
    return result


@router.get("/history/list")
async def get_history(limit: int = 10,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return simulation_service.get_match_history(db, current_user.id, limit)


@router.get("/stats/list")
async def get_agent_stats(current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    return simulation_service.get_agent_stats(db, current_user.id)
