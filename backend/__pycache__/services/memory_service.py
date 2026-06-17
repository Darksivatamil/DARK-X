import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.config import logger

class MemoryService:
    def __init__(self, storage_path: str = "data/memory"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        # Short-term memory: user_id -> {agent_name: [messages]}
        self.working_memory: Dict[int, Dict[str, List[Dict]]] = {}

    def _get_user_file(self, user_id: int) -> str:
        return os.path.join(self.storage_path, f"user_{user_id}.json")

    def load_long_term_memory(self, user_id: int) -> Dict[str, Any]:
        file_path = self._get_user_file(user_id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {"experiences": [], "traits": {}}

    def save_long_term_memory(self, user_id: int, memory: Dict[str, Any]):
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w') as f:
            json.dump(memory, f, indent=4)

    async def add_to_working_memory(self, user_id: int, agent_name: str, role: str, content: str):
        if user_id not in self.working_memory:
            self.working_memory[user_id] = {}
        if agent_name not in self.working_memory[user_id]:
            self.working_memory[user_id][agent_name] = []
        
        self.working_memory[user_id][agent_name].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20 messages for working memory
        if len(self.working_memory[user_id][agent_name]) > 20:
            self.working_memory[user_id][agent_name].pop(0)

    async def get_working_memory(self, user_id: int, agent_name: str) -> List[Dict]:
        return self.working_memory.get(user_id, {}).get(agent_name, [])

    async def record_experience(self, user_id: int, experience: str):
        """Saves a significant event to long-term memory"""
        memory = self.load_long_term_memory(user_id)
        memory["experiences"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": experience
        })
        self.save_long_term_memory(user_id, memory)

memory_service = MemoryService()
