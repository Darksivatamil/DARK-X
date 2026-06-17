import asyncio
from backend.services.sese_service import sese_engine
from backend.database import SessionLocal
from backend.config import logger

async def sese_background_loop():
    """
    Autonomous background loop that monitors threats and generates quests.
    """
    while True:
        try:
            logger.info("SESE: Background intelligence cycle starting...")
            db = SessionLocal()
            await sese_engine.monitor_threats(db)
            db.close()
            logger.info("SESE: Intelligence cycle completed. Sleeping for 6 hours.")
        except Exception as e:
            logger.error(f"SESE Loop Error: {e}")
        
        # Sleep for 6 hours
        await asyncio.sleep(6 * 3600)
