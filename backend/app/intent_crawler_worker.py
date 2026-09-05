import os
import sys
import time
import asyncio
import logging
from app.crm import SessionLocal
from app.crawler import execute_qeic_crawl_and_lead_build

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [QEIC-CRAWLER-WORKER] %(message)s"
)
logger = logging.getLogger("quanta.qeic_worker")

async def run_qeic_crawler_cycle():
    """Single execution pass for QEIC Autonomous Intent Crawler worker."""
    db = SessionLocal()
    try:
        logger.info("Starting QEIC 24/7 Autonomous Intent Crawl Pass...")
        res = await execute_qeic_crawl_and_lead_build(db)
        logger.info(f"QEIC Cycle complete: Targets={res['scanned_targets']}, Signals={res['new_signals_ingested']}, OutreachLeads={res['new_outreach_leads_generated']}")
        return res
    except Exception as e:
        logger.error(f"Error during QEIC worker execution: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

async def start_periodic_qeic_crawler_loop(interval_seconds: int = 600):
    """
    Runs QEIC Intent Crawler loop periodically every 10 minutes (600s).
    Integrated into FastAPI startup task or standalone systemd worker.
    """
    logger.info(f"QEIC Autonomous Crawler loop initialized. Interval: {interval_seconds}s (10 mins)")
    while True:
        try:
            await run_qeic_crawler_cycle()
        except Exception as e:
            logger.error(f"QEIC Loop iteration exception: {e}")
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    logger.info("Starting standalone QEIC Crawler worker process...")
    asyncio.run(start_periodic_qeic_crawler_loop(interval_seconds=600))
