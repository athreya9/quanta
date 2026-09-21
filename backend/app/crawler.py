import os
import json
import logging
import datetime
import httpx
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import ExtensionSignalDB, CompanyDB
from app.scoring import calculate_multi_factor_intent_score, generate_real_problem_statement
from app.deduplication import is_duplicate_signal

logger = logging.getLogger("quanta.qeic")

# Baseline seed watchlist - kept as a working example, not the only thing
# watched. The real watchlist (see build_crawl_target_list) is every company
# already in the companies table, so it grows automatically as SEC EDGAR
# discovers real companies or someone seeds real ones via
# POST /api/v1/companies/seed - no more hardcoded 15-company ceiling.
SEED_CRAWL_DOMAINS = [
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

def build_crawl_target_list(db: Session) -> List[Dict[str, str]]:
    """
    Merges the baseline seed watchlist with every company already known to
    the system (seeded by a user or discovered by SEC EDGAR). A company with
    no curated Greenhouse/Lever slug just gets a best-guess slug from its
    domain - if the guess is wrong, the fetch functions below simply return
    an empty list (already-established graceful-failure pattern), never a
    fabricated one.
    """
    seen = {t["domain"]: t for t in SEED_CRAWL_DOMAINS}
    for c in db.query(CompanyDB).all():
        if c.domain not in seen:
            seen[c.domain] = {
                "domain": c.domain,
                "company": c.company_name or c.domain,
                "slug": c.domain.split(".")[0],
            }
    return list(seen.values())

async def crawl_external_intent_sources(db: Session) -> List[Dict[str, Any]]:
    """
    QEIC (QUANTA External Intent Crawler) Core:
    Polls real, public Greenhouse/Lever job board APIs for every company the
    system currently knows about (see build_crawl_target_list). Only
    produces a result for a domain when real job postings were actually
    found - no fabricated fallback numbers, no invented funding rounds, no
    invented pricing-page telemetry (that data can only come from real
    extension/pixel capture, see ingestion.py).
    """
    crawled_signals = []
    timestamp_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
    target_list = build_crawl_target_list(db)

    for target in target_list:
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
    target_list = build_crawl_target_list(db)
    signals = await crawl_external_intent_sources(db)

    new_signals_count = 0

    for sig in signals:
        domain = sig["domain"]
        event_type = sig["event_type"]

        if is_duplicate_signal(domain, event_type):
            continue

        from app.companies import get_or_create_company, touch_last_signal
        company = get_or_create_company(db, domain, company_name=sig["company"], source="qeic_crawler_watchlist")

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
            company_id=company.id if company else None,
            demo_sample=False
        )
        db.add(db_signal)
        if company:
            touch_last_signal(db, company)
        new_signals_count += 1

    if new_signals_count > 0:
        db.commit()

    res = {
        "status": "completed",
        "scanned_targets": len(target_list),
        "new_signals_ingested": new_signals_count,
        "new_outreach_leads_generated": 0
    }

    try:
        from app.telemetry import log_telemetry_event
        log_telemetry_event(
            tool_name="QEIC Autonomous Intent Crawler",
            status="COMPLETED",
            raw_payload={"targets_count": len(target_list)},
            raw_output=res
        )
    except Exception:
        pass

    return res
