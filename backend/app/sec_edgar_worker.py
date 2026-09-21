import asyncio
import logging
from app.crm import SessionLocal
from app.sec_edgar import discover_from_sec_edgar
from app import icp as icp_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SEC-EDGAR-WORKER] %(message)s"
)
logger = logging.getLogger("quanta.sec_edgar_worker")

async def run_sec_edgar_cycle():
    """Single discovery pass against real, recent SEC Form D filings."""
    db = SessionLocal()
    try:
        active_icp = icp_module.get_active_icp(db)
        logger.info(f"Running SEC EDGAR Form D discovery (ICP: {active_icp.name if active_icp else 'none configured - unfiltered'})...")
        res = await discover_from_sec_edgar(db, icp=active_icp, days_back=2)
        logger.info(f"SEC EDGAR cycle complete: {res}")
        return res
    except Exception as e:
        logger.error(f"Error during SEC EDGAR worker execution: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

async def start_periodic_sec_edgar_loop(interval_seconds: int = 21600):
    """
    Runs every 6 hours by default. SEC EDGAR is a free public resource with a
    fair-access policy - Form D filings don't change minute to minute, so
    there's no reason to poll aggressively. Keep this interval long.
    """
    logger.info(f"SEC EDGAR discovery loop initialized. Interval: {interval_seconds}s")
    while True:
        try:
            await run_sec_edgar_cycle()
        except Exception as e:
            logger.error(f"SEC EDGAR loop iteration exception: {e}")
        await asyncio.sleep(interval_seconds)

if __name__ == "__main__":
    asyncio.run(start_periodic_sec_edgar_loop())
