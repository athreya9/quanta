import os
import json
import logging
import datetime
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import ExtensionSignalDB
from app.scoring import calculate_multi_factor_intent_score, generate_real_problem_statement
from app.deduplication import is_duplicate_signal

logger = logging.getLogger("quanta.qeic")

# Watchlist of company domains whose PUBLIC job boards we poll for real hiring
# signals. This is just a target list - no personal/contact data is attached
# here. QUANTA does not know who the decision-maker is at these companies
# unless a real lead comes in through the contact form or is added manually
# to the LinkedIn ICP tracker with a verified profile.
TARGET_CRAWL_DOMAINS = [
    {"domain": "stripe.com", "company": "Stripe", "slug": "stripe"},
    {"domain": "datadoghq.com", "company": "Datadog", "slug": "datadog"},
    {"domain": "hubspot.com", "company": "HubSpot", "slug": "hubspot"},
    {"domain": "snowflake.com", "company": "Snowflake", "slug": "snowflake"},
    {"domain": "mongodb.com", "company": "MongoDB", "slug": "mongodb"},
    {"domain": "postman.com", "company": "Postman", "slug": "postman"},
    {"domain": "freshworks.com", "company": "Freshworks", "slug": "freshworks"},
    {"domain": "amplitude.com", "company": "Amplitude", "slug": "amplitude"},
    {"domain": "notion.so", "company": "Notion", "slug": "notion"},
    {"domain": "figma.com", "company": "Figma", "slug": "figma"},
    {"domain": "vercel.com", "company": "Vercel", "slug": "vercel"},
    {"domain": "retool.com", "company": "Retool", "slug": "retool"},
    {"domain": "gong.io", "company": "Gong", "slug": "gong"},
    {"domain": "salesloft.com", "company": "Salesloft", "slug": "salesloft"},
    {"domain": "clari.com", "company": "Clari", "slug": "clari"},
]

async def fetch_open_source_greenhouse_jobs(board_slug: str) -> List[str]:
    """Fetches real public job posts from boards-api.greenhouse.io. No paid API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_slug}/jobs"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                jobs = data.get("jobs", [])
                titles = [j.get("title") for j in jobs if j.get("title")]
                return titles[:5]
    except Exception as e:
        logger.debug(f"Greenhouse public API crawl warning for {board_slug}: {e}")
    return []

async def fetch_open_source_lever_jobs(company_slug: str) -> List[str]:
    """Fetches real public postings from api.lever.co. No paid API."""
    url = f"https://api.lever.co/v0/postings/{company_slug}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                postings = res.json()
                if isinstance(postings, list):
                    titles = [p.get("text") for p in postings if p.get("text")]
                    return titles[:5]
    except Exception as e:
        logger.debug(f"Lever public API crawl warning for {company_slug}: {e}")
    return []

async def crawl_external_intent_sources() -> List[Dict[str, Any]]:
    """
    QEIC (QUANTA External Intent Crawler) Core:
    Polls real, public Greenhouse/Lever job board APIs for each watchlisted
    domain. Only produces a result for a domain when real job postings were
    actually found - no fabricated fallback numbers, no invented funding
    rounds, no invented pricing-page telemetry (that data can only come from
    real extension/pixel capture, see ingestion.py).
    """
    crawled_signals = []
    timestamp_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")

    for target in TARGET_CRAWL_DOMAINS:
        domain = target["domain"]
        company = target["company"]
        slug = target.get("slug", domain.split(".")[0])

        gh_titles = await fetch_open_source_greenhouse_jobs(slug)
        lever_titles = await fetch_open_source_lever_jobs(slug) if not gh_titles else []
        real_job_titles = gh_titles + lever_titles

        if not real_job_titles:
            # Nothing real found for this domain this cycle - skip it rather
            # than inventing a signal.
            continue

        telemetry = {
            "hiring_roles_count": len(real_job_titles),
            "tech_stack_changes_count": 0,
            "funding_round": "",
            "dwell_time_seconds": 0,
            "concurrent_hq_ips": 0,
            "persona_role": "",
            "executive_hire_event": False,
            "competitor_evaluation": False,
        }

        score_res = calculate_multi_factor_intent_score(telemetry)
        intent_score = score_res["intent_score"]
        scoring_breakdown = score_res["score_breakdown"]
        problem_stmt = generate_real_problem_statement(domain, scoring_breakdown, telemetry)

        crawled_signals.append({
            "domain": domain,
            "company": company,
            "event_type": "JOB_POST_INTERCEPT",
            "intent_score": intent_score,
            "timestamp": timestamp_str,
            "scoring_breakdown": scoring_breakdown,
            "hiring_titles": real_job_titles,
            "problem_statement": problem_stmt,
        })

    return crawled_signals

async def execute_qeic_crawl_and_lead_build(db: Session) -> Dict[str, Any]:
    """
    Executes a QEIC crawl pass: ingests real public hiring signals into the
    extension_signals table. Does NOT create CRM leads with invented contact
    people - a company-level hiring signal is not a named lead. Real leads
    only come from the contact form (crm.py) or manually verified LinkedIn
    profiles (linkedin_crawler.py).
    """
    logger.info("Executing QEIC public job-board intent crawl pass...")
    signals = await crawl_external_intent_sources()

    new_signals_count = 0

    for sig in signals:
        domain = sig["domain"]
        event_type = sig["event_type"]

        if is_duplicate_signal(domain, event_type):
            continue

        db_signal = ExtensionSignalDB(
            domain=domain,
            company=sig["company"],
            url=f"https://{domain}",
            event_type=event_type,
            intent_score=sig["intent_score"],
            source="qeic_crawler",
            geo_location=None,
            browser_fingerprint="QEIC Public Job Board Crawler",
            enrichment_metadata=json.dumps({
                "problem_statement": sig["problem_statement"],
                "scoring_breakdown": sig["scoring_breakdown"],
                "hiring_titles": sig["hiring_titles"],
                "source_detail": "Real postings fetched from public Greenhouse/Lever API"
            }),
            demo_sample=False
        )
        db.add(db_signal)
        new_signals_count += 1

    if new_signals_count > 0:
        db.commit()

    res = {
        "status": "completed",
        "scanned_targets": len(TARGET_CRAWL_DOMAINS),
        "new_signals_ingested": new_signals_count,
        "new_outreach_leads_generated": 0
    }

    try:
        from app.telemetry import log_telemetry_event
        log_telemetry_event(
            tool_name="QEIC Autonomous Intent Crawler",
            status="COMPLETED",
            raw_payload={"targets_count": len(TARGET_CRAWL_DOMAINS)},
            raw_output=res
        )
    except Exception:
        pass

    return res
