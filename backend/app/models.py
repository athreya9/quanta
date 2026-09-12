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

    # STEP 8: Automatic Lead Enrichment Engine (ALEP) Enriched Columns
    enriched_email = Column(String(255), nullable=True)
    enriched_phone = Column(String(50), nullable=True)
    enriched_role = Column(String(255), nullable=True)
    enriched_linkedin = Column(String(255), nullable=True)
    enriched_company_size = Column(String(100), nullable=True)
    enriched_tech_stack = Column(Text, nullable=True)
    enriched_hiring_signals = Column(Text, nullable=True)
    enriched_funding_signals = Column(Text, nullable=True)
    enrichment_status = Column(String(50), default="PENDING")

    # STEP 9: Outreach-Ready Lead Builder & QEIC Crawler Fields
    outreach_ready = Column(Boolean, default=False)
    outreach_playbook = Column(Text, nullable=True)
    buyer_persona = Column(String(100), nullable=True)
    signal_source = Column(String(100), default="qeic_crawler")

    # STEP 10: Real Data Activation & CRM Enhancements
    outreach_status = Column(String(50), default="UNREAD")
    intent_quality = Column(String(50), default="VERIFIED REAL")
    lead_owner = Column(String(100), default="Unassigned (Auto-Routed)")
    lead_notes = Column(Text, nullable=True)
    activity_log = Column(Text, nullable=True)
    unread_intent = Column(Boolean, default=True)

    # OUTSOURCING INTENT ENGINE FIELDS
    outsourcing_intent_metadata = Column(Text, nullable=True)

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

class LinkedInProfileDB(Base):
    """
    SQLAlchemy ORM model for LinkedIn Profile Finder & ICP Matching Engine.
    Saved into quanta_crm.db under linkedin_profiles table.
    Strictly enforcing the 22 user-specified ICP schema fields.
    """
    __tablename__ = "linkedin_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    current_job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False, default="United States")
    industry = Column(String(150), nullable=False)
    company_website = Column(String(255), nullable=True)
    approximate_company_size = Column(String(100), nullable=True)
    linkedin_profile_url = Column(String(500), nullable=False)
    linkedin_url_verification_status = Column(String(50), default="VERIFIED_LIVE")
    icp_fit = Column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    priority = Column(String(10), default="P1")     # P1, P2, P3
    industry_fit = Column(Text, nullable=True)
    geography_fit = Column(Text, nullable=True)
    seniority_fit = Column(Text, nullable=True)
    direct_material_procurement_fit = Column(Text, nullable=True)
    supplier_discovery_relevance = Column(Text, nullable=True)
    status_lifecycle = Column(String(50), default="NEW") # NEW, IN_OUTREACH, QUALIFIED, DEMO_BOOKED, WON, LOST
    connection_sent = Column(Boolean, default=False)
    connection_accepted = Column(Boolean, default=False)
    message_sent = Column(Boolean, default=False)
    followup_date = Column(String(100), nullable=True)
    activity_timeline = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    requirement_information = Column(Text, nullable=True)
    verified_email = Column(String(255), nullable=True)
    mx_verification_status = Column(String(50), default="MX_VERIFIED_DELIVERABLE")
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

    # STEP 9 Outreach-Ready Fields
    outreach_ready: Optional[bool] = False
    outreach_playbook: Optional[str] = None
    buyer_persona: Optional[str] = None
    signal_source: Optional[str] = "qeic_crawler"

    # STEP 10 Real Data & CRM Enhancements Output Fields
    outreach_status: Optional[str] = "UNREAD"
    intent_quality: Optional[str] = "VERIFIED REAL"
    lead_owner: Optional[str] = "Unassigned (Auto-Routed)"
    lead_notes: Optional[str] = None
    activity_log: Optional[str] = None
    unread_intent: Optional[bool] = True
    lead_age: Optional[str] = "Just now"
    outsourcing_intent_metadata: Optional[str] = None

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

class LinkedInProfileResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    full_name: str
    current_job_title: str
    company: str
    country: str
    industry: str
    company_website: Optional[str] = None
    approximate_company_size: Optional[str] = None
    linkedin_profile_url: str
    linkedin_url_verification_status: str
    icp_fit: str
    priority: str
    industry_fit: Optional[str] = None
    geography_fit: Optional[str] = None
    seniority_fit: Optional[str] = None
    direct_material_procurement_fit: Optional[str] = None
    supplier_discovery_relevance: Optional[str] = None
    status_lifecycle: str
    connection_sent: bool
    connection_accepted: bool
    message_sent: bool
    followup_date: Optional[str] = None
    activity_timeline: Optional[str] = None
    notes: Optional[str] = None
    requirement_information: Optional[str] = None
    verified_email: Optional[str] = None
    mx_verification_status: Optional[str] = "MX_VERIFIED_DELIVERABLE"
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class LinkedInProfileUpdate(BaseModel):
    status_lifecycle: Optional[str] = None
    connection_sent: Optional[bool] = None
    connection_accepted: Optional[bool] = None
    message_sent: Optional[bool] = None
    followup_date: Optional[str] = None
    notes: Optional[str] = None
    requirement_information: Optional[str] = None
