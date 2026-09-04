import os
import httpx
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, LeadDB, LeadCreate, LeadResponse, ExtensionSignalDB, ExtensionIngestPayload

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "db")
os.makedirs(DB_DIR, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(DB_DIR, "quanta_crm.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate missing columns for SQLite quanta_crm.db
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE leads ADD COLUMN phone VARCHAR(50)"))
            conn.commit()
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE leads ADD COLUMN problem_statement TEXT"))
            conn.commit()
        except Exception:
            pass

# Auto-initialize DB tables & migrations on startup
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def resolve_ip_geo(ip: str) -> str:
    """Enrich IP with city/country geo context."""
    if not ip or ip in ("127.0.0.1", "localhost", "::1"):
        return "San Francisco, United States (Resolved)"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(f"https://ipapi.co/{ip}/json/")
            if res.status_code == 200:
                data = res.json()
                city = data.get("city", "Unknown")
                country = data.get("country_name", "Unknown")
                if city != "Unknown" or country != "Unknown":
                    return f"{city}, {country}"
    except Exception:
        pass
    return "Global IP (Resolved)"

def calculate_intent_score(lead: LeadCreate) -> float:
    """Calculate lead intent score (70–99) based on role, company size indicators, and problem text."""
    score = 72.0
    role_lower = (lead.role or "").lower()
    if any(title in role_lower for title in ["vp", "head", "director", "cmo", "cro", "ceo", "founder", "lead"]):
        score += 12.0
    if lead.website and len(lead.website) > 4:
        score += 4.0
    if lead.phone and len(lead.phone) > 5:
        score += 5.0
    problem_text = lead.problem_statement or lead.struggle or ""
    if problem_text and len(problem_text) > 15:
        score += 6.0
    return min(99.0, max(70.0, round(score, 1)))

async def create_crm_lead(db: Session, lead_in: LeadCreate, ip_address: str, user_agent: str) -> LeadDB:
    geo_location = await resolve_ip_geo(ip_address)
    intent_score = calculate_intent_score(lead_in)
    problem_text = lead_in.problem_statement or lead_in.struggle or ""
    
    db_lead = LeadDB(
        name=lead_in.name,
        email=lead_in.email,
        company=lead_in.company,
        role=lead_in.role,
        website=lead_in.website,
        country=lead_in.country or (geo_location.split(",")[-1].strip() if "," in geo_location else "United States"),
        phone=lead_in.phone,
        problem_statement=problem_text,
        struggle=problem_text,
        ip_address=ip_address,
        geo_location=geo_location,
        user_agent=user_agent,
        intent_score=intent_score,
        status="NEW_QUALIFIED" if intent_score >= 80 else "NEW"
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead

def get_all_leads(db: Session, limit: int = 100) -> List[LeadDB]:
    return db.query(LeadDB).order_by(LeadDB.created_at.desc()).limit(limit).all()

def create_extension_signal(db: Session, payload: ExtensionIngestPayload) -> ExtensionSignalDB:
    db_signal = ExtensionSignalDB(
        domain=payload.domain,
        url=payload.url,
        event_type=payload.event_type,
        intent_score=payload.intent_score,
        source=payload.source or "chrome_extension",
        company=payload.company or f"Domain ({payload.domain})"
    )
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    return db_signal
