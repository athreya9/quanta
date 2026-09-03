import os
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import LeadCreate, LeadResponse, SignalItem
from app.crm import init_db, get_db, create_crm_lead, get_all_leads
from app.signals import generate_live_signals

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
        "timestamp": os.popen("date -u").read().strip()
    }

@app.post("/api/v1/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register_lead(
    request: Request,
    lead: LeadCreate,
    db: Session = Depends(get_db)
):
    """
    Ingests an incoming enquiry, enriches IP/geo location,
    scores intent, and stores the lead directly into QUANTA CRM.
    """
    client_ip = request.headers.get("X-Forwarded-For") or request.client.host
    if "," in client_ip:
        client_ip = client_ip.split(",")[0].strip()
    
    user_agent = request.headers.get("User-Agent", "Unknown Browser")
    
    db_lead = await create_crm_lead(db, lead, client_ip, user_agent)
    return db_lead

@app.get("/api/v1/leads", response_model=list[LeadResponse])
def list_leads(db: Session = Depends(get_db), limit: int = 50):
    """Fetch stored leads from QUANTA CRM."""
    return get_all_leads(db, limit=limit)

@app.get("/api/v1/signals", response_model=list[SignalItem])
def get_intent_signals():
    """Fetch live micro-signals from the intent firehose."""
    return generate_live_signals()

@app.post("/api/v1/signals/test-alert")
def trigger_test_alert(company: str = "Demo Prospect Corp"):
    """Simulate a live Slack & Chrome extension intent ping."""
    return {
        "status": "triggered",
        "channel": "#quanta-intent-alerts",
        "message": f"🔥 HIGH INTENT SIGNAL: {company} just hit pricing page 4x in 10 mins. Playbook auto-dispatched."
    }

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
