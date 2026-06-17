import asyncio
from typing import Dict, List, Optional
from backend.agents.base_agent import BaseAgent
from backend.config import logger


class AgentBus:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.active_sessions: Dict[int, List[str]] = {}

    def register_agent(self, agent: BaseAgent):
        name = agent.name.lower()
        if name in self.agents:
            logger.info(f"Agent {agent.name} already registered. Skipping.")
            return
        self.agents[name] = agent
        logger.info(f"Agent {agent.name} registered on the bus.")

    async def arise(self, user_id: int) -> List[str]:
        responses = []
        self.active_sessions[user_id] = []
        for name, agent in self.agents.items():
            msg = await agent.activate(user_id)
            responses.append(f"{agent.name}: {msg}")
            self.active_sessions[user_id].append(name)
            await asyncio.sleep(0.5)
        return responses

    async def rest(self, user_id: int) -> List[str]:
        responses = []
        if user_id in self.active_sessions:
            for name in self.active_sessions[user_id]:
                agent = self.agents.get(name)
                if agent:
                    responses.append(await agent.deactivate())
            self.active_sessions[user_id] = []
        return responses

    async def route_message(self, agent_name: str, message: str, user_id: int) -> str:
        agent = self.agents.get(agent_name.lower())
        if not agent:
            return f"Agent {agent_name} not found in the registry."
        if not agent.is_active:
            await agent.activate(user_id)
        return await agent.process(message, user_id)


agent_bus = AgentBus()
