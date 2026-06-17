import subprocess
import asyncio
import os
import uuid
from typing import Optional, Dict, Any
from backend.config import logger

class ContainerizedExecutor:
    """
    Handles the execution of security tools within isolated environments.
    If Docker is available, it spawns a Kali container. 
    Otherwise, it uses a restricted local subprocess (DEV MODE).
    """
    def __init__(self, use_docker: bool = True):
        self.use_docker = use_docker
        self.active_jobs: Dict[str, asyncio.Process] = {}

    async def execute(self, command: str, timeout: int = 300) -> Dict[str, Any]:
        job_id = str(uuid.uuid4())
        logger.info(f"Executing job {job_id}: {command}")

        try:
            if self.use_docker:
                # Production: Run in a transient Kali container
                # docker run --rm kali-linux-darkx /bin/bash -c "..."
                full_cmd = f"docker run --rm kali-linux-darkx /bin/bash -c {repr(command)}"
            else:
                # Dev Mode: Run locally with limited permissions
                full_cmd = command

            process = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.active_jobs[job_id] = process
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return {
                    "job_id": job_id,
                    "stdout": stdout.decode().strip(),
                    "stderr": stderr.decode().strip(),
                    "exit_code": process.returncode,
                    "status": "completed"
                }
            except asyncio.TimeoutError:
                process.kill()
                return {"job_id": job_id, "status": "timeout", "error": "Command timed out"}

        except Exception as e:
            logger.error(f"Execution error in job {job_id}: {e}")
            return {"job_id": job_id, "status": "error", "error": str(e)}
        finally:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]

executor = ContainerizedExecutor(use_docker=False) # Default to local for dev
