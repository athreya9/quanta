import time
import logging
from typing import Dict, Tuple

logger = logging.getLogger("quanta.deduplication")

# Memory cache for fast 30-minute deduplication: key (domain, event_type) -> timestamp
RECENT_SIGNALS_CACHE: Dict[Tuple[str, str], float] = {}
DEDUP_WINDOW_SECONDS = 1800  # 30 minutes

def is_duplicate_signal(domain: str, event_type: str) -> bool:
    """
    Checks if a signal for (domain, event_type) was received within the 30-minute deduplication window.
    Returns True if duplicate, False if new.
    """
    clean_domain = domain.lower().replace("www.", "").strip()
    key = (clean_domain, event_type.upper().strip())
    now = time.time()
    
    # Prune old cache entries
    expired_keys = [k for k, ts in RECENT_SIGNALS_CACHE.items() if now - ts > DEDUP_WINDOW_SECONDS]
    for k in expired_keys:
        del RECENT_SIGNALS_CACHE[k]
        
    if key in RECENT_SIGNALS_CACHE:
        last_time = RECENT_SIGNALS_CACHE[key]
        if now - last_time < DEDUP_WINDOW_SECONDS:
            logger.info(f"[Deduplication Engine] Suppressed duplicate signal for {clean_domain} [{event_type}] ({int(now - last_time)}s ago)")
            return True
            
    # Record new timestamp
    RECENT_SIGNALS_CACHE[key] = now
    return False
