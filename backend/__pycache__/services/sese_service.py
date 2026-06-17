import asyncio
import random
import json
from typing import List, Dict, Any
from backend.services.ai_service import ai_service
from backend.services.task_service import task_service
from backend.config import logger

class SESEngine:
    """
    Self-Evolving Scenario Engine (SESE).
    Monitors threats and turns them into interactive lab quests.
    """
    def __init__(self):
        self.threat_feeds = [
            "https://nvd.nist.gov/feeds/xml/cve/latest",
            "https://www.exploit-db.com/rss.xml"
        ]

    async def monitor_threats(self, db_session):
        """
        Autonomous loop to find new CVEs and generate quests.
        """
        logger.info("SESE: Scanning for new zero-days...")
        # Simulation: We find a "critical" CVE
        mock_cve = {
            "id": "CVE-2026-X99",
            "title": "Remote Code Execution in Quantum-Router v4",
            "severity": "CRITICAL",
            "description": "A buffer overflow in the management interface allows unauthenticated RCE."
        }
        
        await self.deploy_lab(mock_cve)
        await self.create_dynamic_quest(mock_cve, db_session)

    async def deploy_lab(self, cve: Dict):
        """
        Uses Terraform/Ansible simulation to deploy a vulnerable environment.
        """
        logger.info(f"SESE: Deploying lab for {cve['id']}...")
        await asyncio.sleep(1) 
        logger.info(f"SESE: Lab {cve['id']}_ENV deployed in isolated sandbox.")

    async def create_dynamic_quest(self, cve: Dict, db_session):
        """
        Injects a real-world quest into the Task system.
        """
        system_prompt = f"You are the SESE Quest Architect. Create a high-stakes quest based on this real CVE: {cve['title']}. Description: {cve['description']}. Return JSON with title, description, learning_objectives, xp_reward."
        user_message = "Create an emergency quest."
        
        response_text = await ai_service.generate_response(system_prompt, user_message)
        try:
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)
            
            # Use the task_service to add to DB
            from backend.models.task import DailyTask
            quest = DailyTask(
                track="industry",
                difficulty="Expert",
                title=f"[EMERGENCY] {data['title']}",
                description=f"REAL-WORLD THREAT: {data['description']}",
                learning_objectives=data["learning_objectives"],
                xp_reward=data["xp_reward"] * 2 # Double XP for real threats
            )
            db_session.add(quest)
            db_session.commit()
            logger.info(f"SESE: Dynamic quest created for {cve['id']}.")
        except Exception as e:
            logger.error(f"SESE: Quest generation failed: {e}")

sese_engine = SESEngine()
