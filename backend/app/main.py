import os
from fastapi import FastAPI, Request, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import LeadCreate, LeadResponse, SignalItem, AlertTestResponse
from app.crm import init_db, get_db, create_crm_lead, get_all_leads
from app.signals import generate_live_signals, dispatch_high_intent_alerts
from app.alerts import send_slack_alert
from app.config import SLACK_WEBHOOK_URL

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
        "timestamp": os.popen("date -u").read().strip()
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
    Dispatches Slack alert in background if intent_score >= 90.
    """
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    user_agent = request.headers.get("User-Agent", "Unknown Browser")
    
    db_lead = await create_crm_lead(db, lead, client_ip, user_agent)
    
    # Trigger Slack alert if high intent
    if db_lead.intent_score >= 90:
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
    """Fetch stored leads from QUANTA CRM."""
    return get_all_leads(db, limit=limit)

@app.get("/api/v1/signals", response_model=list[SignalItem])
def get_intent_signals():
    """Fetch live micro-signals from the intent firehose."""
    return generate_live_signals()

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
        message=f"🔥 HIGH INTENT SIGNAL: {company} hit pricing page 4x in 10 mins. Playbook auto-dispatched.{msg_suffix}"
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
