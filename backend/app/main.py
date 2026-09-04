import os
from typing import Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import LeadCreate, LeadResponse, SignalItem, AlertTestResponse, ChromeExtensionEvent, ExtensionIngestPayload, ExtensionSignalDB
from app.crm import init_db, get_db, create_crm_lead, get_all_leads, create_extension_signal
from app.signals import generate_live_signals, dispatch_high_intent_alerts
from app.alerts import send_slack_alert
from app.config import SLACK_WEBHOOK_URL, INTENT_MODE

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="QUANTA Intent Engine API",
    description="Backend API for QUANTA - Real-time Intent Signal Engine & CRM",
    version="1.0.0"
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
def startup_event():
    init_db()

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QUANTA Intent Engine",
        "port": 3002,
        "database": "SQLite / PostgreSQL Ready",
        "slack_alert_configured": bool(SLACK_WEBHOOK_URL),
        "intent_mode": INTENT_MODE,
        "timestamp": os.popen("date -u").read().strip()
    }

@app.get("/api/v1/extension/version")
def get_extension_version():
    """Returns latest extension version telemetry and auto-update status."""
    return {
        "version": "1.1.0",
        "latest_version": "1.1.0",
        "download_url": "https://quanta.virtusol.com/extension/quanta-extension.zip",
        "intent_mode": INTENT_MODE,
        "update_available": False,
        "features": [
            "Real-time domain matching engine",
            "Custom 3D infinity loop icons",
            "Automatic CRM event capture",
            "Real-time Slack webhooks"
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
    
    # Trigger Slack alert if high intent and real event
    if db_lead.intent_score >= 90 and not db_lead.demo_sample:
        background_tasks.add_task(
            send_slack_alert,
            company=db_lead.company,
            event_type="INBOUND_LEAD_ENQUIRY",
            description=f"New high-intent inbound lead submitted by {db_lead.name} ({db_lead.role or 'Exec'}) - Problem: {db_lead.problem_statement or 'N/A'}",
            intent_score=int(db_lead.intent_score),
            source_url=db_lead.website or "https://quanta.virtusol.com"
        )
        
    return db_lead

@app.get("/api/v1/leads", response_model=list[LeadResponse])
def list_leads(db: Session = Depends(get_db), limit: int = 50):
    """
    Fetch stored leads from QUANTA CRM.
    Filters out demo_sample leads if INTENT_MODE == 'production'.
    """
    all_leads = get_all_leads(db, limit=limit)
    if INTENT_MODE == "production":
        return [l for l in all_leads if not getattr(l, 'demo_sample', False)]
    return all_leads

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
        signals.append(
            SignalItem(
                id=f"ext_{ext.id}",
                company=ext.company or f"Domain ({ext.domain})",
                domain=ext.domain,
                event_type=ext.event_type,
                description=f"Active Chrome Extension intercept on {ext.domain}. URL: {ext.url or 'N/A'}",
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
                demo_sample=ext.demo_sample or False
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
    and triggers real-time Slack alerts for high intent events (demo_sample = False).
    """
    db_signal = create_extension_signal(db, payload)
    
    # Also record into leads table for CRM visibility
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    clean_domain = payload.domain.replace("www.", "").lower()
    lead_data = LeadCreate(
        name="Chrome Extension Intercept",
        email=f"intent@{clean_domain}",
        company=payload.company or f"Domain ({payload.domain})",
        role="Active Extension Prospect",
        website=payload.url or f"https://{payload.domain}",
        country="Extension Stream",
        phone=None,
        problem_statement=f"Chrome Extension captured active intent on '{payload.domain}' [{payload.event_type}]",
        struggle=f"Extension signal capture on {payload.domain}",
        demo_sample=payload.demo_sample or False
    )
    await create_crm_lead(db, lead_data, client_ip, request.headers.get("User-Agent", "QUANTA Chrome Extension"))

    # Only fire Slack alert if real signal (demo_sample = False) and intent_score >= 90
    if payload.intent_score >= 90 and not payload.demo_sample:
        background_tasks.add_task(
            send_slack_alert,
            company=payload.company or f"Target Domain ({payload.domain})",
            event_type=payload.event_type,
            description=f"🎯 Real Chrome Extension intent captured on domain '{payload.domain}' URL: {payload.url or 'N/A'}",
            intent_score=payload.intent_score,
            source_url=payload.url or f"https://{payload.domain}"
        )
        
    return {"status": "ingested", "signal_id": db_signal.id, "domain": payload.domain, "intent_mode": INTENT_MODE}

@app.post("/api/v1/signals/capture-extension")
async def capture_extension_event(
    request: Request,
    event: ChromeExtensionEvent,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingests Chrome extension domain intercepts directly into quanta_crm.db
    and triggers real-time Slack alerts for high intent events.
    """
    payload = ExtensionIngestPayload(
        domain=event.domain,
        url=event.url,
        event_type=event.event_type,
        intent_score=event.intent_score,
        source="chrome_extension",
        company=event.company,
        demo_sample=event.demo_sample or False
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
