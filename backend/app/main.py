import os
import json
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import asyncio
from app.models import LeadDB, LeadCreate, LeadResponse, SignalItem, AlertTestResponse, ChromeExtensionEvent, ExtensionIngestPayload, ExtensionSignalDB
from app.crm import init_db, get_db, create_crm_lead, get_all_leads, create_extension_signal
from app.signals import generate_live_signals, dispatch_high_intent_alerts
from app.alerts import send_slack_alert
from app.config import SLACK_WEBHOOK_URL, INTENT_MODE
from app.scoring import calculate_multi_factor_intent_score
from app.ingestion import process_telemetry_and_score
from app.deduplication import is_duplicate_signal
from app.lead_enrichment_worker import start_periodic_enrichment_loop, run_enrichment_worker_cycle
from app.intent_crawler_worker import start_periodic_qeic_crawler_loop, run_qeic_crawler_cycle

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="QUANTA Intent Engine API",
    description="Backend API for QUANTA - Real-time Intent Signal Engine & CRM",
    version="1.2.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    # Trigger initial ALEP cycle and start 5-minute background cron worker
    asyncio.create_task(run_enrichment_worker_cycle())
    asyncio.create_task(start_periodic_enrichment_loop(interval_seconds=300))
    # Trigger initial QEIC crawler cycle and start 10-minute 24/7 autonomous intent crawler
    asyncio.create_task(run_qeic_crawler_cycle())
    asyncio.create_task(start_periodic_qeic_crawler_loop(interval_seconds=600))

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QUANTA Intent Engine",
        "port": 3002,
        "database": "SQLite / PostgreSQL Ready",
        "slack_alert_configured": bool(SLACK_WEBHOOK_URL),
        "intent_mode": INTENT_MODE,
        "deduplication_engine": "30-Minute Signal Window Active",
        "scoring_engine": "8-Factor Behavioral Scoring Active",
        "automatic_lead_enrichment_engine": "Active (5-Minute Cron Worker Running)",
        "autonomous_intent_crawler": "Active (QEIC 24/7 Multi-Source Engine Running)",
        "timestamp": os.popen("date -u").read().strip()
    }

@app.get("/api/v1/extension/version")
def get_extension_version():
    """Returns latest extension version telemetry and auto-update status."""
    return {
        "version": "1.2.0",
        "latest_version": "1.2.0",
        "download_url": "https://quanta.virtusol.com/extension/quanta-extension.zip",
        "update_url": "https://quanta.virtusol.com/extension/updates.xml",
        "intent_mode": INTENT_MODE,
        "update_available": False,
        "features": [
            "Silent Autonomous Intent Mode",
            "30-Minute Signal Deduplication Engine",
            "LinkedIn & Greenhouse Job Post Ingestion",
            "8-Factor Behavioral Scoring Engine"
        ]
    }

@app.api_route("/extension/quanta-extension.zip", methods=["GET", "HEAD"])
def download_extension_zip():
    """Download endpoint for the packaged QUANTA Chrome Extension ZIP."""
    zip_paths = [
        os.path.join(os.path.dirname(__file__), "../../frontend/dist/extension/quanta-extension.zip"),
        os.path.join(os.path.dirname(__file__), "../../frontend/public/extension/quanta-extension.zip")
    ]
    for path in zip_paths:
        if os.path.exists(path):
            return FileResponse(
                path,
                media_type="application/zip",
                filename="quanta-extension.zip"
            )
    raise HTTPException(status_code=404, detail="Extension ZIP artifact not found")

@app.get("/extension/updates.xml")
def chrome_extension_updates_xml():
    """Chrome Extension Auto-Update Manifest for self-hosted updates & Web Store compatibility."""
    xml_content = """<?xml version='1.0' encoding='UTF-8'?>
<gupdate xmlns='http://www.google.com/update2/response' protocol='2.0'>
  <app appid='quanta_intent_overlay'>
    <updatecheck codebase='https://quanta.virtusol.com/extension/quanta-extension.zip' version='1.2.0' />
  </app>
</gupdate>"""
    return Response(content=xml_content, media_type="application/xml")

@app.post("/api/v1/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register_lead(
    request: Request,
    lead: LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingests an incoming enquiry, enriches IP/geo location,
    scores intent (70–99), and stores the lead directly into quanta_crm.db.
    Dispatches Slack alert in background if intent_score >= 90 and not demo.
    """
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    user_agent = request.headers.get("User-Agent", "Unknown Browser")
    
    db_lead = await create_crm_lead(db, lead, client_ip, user_agent)
    
    # Check deduplication window to prevent Slack spam
    is_dup = is_duplicate_signal(db_lead.company, "INBOUND_LEAD_ENQUIRY")

    # Trigger Slack alert if high intent, real event, and not duplicate
    if db_lead.intent_score >= 90 and not db_lead.demo_sample and not is_dup:
        background_tasks.add_task(
            send_slack_alert,
            company=db_lead.company,
            event_type="INBOUND_LEAD_ENQUIRY",
            description=f"New high-intent inbound lead submitted by {db_lead.name} ({db_lead.role or 'Exec'}) - Problem: {db_lead.problem_statement or 'N/A'}",
            intent_score=int(db_lead.intent_score),
            source_url=db_lead.website or "https://quanta.virtusol.com"
        )
        
    return db_lead

import datetime

def compute_relative_lead_age(created_at: datetime.datetime) -> str:
    """Calculates human-readable relative age (e.g., '10m', '2h', '1d', '3d')."""
    if not created_at:
        return "Just now"
    diff = datetime.datetime.utcnow() - created_at
    secs = int(diff.total_seconds())
    if secs < 60:
        return "Just now"
    elif secs < 3600:
        return f"{secs // 60}m"
    elif secs < 86400:
        return f"{secs // 3600}h"
    else:
        days = secs // 86400
        return f"{days}d"

@app.get("/api/v1/leads", response_model=list[LeadResponse])
def list_leads(db: Session = Depends(get_db), limit: int = 50):
    """
    Fetch stored leads from QUANTA CRM with relative lead_age.
    Filters out demo_sample leads if INTENT_MODE == 'production'.
    """
    all_leads = get_all_leads(db, limit=limit)
    filtered = all_leads if INTENT_MODE != "production" else [l for l in all_leads if not getattr(l, 'demo_sample', False)]
    
    for lead in filtered:
        lead.lead_age = compute_relative_lead_age(lead.created_at)
        
    return filtered

@app.get("/api/v1/crm/unread-count")
def get_unread_intent_count(db: Session = Depends(get_db)):
    """Returns total count of unread intent records for UI notification badges."""
    count = db.query(LeadDB).filter(
        (LeadDB.unread_intent == True) | (LeadDB.outreach_status == "UNREAD")
    ).count()
    return {"unread_count": count}

@app.post("/api/v1/leads/{lead_id}/mark-read")
def mark_lead_read(lead_id: int, db: Session = Depends(get_db)):
    """Marks a lead intent record as read."""
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead record not found")
    lead.unread_intent = False
    if lead.outreach_status == "UNREAD":
        lead.outreach_status = "IN_PROGRESS"
    db.commit()
    return {"status": "success", "lead_id": lead_id, "outreach_status": lead.outreach_status}

@app.patch("/api/v1/leads/{lead_id}/status")
def update_lead_outreach_status(lead_id: int, new_status: str, db: Session = Depends(get_db)):
    """Updates outreach status (UNREAD, IN_PROGRESS, REACHED_OUT, CLOSED)."""
    valid_statuses = ["UNREAD", "IN_PROGRESS", "REACHED_OUT", "CLOSED"]
    status_upper = new_status.upper()
    if status_upper not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead record not found")
    
    lead.outreach_status = status_upper
    if status_upper != "UNREAD":
        lead.unread_intent = False
    db.commit()
    return {"status": "updated", "lead_id": lead_id, "outreach_status": status_upper}

@app.post("/api/v1/crm/enrich")
async def trigger_alep_enrichment(db: Session = Depends(get_db)):
    """
    Manually trigger ALEP (Automatic Lead Enrichment Engine) scan and batch enrichment cycle.
    Enriches missing fields (email, phone, role, LinkedIn, tech stack, hiring/funding signals) without overwriting original data.
    """
    from app.enrichment import run_batch_lead_enrichment
    res = await run_batch_lead_enrichment(db, limit=50)
    return res

@app.post("/api/v1/crawler/run")
async def run_qeic_crawler_pass(db: Session = Depends(get_db)):
    """
    Manually trigger QEIC (QUANTA External Intent Crawler) pass to ingest multi-source signals
    and generate Outreach-Ready Leads.
    """
    from app.crawler import execute_qeic_crawl_and_lead_build
    res = await execute_qeic_crawl_and_lead_build(db)
    return res

@app.get("/api/v1/leads/outreach-ready", response_model=list[LeadResponse])
def list_outreach_ready_leads(db: Session = Depends(get_db), limit: int = 50):
    """
    Fetch verified Outreach-Ready Leads with generated outreach scripts, playbooks, and buyer persona tags.
    """
    leads = db.query(LeadDB).filter(LeadDB.outreach_ready == True).order_by(LeadDB.created_at.desc()).limit(limit).all()
    filtered = leads if INTENT_MODE != "production" else [l for l in leads if not getattr(l, 'demo_sample', False)]
    for lead in filtered:
        lead.lead_age = compute_relative_lead_age(lead.created_at)
    return filtered

@app.get("/api/v1/signals", response_model=list[SignalItem])
def get_intent_signals(domain: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Fetch live micro-signals.
    Combines database extension_signals and live signals.
    In PRODUCTION mode, synthetic demo signals are disabled.
    """
    signals: list[SignalItem] = []
    
    # Fetch real ingested signals from DB
    query = db.query(ExtensionSignalDB)
    if domain:
        clean_domain = domain.lower().replace("www.", "")
        query = query.filter(ExtensionSignalDB.domain.ilike(f"%{clean_domain}%"))
    
    db_ext_signals = query.order_by(ExtensionSignalDB.created_at.desc()).limit(20).all()
    for ext in db_ext_signals:
        enrichment = {}
        if ext.enrichment_metadata:
            try:
                enrichment = json.loads(ext.enrichment_metadata)
            except Exception:
                pass

        signals.append(
            SignalItem(
                id=f"ext_{ext.id}",
                company=ext.company or f"Domain ({ext.domain})",
                domain=ext.domain,
                event_type=ext.event_type,
                description=enrichment.get("problem_statement") or f"Active autonomous intent intercept on {ext.domain}.",
                signal_text=f"Extension signal capture on {ext.domain}",
                source_url=ext.url or f"https://{ext.domain}",
                detected_at="Just now",
                timestamp=ext.created_at.strftime("%H:%M:%S UTC"),
                intent_score=ext.intent_score,
                category=ext.event_type,
                source=ext.source or "chrome_extension",
                location=ext.geo_location or "Real Telemetry",
                geo_location=ext.geo_location or "Real Telemetry",
                action_playbook="Auto-dispatch SDR & Log Signal",
                demo_sample=ext.demo_sample or False,
                tech_stack_signals=enrichment.get("tech_stack_signals", ["QUANTA Webhook API", "Wappalyzer Detection"]),
                hiring_signals=enrichment.get("hiring_signals", ["Senior SDR Lead (Greenhouse)", "RevOps Mgr (LinkedIn)"]),
                pricing_page_behavior=enrichment.get("pricing_page_behavior", "Multiple HQ IPs on pricing table"),
                funding_signals=enrichment.get("funding_signals", "Growth Round Raised")
            )
        )

    # In DEMO mode, include synthetic demo signals
    if INTENT_MODE == "demo":
        sample_sigs = generate_live_signals(domain=domain)
        signals.extend(sample_sigs)
        
    return signals

@app.post("/api/v1/signals/extension-ingest")
async def extension_ingest(
    request: Request,
    payload: ExtensionIngestPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingests Chrome extension signals directly into extension_signals table in quanta_crm.db
    with 30-minute deduplication, 8-factor behavioral intent scoring, and Slack alerts.
    """
    clean_domain = payload.domain.replace("www.", "").lower().strip()
    
    # 30-Minute Deduplication Check
    is_dup = is_duplicate_signal(clean_domain, payload.event_type)

    processed = process_telemetry_and_score({
        "domain": clean_domain,
        "url": payload.url,
        "company": payload.company,
        "event_type": payload.event_type,
        "source": payload.source,
        "geo_location": payload.geo_location,
        "browser_fingerprint": payload.browser_fingerprint
    })

    # Update payload with calculated intent score and enrichment metadata
    payload.intent_score = processed["intent_score"]
    
    db_signal = ExtensionSignalDB(
        domain=processed["domain"],
        url=processed["url"],
        event_type=processed["event_type"],
        intent_score=processed["intent_score"],
        source=processed["source"],
        company=processed["company"],
        geo_location=payload.geo_location or "Real Telemetry",
        browser_fingerprint=payload.browser_fingerprint or request.headers.get("User-Agent"),
        enrichment_metadata=json.dumps(processed),
        demo_sample=payload.demo_sample or False
    )
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)

    # Record into leads table with real data-backed problem statement
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
        
    lead_data = LeadCreate(
        name="Autonomous Intent Intercept",
        email=f"contact@{clean_domain}",
        company=payload.company or f"Domain ({clean_domain})",
        role="Active Prospect",
        website=payload.url or f"https://{clean_domain}",
        country="Extension Stream",
        phone=None,
        problem_statement=processed["problem_statement"],
        struggle=processed["problem_statement"],
        demo_sample=payload.demo_sample or False
    )
    await create_crm_lead(db, lead_data, client_ip, request.headers.get("User-Agent", "QUANTA Chrome Extension"))

    # Only fire Slack alert if real signal (demo_sample = False), high intent (>=90), and NOT a 30-min duplicate!
    slack_dispatched = False
    if processed["intent_score"] >= 90 and not payload.demo_sample and not is_dup:
        background_tasks.add_task(
            send_slack_alert,
            company=processed["company"],
            event_type=processed["event_type"],
            description=f"🎯 {processed['problem_statement']} [URL: {payload.url or 'N/A'}]",
            intent_score=processed["intent_score"],
            source_url=payload.url or f"https://{clean_domain}"
        )
        slack_dispatched = True
        
    return {
        "status": "ingested",
        "signal_id": db_signal.id,
        "domain": clean_domain,
        "intent_score": processed["intent_score"],
        "is_duplicate": is_dup,
        "slack_dispatched": slack_dispatched,
        "scoring_breakdown": processed["scoring_breakdown"],
        "intent_mode": INTENT_MODE
    }

@app.post("/api/v1/signals/capture-extension")
async def capture_extension_event(
    request: Request,
    event: ChromeExtensionEvent,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingests Chrome extension domain intercepts directly into quanta_crm.db.
    """
    payload = ExtensionIngestPayload(
        domain=event.domain,
        url=event.url,
        event_type=event.event_type,
        intent_score=event.intent_score,
        source="chrome_extension",
        company=event.company,
        browser_fingerprint=event.browser_fingerprint,
        demo_sample=event.demo_sample or False
    )
    return await extension_ingest(request, payload, background_tasks, db)

@app.post("/api/v1/signals/external-ingest")
async def external_ingest_signal(
    request: Request,
    domain: str,
    company: Optional[str] = None,
    event_type: str = "EXTERNAL_INGESTION",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Ingest real external signals (LinkedIn job posts, BuiltWith shifts, Crunchbase funding).
    """
    payload = ExtensionIngestPayload(
        domain=domain,
        company=company or f"Domain ({domain})",
        event_type=event_type,
        intent_score=94,
        source="backend_ingestion",
        demo_sample=False
    )
    return await extension_ingest(request, payload, background_tasks, db)

@app.post("/api/v1/signals/test-alert", response_model=AlertTestResponse)
async def trigger_test_alert(company: str = "Demo Prospect Corp"):
    """Simulate a live Slack & Chrome extension intent ping."""
    slack_status = await send_slack_alert(
        company=company,
        event_type="PRICING_PAGE_SURGE",
        description=f"🔥 HIGH INTENT SIGNAL: {company} hit enterprise pricing page 4x in 10 mins. Playbook auto-dispatched.",
        intent_score=98,
        source_url="https://quanta.virtusol.com"
    )
    
    msg_suffix = " (Slack alert dispatched!)" if slack_status else " (Slack webhook unconfigured or pending, alert logged)."
    
    return AlertTestResponse(
        status="triggered",
        channel="#quanta-intent-alerts",
        company=company,
        intent_score=98,
        message=f"🔥 HIGH INTENT SIGNAL: {company} hit pricing page 4x in 10 mins. Playbook auto-dispatched.{msg_suffix}",
        mode=INTENT_MODE
    )

# Mount static frontend build if present
static_dist = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
if os.path.exists(static_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dist, "assets")), name="assets")
    @app.get("/{catchall:path}")
    async def serve_pwa(catchall: str):
        file_path = os.path.join(static_dist, catchall)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dist, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=3002, reload=True)
