from typing import List, Dict, Any
from backend.modules.mesh.executor import executor
from backend.config import logger

class MeshController:
    """
    The orchestrator for all tool executions. 
    It manages queues, permissions, and distributes tasks to the executor.
    """
    def __init__(self):
        self.job_history: List[Dict] = []

    async def run_tool(self, tool_name: str, command: str, user_id: int) -> Dict[str, Any]:
        logger.info(f"User {user_id} requesting tool {tool_name}")
        
        # In a real production environment, we'd check permissions here
        # e.g., if user.rank < "Data Hunter", block certain tools.
        
        result = await executor.execute(command)
        
        # Store in history for the agent's episodic memory
        self.job_history.append({
            "user_id": user_id,
            "tool": tool_name,
            "command": command,
            "result": result
        })
        
        return result

mesh_controller = MeshController()
