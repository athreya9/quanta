import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class LeadDB(Base):
    """
    SQLAlchemy ORM model for QUANTA CRM Leads.
    Saved directly into quanta_crm.db SQLite database.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    problem_statement = Column(Text, nullable=True)
    struggle = Column(Text, nullable=True)
    
    # Enrichment & Scoring fields
    ip_address = Column(String(45), nullable=True)
    geo_location = Column(String(255), nullable=True)
    user_agent = Column(Text, nullable=True)
    intent_score = Column(Float, default=85.0)
    status = Column(String(50), default="NEW_QUALIFIED")
    demo_sample = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ExtensionSignalDB(Base):
    """
    SQLAlchemy ORM model for Chrome Extension Signals stored in quanta_crm.db under extension_signals table.
    """
    __tablename__ = "extension_signals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain = Column(String(255), nullable=False, index=True)
    url = Column(Text, nullable=True)
    event_type = Column(String(100), default="CHROME_EXTENSION_INTERCEPT")
    intent_score = Column(Integer, default=92)
    source = Column(String(50), default="chrome_extension")
    company = Column(String(255), nullable=True)
    geo_location = Column(String(255), nullable=True)
    browser_fingerprint = Column(Text, nullable=True)
    enrichment_metadata = Column(Text, nullable=True)
    demo_sample = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LeadCreate(BaseModel):
    name: str = Field(..., example="Alex Morgan")
    email: EmailStr = Field(..., example="alex@acmegrowth.com")
    company: str = Field(..., example="Acme Growth Marketing")
    role: Optional[str] = Field(None, example="VP of Sales Ops")
    website: Optional[str] = Field(None, example="https://acmegrowth.com")
    country: Optional[str] = Field(None, example="United States")
    phone: Optional[str] = Field(None, example="+1 (555) 234-5678")
    problem_statement: Optional[str] = Field(None, example="Missing high-intent buyers visiting competitor pricing tables.")
    struggle: Optional[str] = Field(None, example="Alternative field for problem statement.")
    demo_sample: Optional[bool] = False

class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    company: str
    role: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    problem_statement: Optional[str] = None
    struggle: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None
    intent_score: float
    status: str
    demo_sample: bool = False
    created_at: datetime.datetime

    # STEP 8 Enriched Output Fields
    enriched_email: Optional[str] = None
    enriched_phone: Optional[str] = None
    enriched_role: Optional[str] = None
    enriched_linkedin: Optional[str] = None
    enriched_company_size: Optional[str] = None
    enriched_tech_stack: Optional[str] = None
    enriched_hiring_signals: Optional[str] = None
    enriched_funding_signals: Optional[str] = None
    enrichment_status: Optional[str] = "PENDING"

    class Config:
        from_attributes = True

class SignalItem(BaseModel):
    id: str
    company: str
    domain: Optional[str] = None
    event_type: str
    description: str
    signal_text: Optional[str] = None
    source_url: Optional[str] = None
    detected_at: str
    timestamp: Optional[str] = None
    intent_score: int
    category: str
    source: Optional[str] = "backend_ingestion"
    location: Optional[str] = None
    geo_location: Optional[str] = None
    action_playbook: Optional[str] = None
    demo_sample: bool = False
    # Step 5 Full Enrichment Signals
    tech_stack_signals: Optional[List[str]] = None
    hiring_signals: Optional[List[str]] = None
    pricing_page_behavior: Optional[str] = None
    funding_signals: Optional[str] = None

class ChromeExtensionEvent(BaseModel):
    domain: str
    company: Optional[str] = None
    event_type: str = "CHROME_EXTENSION_INTERCEPT"
    url: Optional[str] = None
    intent_score: int = 92
    browser_fingerprint: Optional[str] = None
    source: Optional[str] = "chrome_extension"
    demo_sample: Optional[bool] = False

class ExtensionIngestPayload(BaseModel):
    domain: str
    url: Optional[str] = None
    timestamp: Optional[str] = None
    event_type: str = "CHROME_EXTENSION_INTERCEPT"
    intent_score: int = 92
    source: str = "chrome_extension"
    company: Optional[str] = None
    geo_location: Optional[str] = None
    browser_fingerprint: Optional[str] = None
    demo_sample: Optional[bool] = False

class AlertTestResponse(BaseModel):
    status: str
    channel: str
    company: str
    intent_score: int
    message: str
    mode: str = "production"
