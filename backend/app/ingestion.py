import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.scoring import calculate_multi_factor_intent_score, generate_real_problem_statement

logger = logging.getLogger("quanta.ingestion")

def process_telemetry_and_score(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes incoming extension/external telemetry and scores it using ONLY
    the fields actually present in the payload. Missing fields default to
    0/False/"" (no signal), never to a fabricated positive value - a payload
    that only reports "user visited a jobs page" must not get credit for a
    funding round or a competitor evaluation it never observed.
    """
    domain = payload.get("domain", "").lower().replace("www.", "")
    url = payload.get("url", "")
    dwell_time = payload.get("dwell_time_seconds", 0) or 0
    concurrent_ips = payload.get("concurrent_hq_ips", 0) or 0

    scoring_telemetry = {
        "hiring_roles_count": payload.get("hiring_roles_count", 1 if payload.get("event_type") == "JOB_POST_INTERCEPT" else 0),
        "tech_stack_changes_count": payload.get("tech_stack_changes_count", 0),
        "funding_round": payload.get("funding_round", ""),
        "dwell_time_seconds": dwell_time,
        "concurrent_hq_ips": concurrent_ips,
        "persona_role": payload.get("persona_role", ""),
        "executive_hire_event": bool(payload.get("executive_hire_event", False)),
        "competitor_evaluation": bool(payload.get("competitor_evaluation", False)),
    }

    score_res = calculate_multi_factor_intent_score(scoring_telemetry)
    problem_text = generate_real_problem_statement(domain, score_res["score_breakdown"], scoring_telemetry)

    return {
        "domain": domain,
        "url": url,
        "company": payload.get("company") or f"Domain ({domain})",
        "event_type": payload.get("event_type", "PRICING_PAGE_INTERCEPT"),
        "intent_score": score_res["intent_score"],
        "scoring_breakdown": score_res["score_breakdown"],
        "problem_statement": problem_text,
        "source": payload.get("source", "chrome_extension"),
        "geo_location": payload.get("geo_location"),
        "browser_fingerprint": payload.get("browser_fingerprint"),
        "tech_stack_signals": payload.get("tech_stack_signals"),
        "hiring_signals": payload.get("hiring_signals"),
        "pricing_page_behavior": (
            f"{concurrent_ips} HQ IPs spent {dwell_time // 60} mins on this page"
            if concurrent_ips or dwell_time else None
        ),
        "funding_signals": payload.get("funding_round") or None
    }
