import json
import os
from sqlalchemy.orm import Session
from backend.models.progress import UserProgress
from backend.config import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')

class GamificationService:
    def __init__(self):
        self.RANKS = [
            (1, "Shadow Initiate", "Gray"),
            (6, "Cyber Scout", "Green"),
            (16, "Data Hunter", "Blue"),
            (31, "Code Assassin", "Purple"),
            (51, "System Breaker", "Red"),
            (71, "Ghost Operative", "Orange"),
            (86, "Phantom Elite", "White"),
            (96, "Shadow Monarch", "Gold"),
        ]
        self._powers = None
        self._events = None

    def load_powers(self):
        if self._powers is None:
            try:
                path = os.path.join(DATA_DIR, 'powers.json')
                with open(path) as f:
                    self._powers = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load powers: {e}")
                self._powers = []
        return self._powers

    def load_events(self):
        if self._events is None:
            try:
                path = os.path.join(DATA_DIR, 'random_events.json')
                with open(path) as f:
                    self._events = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load events: {e}")
                self._events = []
        return self._events

    def get_rank_for_level(self, level: int) -> str:
        current_rank = self.RANKS[0][1]
        for min_lvl, rank, color in self.RANKS:
            if level >= min_lvl:
                current_rank = rank
            else:
                break
        return current_rank

    def add_xp(self, db: Session, user_id: int, xp_amount: int) -> dict:
        progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        if not progress:
            return {"error": "Progress not found"}

        old_level = progress.overall_level
        progress.total_xp += xp_amount

        new_level = (progress.total_xp // 500) + 1
        progress.overall_level = new_level
        progress.current_rank = self.get_rank_for_level(new_level)

        # Auto-unlock powers for current level
        powers = self.load_powers()
        unlocked = progress.powers_unlocked or []
        for p in powers:
            if p['level'] <= new_level and p['id'] not in unlocked:
                unlocked.append(p['id'])
        progress.powers_unlocked = unlocked

        db.commit()
        db.refresh(progress)

        leveled_up = new_level > old_level
        new_power = None
        if leveled_up:
            for p in powers:
                if p['level'] == new_level:
                    new_power = p['name']
                    break

        return {
            "new_level": new_level,
            "total_xp": progress.total_xp,
            "current_rank": progress.current_rank,
            "leveled_up": leveled_up,
            "new_power": new_power,
            "powers_unlocked": len(unlocked)
        }

    def unlock_power(self, db: Session, user_id: int, power_id: str):
        progress = db.query(UserProgress).filter(UserProgress.user_id == user_id).first()
        if not progress:
            return

        powers = progress.powers_unlocked or []
        if power_id not in powers:
            powers.append(power_id)
            progress.powers_unlocked = powers
            db.commit()

gamification_service = GamificationService()
