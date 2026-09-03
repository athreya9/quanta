import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class LeadDB(Base):
    """
    SQLAlchemy ORM model for QUANTA CRM Leads.
    Designed for seamless migration between SQLite (default) and PostgreSQL.
    """
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    struggle = Column(Text, nullable=True)
    
    # Enrichment fields
    ip_address = Column(String(45), nullable=True)
    geo_location = Column(String(255), nullable=True)
    user_agent = Column(Text, nullable=True)
    intent_score = Column(Float, default=85.0)
    status = Column(String(50), default="NEW")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LeadCreate(BaseModel):
    name: str = Field(..., example="Alex Morgan")
    email: EmailStr = Field(..., example="alex@acmegrowth.com")
    company: str = Field(..., example="Acme Growth Marketing")
    role: Optional[str] = Field(None, example="VP of Sales Ops")
    website: Optional[str] = Field(None, example="https://acmegrowth.com")
    country: Optional[str] = Field(None, example="United States")
    struggle: Optional[str] = Field(None, example="We miss high intent buyers looking for our competitors.")

class LeadResponse(BaseModel):
    id: int
    name: str
    email: str
    company: str
    role: Optional[str] = None
    website: Optional[str] = None
    country: Optional[str] = None
    struggle: Optional[str] = None
    ip_address: Optional[str] = None
    geo_location: Optional[str] = None
    intent_score: float
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class SignalItem(BaseModel):
    id: str
    type: str
    company: str
    signal_text: str
    timestamp: str
    intent_score: int
    category: str
    location: str
    action_playbook: str
