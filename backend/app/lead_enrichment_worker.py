import os
import sys
import time
import asyncio
import logging
from app.crm import SessionLocal
from app.enrichment import run_batch_lead_enrichment

# Configure logger for ALEP worker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [QUANTA-ALEP-WORKER] %(message)s"
)
logger = logging.getLogger("quanta.alep_worker")

async def run_enrichment_worker_cycle():
    """Single execution pass for ALEP background worker."""
    db = SessionLocal()
    try:
        logger.info("Scanning QUANTA CRM database for un-enriched lead records...")
        res = await run_batch_lead_enrichment(db, limit=50)
        logger.info(f"Worker cycle complete: Scanned={res['scanned_count']}, Enriched={res['enriched_count']}")
        return res
    except Exception as e:
        logger.error(f"Error during ALEP worker execution: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

async def start_periodic_enrichment_loop(interval_seconds: int = 300):
    """
    Runs ALEP enrichment loop periodically every 5 minutes (300 seconds).
    Designed to run as an async background task inside FastAPI startup or systemd.
    """
    logger.info(f"ALEP Worker service loop initialized. Interval: {interval_seconds}s (5 mins)")
    while True:
        try:
            await run_enrichment_worker_cycle()
        except Exception as e:
            logger.error(f"Loop iteration exception: {e}")
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    logger.info("Starting standalone ALEP worker process...")
    asyncio.run(start_periodic_enrichment_loop(interval_seconds=300))
