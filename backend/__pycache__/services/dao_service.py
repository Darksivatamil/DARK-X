import uuid
import json
import os
from typing import List, Dict, Any, Optional
from backend.config import logger

class ShadowDAO:
    """
    Simulates a Decentralized Autonomous Hacking Organization.
    Manages DIDs (Decentralized IDs) and the Shadow Ledger for reputation.
    """
    def __init__(self, ledger_path: str = "data/shadow_ledger.json"):
        self.ledger_path = ledger_path
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        self._init_ledger()

    def _init_ledger(self):
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'w') as f:
                json.dump({"identities": {}, "guilds": {}}, f, indent=4)

    def _read_ledger(self) -> Dict:
        with open(self.ledger_path, 'r') as f:
            return json.load(f)

    def _write_ledger(self, data: Dict):
        with open(self.ledger_path, 'w') as f:
            json.dump(data, f, indent=4)

    def register_did(self, user_id: int, username: str) -> str:
        ledger = self._read_ledger()
        did = f"did:darkx:{uuid.uuid4().hex[:16]}"
        ledger["identities"][did] = {
            "user_id": user_id,
            "username": username,
            "reputation": 100,
            "guild": None,
            "contributions": []
        }
        self._write_ledger(ledger)
        return did

    def get_did_by_user(self, user_id: int) -> Optional[str]:
        ledger = self._read_ledger()
        for did, info in ledger["identities"].items():
            if info["user_id"] == user_id:
                return did
        return None

    def update_reputation(self, did: str, delta: int):
        ledger = self._read_ledger()
        if did in ledger["identities"]:
            ledger["identities"][did]["reputation"] += delta
            self._write_ledger(ledger)

    def join_guild(self, did: str, guild_name: str):
        ledger = self._read_ledger()
        if did in ledger["identities"]:
            ledger["identities"][did]["guild"] = guild_name
            if guild_name not in ledger["guilds"]:
                ledger["guilds"][guild_name] = {"members": [], "power_level": 0}
            
            if did not in ledger["guilds"][guild_name]["members"]:
                ledger["guilds"][guild_name]["members"].append(did)
                
            self._write_ledger(ledger)

shadow_dao = ShadowDAO()
