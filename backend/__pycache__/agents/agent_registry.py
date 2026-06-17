from typing import List
from backend.agents.base_agent import BaseAgent
from backend.agents.agent_bus import agent_bus
from backend.services.ai_service import ai_service
from backend.services.memory_service import memory_service


class GenericAgent(BaseAgent):
    async def process(self, message: str, user_id: int) -> str:
        working_mem = await memory_service.get_working_memory(user_id, self.name)
        long_term_mem = memory_service.load_long_term_memory(user_id)
        experiences = "\n".join([e["event"] for e in long_term_mem["experiences"][-5:]])

        system_prompt = (
            f"You are {self.full_name}, the {self.role}. Personality: {self.personality}. "
            f"Capabilities: {', '.join(self.capabilities)}. "
            f"You are part of the DARK-X OMNISCIENCE system. "
            f"USER LONG-TERM MEMORY:\n{experiences}\n"
            f"Respond concisely and in character. If the user's past experience is relevant, mention it."
        )

        response = await ai_service.generate_response(system_prompt, message, working_mem)

        await memory_service.add_to_working_memory(user_id, self.name, "user", message)
        await memory_service.add_to_working_memory(user_id, self.name, "assistant", response)

        if len(working_mem) > 0 and len(working_mem) % 5 == 0:
            await self.reflect(user_id, message, response)

        return f"[{self.name}] {response}"

    async def reflect(self, user_id: int, user_msg: str, ai_res: str):
        reflection_prompt = (
            f"Analyze this interaction and extract one key fact or preference "
            f"about the user to remember permanently: User: {user_msg} | AI: {ai_res}"
        )
        fact = await ai_service.generate_response(
            "You are a memory processor. Extract a single concise fact.", reflection_prompt
        )
        await self.remember(user_id, "fact", fact)


def init_agents():
    agent_profiles = [
        {"name": "BLADE", "full_name": "Blade", "role": "Assassin Agent", "personality": "Sharp, lethal, precise", "capabilities": ["assassination", "precision strikes", "vulnerability exploitation"]},
        {"name": "SHADOW", "full_name": "Shadow", "role": "Leader Agent", "personality": "Commanding, strategic, omniscient", "capabilities": ["squad command", "tactical coordination", "mission planning"]},
        {"name": "HUNTER", "full_name": "Hunter", "role": "Scout Agent", "personality": "Alert, tracking, relentless", "capabilities": ["target tracking", "reconnaissance", "perimeter scanning"]},
        {"name": "SENTRY", "full_name": "Sentry", "role": "Defense Agent", "personality": "Vigilant, unyielding, protective", "capabilities": ["defense analysis", "firewall testing", "intrusion detection"]},
        {"name": "INFERNO", "full_name": "Inferno", "role": "Destroyer Agent", "personality": "Fierce, overwhelming, relentless", "capabilities": ["brute force", "denial of service", "overwhelming attacks"]},
        {"name": "SPECTER", "full_name": "Specter", "role": "Stealth Agent", "personality": "Ghostly, unseen, phantom-like", "capabilities": ["stealth operations", "invisible scanning", "covert recon"]},
        {"name": "NULL", "full_name": "Null", "role": "Support Agent", "personality": "Silent, helpful, background", "capabilities": ["data support", "log analysis", "background tasks"]},
        {"name": "PHANTOM", "full_name": "Phantom", "role": "Intelligence Agent", "personality": "Analytical, deep-thinking, observant", "capabilities": ["deep analysis", "pattern recognition", "threat intelligence"]},
        {"name": "ASSASSIN", "full_name": "Assassin", "role": "Execution Agent", "personality": "Fast, decisive, final", "capabilities": ["final strikes", "exploit execution", "precision payloads"]},
        {"name": "TITAN", "full_name": "Titan", "role": "Tank Agent", "personality": "Sturdy, immovable, powerful", "capabilities": ["heavy scanning", "brute force analysis", "stress testing"]},
        {"name": "WARLOCK", "full_name": "Warlock", "role": "Magic Agent", "personality": "Mystical, cryptic, powerful", "capabilities": ["cryptographic warfare", "quantum analysis", "encryption breaking"]},
        {"name": "RANGER", "full_name": "Ranger", "role": "Long Range Agent", "personality": "Far-seeing, patient, accurate", "capabilities": ["remote scanning", "external recon", "perimeter testing"]},
        {"name": "ENGINEER", "full_name": "Engineer", "role": "Tech Agent", "personality": "Technical, precise, builder", "capabilities": ["tool building", "script automation", "system engineering"]},
        {"name": "SUMMONER", "full_name": "Summoner", "role": "Special Agent", "personality": "Unique, creative, unpredictable", "capabilities": ["special operations", "creative attacks", "custom exploits"]},
        {"name": "OVERLORD", "full_name": "Overlord", "role": "Ultimate Agent", "personality": "Supreme, all-powerful, final", "capabilities": ["ultimate analysis", "full system control", "command authority"]},
    ]

    for profile in agent_profiles:
        agent = GenericAgent(
            name=profile["name"],
            full_name=profile["full_name"],
            role=profile["role"],
            personality=profile["personality"],
            capabilities=profile["capabilities"],
        )
        agent_bus.register_agent(agent)
