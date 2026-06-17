import abc
from typing import Dict, List, Any, Optional
from backend.config import logger
from backend.services.memory_service import memory_service


class BaseAgent(abc.ABC):
    def __init__(self, name: str, full_name: str, role: str, personality: str, capabilities: List[str]):
        self.name = name
        self.full_name = full_name
        self.role = role
        self.personality = personality
        self.capabilities = capabilities
        self.is_active = False
        self.status: str = "dormant"
        self.memory: Dict[str, Any] = {}

    @abc.abstractmethod
    async def process(self, message: str, user_id: int) -> str:
        pass

    async def activate(self, user_id: int) -> str:
        self.is_active = True
        self.status = "active"
        logger.info(f"Agent {self.name} activated for user {user_id}")
        return await self.get_intro()

    async def deactivate(self) -> str:
        self.is_active = False
        self.status = "dormant"
        logger.info(f"Agent {self.name} deactivated")
        return f"{self.name} is now dormant."

    async def get_intro(self) -> str:
        return f"I am {self.full_name}, the {self.role}. I am now online and ready to assist."

    async def remember(self, user_id: int, key: str, value: Any):
        await memory_service.record_experience(user_id, f"{key}: {value}")

    async def recall(self, user_id: int) -> Dict[str, Any]:
        return memory_service.load_long_term_memory(user_id)
