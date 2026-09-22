import logging
import datetime

logger = logging.getLogger("quanta.deduplication")

DEDUP_WINDOW_SECONDS = 1800  # 30 minutes

def is_duplicate_signal(domain: str, event_type: str) -> bool:
    """
    Checks if a signal for (domain, event_type) was already stored within
    the last 30 minutes.

    DB-backed on purpose, not an in-memory cache. The original implementation
    used an in-memory dict, which resets to empty on every process restart -
    and this service gets restarted on every deploy. That silently defeated
    deduplication exactly when it mattered: two identical SEC EDGAR funding
    signals for the same real company (Nvision Capital Group) were found
    live in production, created ~3 hours apart across two deploy restarts,
    because the in-memory cache had "forgotten" the first one by the second
    restart's startup discovery pass. Querying the real stored signals
    instead means deduplication survives restarts the same way the data does.
    """
    from app.crm import SessionLocal
    from app.models import ExtensionSignalDB

    clean_domain = domain.lower().replace("www.", "").strip()
    clean_event_type = event_type.strip()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=DEDUP_WINDOW_SECONDS)

    db = SessionLocal()
    try:
        existing = db.query(ExtensionSignalDB).filter(
            ExtensionSignalDB.domain == clean_domain,
            ExtensionSignalDB.event_type.ilike(clean_event_type),
            ExtensionSignalDB.created_at >= cutoff,
        ).first()

        if existing:
            logger.info(f"[Deduplication Engine] Suppressed duplicate signal for {clean_domain} [{event_type}] (existing signal_id={existing.id})")
            try:
                from app.telemetry import log_telemetry_event
                log_telemetry_event(
                    tool_name="Deduplication Engine",
                    status="WARNING",
                    raw_payload={"domain": clean_domain, "event_type": event_type},
                    raw_output={"suppressed": True, "existing_signal_id": existing.id, "existing_created_at": existing.created_at.isoformat() if existing.created_at else None}
                )
            except Exception:
                pass
            return True

        return False
    finally:
        db.close()

def is_duplicate_citation(url: str) -> bool:
    """
    Permanent (no time window) check: has this exact citation URL already
    been stored as a signal? For discrete, one-time real-world events with a
    stable citation - a specific SEC filing, a specific Companies House
    record - as opposed to is_duplicate_signal's 30-minute window, which
    suits recurring/transient activity (new job posts legitimately appearing
    on the same domain over time). SEC EDGAR and Companies House discovery
    both re-scan overlapping date ranges every cycle (by design, to not miss
    anything near a window boundary), so without this they would re-store
    the same real filing every single cycle forever.
    """
    if not url:
        return False
    from app.crm import SessionLocal
    from app.models import ExtensionSignalDB
    db = SessionLocal()
    try:
        return db.query(ExtensionSignalDB).filter(ExtensionSignalDB.url == url).first() is not None
    finally:
        db.close()
