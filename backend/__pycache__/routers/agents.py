from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from backend.agents.agent_bus import agent_bus
from backend.agents.agent_registry import init_agents
from backend.utils.security import decode_access_token
from backend.services.ai_service import ai_service, AGENT_PERSONALITIES
from backend.services.memory_service import memory_service
from backend.config import logger
from backend.database import get_db
from backend.models.user import User
from backend.models.progress import UserProgress
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/api/agents", tags=["agents"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

@router.on_event("startup")
async def startup_agents():
    init_agents()
    logger.info("AI Agents initialized and registered.")

@router.post("/chat")
async def agent_chat(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    agent = data.get('agent', 'shadow').lower()
    message = data.get('message', '')
    agent_key = agent.lower()
    agent_info = AGENT_PERSONALITIES.get(agent_key, AGENT_PERSONALITIES['default'])

    # Get memory context
    working_mem = await memory_service.get_working_memory(current_user.id, agent_key)
    long_term_mem = memory_service.load_long_term_memory(current_user.id)
    experiences = "\n".join([e["event"] for e in long_term_mem["experiences"][-5:]])

    progress = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).first()
    user_context = f"User Level: {progress.overall_level if progress else 1}, Rank: {progress.current_rank if progress else 'Shadow Initiate'}"

    system_prompt = (
        f"{agent_info['system_prompt']}\n\n"
        f"USER CONTEXT:\n{user_context}\n"
        f"USER MEMORY:\n{experiences}\n"
        f"Respond in character as {agent_info['name']}, the {agent_info['role']}."
    )

    if ai_service.is_available():
        response = await ai_service.generate_response(system_prompt, message, working_mem)
    else:
        response = f"{agent_info['name']} online. AI neural core not initialized — configure API keys in Settings for intelligent responses."

    # Store in memory
    await memory_service.add_to_working_memory(current_user.id, agent_key, "user", message)
    await memory_service.add_to_working_memory(current_user.id, agent_key, "assistant", response)

    return {'reply': response, 'agent': agent}

@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        token_data = await websocket.receive_text()
        token = token_data.replace("Bearer ", "")
        payload = decode_access_token(token)

        if not payload:
            await websocket.send_text("System Error: Unauthorized. Connection closed.")
            await websocket.close()
            return

        user_id = payload.get("user_id", 1)
        username = payload.get("sub", "Shadow")

        await websocket.send_text(f"S-SYSTEM: Neural link established, {username}. Terminal ready.")

        while True:
            data = await websocket.receive_text()

            if data == "/arise":
                responses = await agent_bus.arise(user_id)
                for res in responses:
                    await websocket.send_text(res)

            elif data == "/rest":
                responses = await agent_bus.rest(user_id)
                for res in responses:
                    await websocket.send_text(res)

            elif data == "/status":
                await websocket.send_text("S-SYSTEM STATUS: All agents operational. Neural Link: Stable. Memory: 98% Optimized.")

            elif data.startswith("/stats"):
                from backend.database import SessionLocal
                db = SessionLocal()
                try:
                    progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
                    level = progress.overall_level if progress else 1
                    xp = progress.total_xp if progress else 0
                    rank = progress.current_rank if progress else 'Shadow Initiate'
                    await websocket.send_text(f"CURRENT STATS: Level {level} | Rank: {rank} | Total XP: {xp} | Streak: 0 Days")
                finally:
                    db.close()

            elif data.startswith("/power"):
                from backend.database import SessionLocal
                db = SessionLocal()
                try:
                    progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
                    unlocked = progress.powers_unlocked if progress else []
                    if unlocked:
                        await websocket.send_text(f"UNLOCKED POWERS ({len(unlocked)}): {', '.join(unlocked[:5])}{'...' if len(unlocked) > 5 else ''}")
                    else:
                        await websocket.send_text("UNLOCKED POWERS: [None] - Increase your level to unlock shadow abilities.")
                finally:
                    db.close()

            elif data == "/daily":
                await websocket.send_text("DAILY QUESTS: Available. Navigate to the Tasks tab to begin your trial.")

            elif data.startswith("/"):
                agent_name = data[1:]
                if agent_name.lower() in agent_bus.agents:
                    intro = await agent_bus.agents[agent_name.lower()].activate(user_id)
                    await websocket.send_text(f"{agent_name.upper()}: {intro}")
                elif agent_name.lower() in AGENT_PERSONALITIES:
                    info = AGENT_PERSONALITIES[agent_name.lower()]
                    await websocket.send_text(f"{info['name']}: {info['system_prompt'][:100]}...")
                else:
                    await websocket.send_text(f"Unknown command: {data}. Type /help for available commands.")

            else:
                response = await agent_bus.route_message("dark-guide-x", data, user_id)
                await websocket.send_text(response)

    except WebSocketDisconnect:
        logger.info("Agent WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
