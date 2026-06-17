from fastapi import APIRouter, Depends
from backend.routers.auth import get_current_user
from backend.models.user import User
from backend.services.dao_service import shadow_dao

router = APIRouter(prefix="/api/dao", tags=["dao"])

@router.get("/my-id")
async def get_my_did(current_user: User = Depends(get_current_user)):
    did = shadow_dao.get_did_by_user(current_user.id)
    if not did:
        did = shadow_dao.register_did(current_user.id, current_user.username)
    
    ledger = shadow_dao._read_ledger()
    return {
        "did": did,
        "profile": ledger["identities"][did]
    }

@router.post("/guild/join")
async def join_guild(guild_name: str, current_user: User = Depends(get_current_user)):
    did = shadow_dao.get_did_by_user(current_user.id)
    if not did:
        did = shadow_dao.register_did(current_user.id, current_user.username)
    
    shadow_dao.join_guild(did, guild_name)
    return {"message": f"Joined guild {guild_name} successfully."}
