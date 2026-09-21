import os
import json
import datetime
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
from app.models import LeadDB, LeadCreate, LeadResponse, SignalItem, AlertTestResponse, ChromeExtensionEvent, ExtensionIngestPayload, ExtensionSignalDB, LinkedInProfileDB, LinkedInProfileResponse, LinkedInProfileUpdate, LinkedInProfileCreate, CompanyDB, CompanyResponse, ICPProfileCreate, ICPProfileResponse, CompanyICPScoreDB, CompanyICPScoreResponse, OutreachDraftResponse, CompanySeedRequest
from app.linkedin_crawler import crawl_linkedin_icp_profiles, add_linkedin_profile, verify_linkedin_url
from app.crm import init_db, get_db, create_crm_lead, get_all_leads, create_extension_signal
from app.signals import generate_live_signals, dispatch_high_intent_alerts
from app.alerts import send_slack_alert
from app.config import SLACK_WEBHOOK_URL, INTENT_MODE
from app.scoring import calculate_multi_factor_intent_score
from app.ingestion import process_telemetry_and_score
from app.deduplication import is_duplicate_signal
from app.lead_enrichment_worker import start_periodic_enrichment_loop, run_enrichment_worker_cycle
from app.intent_crawler_worker import start_periodic_qeic_crawler_loop, run_qeic_crawler_cycle
from app.companies import backfill_companies_from_existing_data, get_or_create_company
from app import icp as icp_module

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
    # SEC EDGAR Form D discovery - real, free, authoritative funding signals.
    # Runs every 6h (not 10min) out of respect for SEC's fair-access policy.
    from app.sec_edgar_worker import run_sec_edgar_cycle, start_periodic_sec_edgar_loop
    asyncio.create_task(run_sec_edgar_cycle())
    asyncio.create_task(start_periodic_sec_edgar_loop(interval_seconds=21600))

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "QUANTA Intent Engine",
        "port": 3002,
        "database": "SQLite / PostgreSQL Ready",
        "slack_alert_configured": bool(SLACK_WEBHOOK_URL),
        "intent_mode": INTENT_MODE,
        "data_policy": "No synthetic or fabricated records. Signals/leads are only stored when sourced from a real public API, a real visitor submission, or manually verified data.",
        "deduplication_engine": "30-Minute Signal Window Active",
        "scoring_engine": "8-Factor Behavioral Scoring Active (0-99, no artificial floor)",
        "automatic_lead_enrichment_engine": "Active (5-Minute Cron Worker Running; requires HUNTER_API_KEY/CLEARBIT_API_KEY to produce enrichment, otherwise reports NO_EXTERNAL_DATA_AVAILABLE)",
        "autonomous_intent_crawler": "Active (QEIC 10-Minute Cycle - polls real public Greenhouse/Lever job boards only)",
        "outsourcing_intent_engine": "Active (Reddit r/forhire + Upwork public RSS only)",
        "sec_edgar_discovery_engine": "Active (6-Hour Cycle - real Form D filings, domain-verified before storage, no paid API)",
        "telemetry_stream": "Active (Real-time ring buffer, starts empty)",
        "single_source_of_truth": "companies table (dedup key: normalized root domain) - see /api/v1/companies",
        "icp_driven": "GET/POST /api/v1/icp - discovery and scoring are unfiltered/neutral until an ICP profile is activated",
        "timestamp": datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S UTC %Y")
    }

@app.get("/api/v1/telemetry/logs")
def get_telemetry_logs(limit: int = 100, tool: Optional[str] = "all"):
    """
    Returns real-time telemetry events and raw outputs from QEIC crawler, Outsourcing crawler,
    ALEP enrichment engine, Deduplication engine, Slack alerts, and database writers.
    """
    from app.telemetry import get_recent_telemetry
    events = get_recent_telemetry(limit=limit, tool_filter=tool)
    return {
        "status": "active",
        "total_events": len(events),
        "tool_filter": tool,
        "events": events
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

@app.get("/api/v1/linkedin/profiles", response_model=list[LinkedInProfileResponse])
def get_linkedin_icp_profiles(db: Session = Depends(get_db)):
    """
    Returns all LinkedIn profiles in the ICP tracker. There is no synthetic
    seed data - this list is empty until a real profile is added via
    POST /api/v1/linkedin/profiles.
    """
    profiles = db.query(LinkedInProfileDB).order_by(LinkedInProfileDB.created_at.desc()).all()
    return profiles

@app.post("/api/v1/linkedin/profiles", response_model=LinkedInProfileResponse, status_code=status.HTTP_201_CREATED)
def create_linkedin_icp_profile(payload: LinkedInProfileCreate, db: Session = Depends(get_db)):
    """
    Adds a real, manually-sourced LinkedIn profile to the ICP tracker. The
    profile URL is verified live (HTTP check) before being saved. No email or
    activity history is fabricated - only what's actually supplied is stored.
    """
    profile = add_linkedin_profile(db, payload.model_dump(exclude_none=True))
    return profile

@app.post("/api/v1/linkedin/crawl")
def trigger_linkedin_icp_crawl(db: Session = Depends(get_db)):
    """
    Triggers live LinkedIn Profile Finder crawl pass & MX email verification.
    """
    result = crawl_linkedin_icp_profiles(db)
    return result

@app.post("/api/v1/linkedin/verify-url")
@app.get("/api/v1/linkedin/verify-url")
def api_verify_linkedin_url(url: Optional[str] = None, payload: Optional[dict] = None):
    """
    LinkedIn URL Checker API Tool Endpoint:
    Sends HTTP request with facebookexternalhit/1.1 headers to validate live public LinkedIn profiles.
    Rejects 404/302/login-wall pages.
    """
    target_url = url or (payload.get("url") if payload else "")
    if not target_url:
        raise HTTPException(status_code=400, detail="Parameter 'url' is required")
    return verify_linkedin_url(target_url)

@app.patch("/api/v1/linkedin/profiles/{profile_id}")
def update_linkedin_profile(profile_id: int, payload: LinkedInProfileUpdate, db: Session = Depends(get_db)):
    """
    Updates status lifecycle (NEW -> IN_OUTREACH -> QUALIFIED -> DEMO_BOOKED -> WON/LOST),
    outreach fields, notes, and requirement information.
    """
    profile = db.query(LinkedInProfileDB).filter(LinkedInProfileDB.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="LinkedIn profile record not found")
    
    if payload.status_lifecycle is not None:
        profile.status_lifecycle = payload.status_lifecycle
    if payload.connection_sent is not None:
        profile.connection_sent = payload.connection_sent
    if payload.connection_accepted is not None:
        profile.connection_accepted = payload.connection_accepted
    if payload.message_sent is not None:
        profile.message_sent = payload.message_sent
    if payload.followup_date is not None:
        profile.followup_date = payload.followup_date
    if payload.notes is not None:
        profile.notes = payload.notes
    if payload.requirement_information is not None:
        profile.requirement_information = payload.requirement_information

    db.commit()
    db.refresh(profile)
    return profile

# ============ ICP Profiles (many can exist/be active at once - one per project) ============

@app.get("/api/v1/icp", response_model=list[ICPProfileResponse])
def list_icp_profiles_endpoint(active_only: bool = False, db: Session = Depends(get_db)):
    """Lists all ICP (Ideal Customer Profile) definitions - one per project."""
    profiles = icp_module.list_icp_profiles(db, active_only=active_only)
    return [_serialize_icp(p) for p in profiles]

@app.get("/api/v1/icp/fields")
def list_icp_fields():
    """The menu of facts an ICP rule can reference right now. Grows as new data sources are added - never guess a field name."""
    from app.icp_fields import list_available_fields
    return {"available_fields": list_available_fields()}

@app.post("/api/v1/icp", response_model=ICPProfileResponse, status_code=status.HTTP_201_CREATED)
def create_icp_profile_endpoint(payload: ICPProfileCreate, db: Session = Depends(get_db)):
    """
    Creates a project's ICP as a list of {field, operator, value, weight}
    rules - see GET /api/v1/icp/fields for valid field names. Multiple
    profiles can exist and be active simultaneously, one per project.
    """
    profile = icp_module.create_icp_profile(db, payload.model_dump())
    return _serialize_icp(profile)

@app.post("/api/v1/icp/{profile_id}/clone", response_model=ICPProfileResponse, status_code=status.HTTP_201_CREATED)
def clone_icp_profile_endpoint(profile_id: int, new_name: str, db: Session = Depends(get_db)):
    """Starts a new project's ICP from an existing one - copy then tweak."""
    clone = icp_module.clone_icp_profile(db, profile_id, new_name)
    if not clone:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return _serialize_icp(clone)

@app.patch("/api/v1/icp/{profile_id}", response_model=ICPProfileResponse)
def update_icp_profile_endpoint(profile_id: int, payload: ICPProfileCreate, db: Session = Depends(get_db)):
    """Updates a project's ICP in place (criteria, geography, pitch, etc.) rather than creating a near-duplicate."""
    profile = icp_module.update_icp_profile(db, profile_id, payload.model_dump(exclude_unset=True))
    if not profile:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return _serialize_icp(profile)

@app.post("/api/v1/icp/{profile_id}/activate", response_model=ICPProfileResponse)
def activate_icp_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    profile = icp_module.set_icp_active(db, profile_id, True)
    if not profile:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return _serialize_icp(profile)

@app.post("/api/v1/icp/{profile_id}/deactivate", response_model=ICPProfileResponse)
def deactivate_icp_profile_endpoint(profile_id: int, db: Session = Depends(get_db)):
    profile = icp_module.set_icp_active(db, profile_id, False)
    if not profile:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return _serialize_icp(profile)

@app.get("/api/v1/icp/{profile_id}/qualified-leads")
def qualified_leads(profile_id: int, min_fit: str = "MEDIUM", limit: int = 20, db: Session = Depends(get_db)):
    """
    The one call to actually use this system day to day: every company that
    qualifies for this project's ICP, with its fit reasoning AND a ready-to-
    review outreach draft in the same response. Companies whose real signals
    aren't enough to draft anything honestly show drafted=false rather than
    being silently omitted or padded with filler - see app.outreach.
    """
    from app.outreach import draft_outreach_for_company

    icp = icp_module.get_icp_profile(db, profile_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP profile not found")

    fit_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    min_rank = fit_rank.get(min_fit.upper(), 2)
    acceptable_fits = [f for f, r in fit_rank.items() if r >= min_rank]

    scores = (
        db.query(CompanyICPScoreDB)
        .filter(CompanyICPScoreDB.icp_profile_id == profile_id, CompanyICPScoreDB.fit.in_(acceptable_fits))
        .order_by(CompanyICPScoreDB.score.desc())
        .limit(limit)
        .all()
    )

    results = []
    for s in scores:
        company = db.query(CompanyDB).filter(CompanyDB.id == s.company_id).first()
        if not company:
            continue
        draft = draft_outreach_for_company(db, company, icp)
        results.append({
            "company_id": company.id,
            "domain": company.domain,
            "company_name": company.company_name,
            "fit": s.fit,
            "score": s.score,
            "fit_reasons": json.loads(s.reasons) if s.reasons else [],
            "drafted": draft["status"] == "DRAFT_READY",
            "subject_line": draft.get("subject_line"),
            "email_body": draft.get("email_body"),
            "cited_signals": draft.get("cited_signals", []),
            "draft_skipped_reason": draft.get("reason"),
        })

    return {
        "icp_profile_id": profile_id,
        "icp_profile_name": icp.name,
        "min_fit": min_fit.upper(),
        "total_qualified": len(results),
        "ready_to_send_count": sum(1 for r in results if r["drafted"]),
        "leads": results,
    }

def _serialize_icp(p) -> dict:
    return {
        "id": p.id, "name": p.name, "description": p.description, "is_active": p.is_active,
        "criteria": json.loads(p.criteria) if p.criteria else None,
        "excluded_domains": json.loads(p.excluded_domains) if p.excluded_domains else None,
        "outreach_pitch": p.outreach_pitch,
        "created_at": p.created_at, "updated_at": p.updated_at,
    }

# ============ Companies (single source of truth) ============

@app.get("/api/v1/companies", response_model=list[CompanyResponse])
def list_companies(icp_profile_id: Optional[int] = None, fit: Optional[str] = None, limit: int = 100, db: Session = Depends(get_db)):
    """
    Lists canonical company records - the de-duplicated view of "who have we
    actually found evidence about". Pass icp_profile_id (+ optional fit) to
    view one project's qualified list over this same shared data.
    """
    if icp_profile_id:
        query = db.query(CompanyDB).join(CompanyICPScoreDB, CompanyICPScoreDB.company_id == CompanyDB.id).filter(
            CompanyICPScoreDB.icp_profile_id == icp_profile_id
        )
        if fit:
            query = query.filter(CompanyICPScoreDB.fit == fit.upper())
        return query.order_by(CompanyDB.last_signal_at.desc().nullslast()).limit(limit).all()

    return db.query(CompanyDB).order_by(CompanyDB.last_signal_at.desc().nullslast(), CompanyDB.created_at.desc()).limit(limit).all()

@app.get("/api/v1/companies/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@app.get("/api/v1/companies/{company_id}/icp-scores", response_model=list[CompanyICPScoreResponse])
def get_company_icp_scores(company_id: int, db: Session = Depends(get_db)):
    """Every project's fit score for this one company, side by side."""
    from app.models import ICPProfileDB as ICPModel
    rows = db.query(CompanyICPScoreDB).filter(CompanyICPScoreDB.company_id == company_id).all()
    out = []
    for r in rows:
        profile = db.query(ICPModel).filter(ICPModel.id == r.icp_profile_id).first()
        out.append({
            "company_id": r.company_id, "icp_profile_id": r.icp_profile_id,
            "icp_profile_name": profile.name if profile else None,
            "fit": r.fit, "score": r.score,
            "reasons": json.loads(r.reasons) if r.reasons else None,
            "computed_at": r.computed_at,
        })
    return out

@app.post("/api/v1/companies/seed")
async def seed_companies(payload: CompanySeedRequest, db: Session = Depends(get_db)):
    """
    Bulk-adds real companies YOU already know are relevant (existing network,
    prior research, whatever) as the fastest way to get real signal coverage
    for a new project - QUANTA doesn't have to "discover" a company you
    already know about. Every crawler (Greenhouse/Lever hiring, SEC EDGAR
    funding) automatically starts watching everything in the companies table,
    so seeding here means real ongoing monitoring starts immediately.

    Companies missing an industry get one inferred from their own real
    homepage content (app.industry_classifier) - never guessed from the
    domain name alone, and left blank if there's not enough real evidence.
    """
    from app.industry_classifier import infer_industry_from_homepage

    added = 0
    already_existed = 0
    industry_inferred = 0

    from app.companies import normalize_domain
    for entry in payload.companies:
        norm = normalize_domain(entry.domain)
        pre_existing = db.query(CompanyDB).filter(CompanyDB.domain == norm).first() if norm else None

        company = get_or_create_company(
            db, entry.domain,
            company_name=entry.company_name,
            industry=entry.industry,
            country=entry.country,
            source="user_seed",
        )
        if not company:
            continue
        if pre_existing:
            already_existed += 1
        else:
            added += 1

        if not company.industry:
            inferred = await infer_industry_from_homepage(company.domain)
            if inferred:
                company.industry = inferred
                company.updated_at = datetime.datetime.utcnow()
                db.commit()
                industry_inferred += 1

    scored_against = None
    if payload.icp_profile_id:
        icp = icp_module.get_icp_profile(db, payload.icp_profile_id)
        if icp:
            companies = db.query(CompanyDB).all()
            for c in companies:
                icp_module.score_and_store(db, c, icp)
            scored_against = icp.name

    return {
        "status": "completed",
        "submitted": len(payload.companies),
        "newly_added": added,
        "already_existed": already_existed,
        "industry_inferred_from_homepage": industry_inferred,
        "rescored_against_icp": scored_against,
    }

@app.post("/api/v1/companies/backfill")
def backfill_companies(db: Session = Depends(get_db)):
    """
    Idempotent maintenance task: links pre-existing leads/signals (created
    before the companies table existed) to a canonical Company row. Safe to
    call repeatedly - only touches rows with no company_id yet.
    """
    return backfill_companies_from_existing_data(db)

@app.post("/api/v1/companies/rescore")
def rescore_companies(icp_profile_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    Recomputes fit for every company against one ICP profile (or every
    active profile if icp_profile_id is omitted). Each profile's scores are
    stored independently - rescoring Project A never touches Project B's view.
    """
    if icp_profile_id:
        profiles = [icp_module.get_icp_profile(db, icp_profile_id)]
        if not profiles[0]:
            raise HTTPException(status_code=404, detail="ICP profile not found")
    else:
        profiles = icp_module.list_icp_profiles(db, active_only=True)
        if not profiles:
            raise HTTPException(status_code=400, detail="No active ICP profiles - create one via POST /api/v1/icp first")

    companies = db.query(CompanyDB).all()
    results = {}
    for profile in profiles:
        for c in companies:
            icp_module.score_and_store(db, c, profile)
        results[profile.name] = len(companies)

    return {"status": "completed", "companies_rescored": len(companies), "profiles": results}

@app.get("/api/v1/companies/{company_id}/draft-outreach", response_model=OutreachDraftResponse)
def draft_outreach_endpoint(company_id: int, icp_profile_id: int, db: Session = Depends(get_db)):
    """
    Drafts outreach copy for one company under one project's ICP. Returns
    INSUFFICIENT_DATA (no draft) if there's no real signal on file for this
    company - never falls back to generic/fabricated content. Every fact in
    a DRAFT_READY response is cited back to a real signal_id/source_url so it
    can be verified before anything is sent. Nothing is sent automatically -
    this only returns a draft for a human to review.
    """
    from app.outreach import draft_outreach_for_company
    company = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    icp = icp_module.get_icp_profile(db, icp_profile_id)
    if not icp:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return draft_outreach_for_company(db, company, icp)

@app.post("/api/v1/discovery/sec-edgar")
async def run_sec_edgar_discovery(days_back: int = 7, db: Session = Depends(get_db)):
    """
    Triggers a real SEC EDGAR Form D discovery pass: recent private funding
    filings, ICP-filtered by industry when an active ICP profile exists,
    domain-verified before anything is stored. Free, no API key.
    """
    from app.sec_edgar import discover_from_sec_edgar
    industry_keywords = icp_module.active_industry_keywords(db)
    res = await discover_from_sec_edgar(db, icp_industries=industry_keywords, days_back=days_back)
    res["industry_keywords_used"] = industry_keywords or "none (all active ICPs have no industry criteria - discovery is unfiltered)"
    return res

@app.post("/api/v1/discovery/uk-companies-house")
async def run_companies_house_discovery(industries: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Triggers a real UK Companies House discovery pass, filtered by real SIC
    codes (see app.companies_house.SIC_CODES_BY_INDUSTRY). Requires
    COMPANIES_HOUSE_API_KEY to be configured (free registration, not a paid
    API) - returns status=not_configured otherwise rather than guessing.
    `industries` is a comma-separated list (e.g. "automotive,electronics");
    omit to search all configured categories.
    """
    from app.companies_house import discover_from_companies_house
    industry_list = [i.strip() for i in industries.split(",")] if industries else None
    return await discover_from_companies_house(db, industries=industry_list)

@app.get("/api/v1/gleif/lookup")
async def gleif_lookup_endpoint(company_name: str, country: Optional[str] = None):
    """
    Real, free, no-key lookup against the global LEI registry - confirms a
    company is real/active and shows its real registered address/country.
    Fact-checking layer, not a discovery engine (no industry data in GLEIF).
    """
    from app.gleif import lookup_by_name
    results = await lookup_by_name(company_name, country=country)
    return {"query": company_name, "country_filter": country, "matches": results}

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

@app.post("/api/v1/crawler/outsourcing")
async def run_outsourcing_intent_crawl_pass(db: Session = Depends(get_db)):
    """
    Triggers a live OUTSOURCING INTENT crawl pass across Upwork RSS, SAM.gov RFPs, Reddit, Clutch, and GitHub Bounties.
    """
    from app.outsourcing_crawler import execute_outsourcing_intent_crawl
    res = await execute_outsourcing_intent_crawl(db)
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
                description=enrichment.get("problem_statement") or f"No problem statement captured for {ext.domain}.",
                signal_text=f"Extension signal capture on {ext.domain}",
                source_url=ext.url or f"https://{ext.domain}",
                detected_at="Just now",
                timestamp=ext.created_at.strftime("%H:%M:%S UTC"),
                intent_score=ext.intent_score,
                category=ext.event_type,
                source=ext.source or "chrome_extension",
                location=ext.geo_location,
                geo_location=ext.geo_location,
                action_playbook=None,
                demo_sample=ext.demo_sample or False,
                tech_stack_signals=enrichment.get("tech_stack_signals"),
                hiring_signals=enrichment.get("hiring_signals") or (enrichment.get("hiring_titles") if enrichment.get("hiring_titles") else None),
                pricing_page_behavior=enrichment.get("pricing_page_behavior"),
                funding_signals=enrichment.get("funding_signals")
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
    Ingests a real Chrome extension telemetry event into the extension_signals
    table (30-minute deduplication, 8-factor scoring, Slack alert if it crosses
    threshold). This does NOT create a CRM "lead" - silent browser telemetry
    never comes with a real contact identity, so fabricating a placeholder
    name/email for it would be exactly the kind of fake record this system is
    built to avoid. Real leads only come from a real visitor filling out the
    contact form (POST /api/v1/leads) or a manually verified LinkedIn profile.
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

    payload.intent_score = processed["intent_score"]

    db_signal = ExtensionSignalDB(
        domain=processed["domain"],
        url=processed["url"],
        event_type=processed["event_type"],
        intent_score=processed["intent_score"],
        source=processed["source"],
        company=processed["company"],
        geo_location=payload.geo_location,
        browser_fingerprint=payload.browser_fingerprint or request.headers.get("User-Agent"),
        enrichment_metadata=json.dumps(processed),
        demo_sample=payload.demo_sample or False
    )
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)

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
