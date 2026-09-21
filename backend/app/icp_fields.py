"""
The field registry: the menu of facts an ICP rule is allowed to reference.

This is the extensibility point that makes the ICP system work "no matter
what the ICP is" without a schema migration every time a project needs a new
kind of criterion. Adding a new scoreable fact later (tech stack, domain age,
whatever a future data source produces) means adding one function here -
nothing else changes. A rule referencing a field with no resolver, or a
company where the resolver returns None, is simply treated as "unknown" by
app.icp.evaluate_company and never scored either direction - the system
never guesses a fact it doesn't actually have.

Every resolver has the signature: (company: CompanyDB, db: Session) -> Any | None
"""
import datetime
import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models import CompanyDB, ExtensionSignalDB

def _industry(company: CompanyDB, db: Session) -> Optional[str]:
    return company.industry

def _country(company: CompanyDB, db: Session) -> Optional[str]:
    return company.country

def _employee_count(company: CompanyDB, db: Session) -> Optional[int]:
    if company.employee_count_value and str(company.employee_count_value).isdigit():
        return int(company.employee_count_value)
    return None

def _discovery_source(company: CompanyDB, db: Session) -> Optional[str]:
    return company.first_discovered_source

def _has_funding_signal_90d(company: CompanyDB, db: Session) -> Optional[bool]:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    exists = db.query(ExtensionSignalDB).filter(
        ExtensionSignalDB.company_id == company.id,
        ExtensionSignalDB.event_type == "FUNDING_FILING",
        ExtensionSignalDB.created_at >= cutoff,
    ).first()
    return bool(exists) if exists is not None else False

def _has_hiring_signal_30d(company: CompanyDB, db: Session) -> Optional[bool]:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    exists = db.query(ExtensionSignalDB).filter(
        ExtensionSignalDB.company_id == company.id,
        ExtensionSignalDB.event_type == "JOB_POST_INTERCEPT",
        ExtensionSignalDB.created_at >= cutoff,
    ).first()
    return bool(exists) if exists is not None else False

def _hiring_titles_90d(company: CompanyDB, db: Session) -> Optional[list]:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    rows = db.query(ExtensionSignalDB).filter(
        ExtensionSignalDB.company_id == company.id,
        ExtensionSignalDB.event_type == "JOB_POST_INTERCEPT",
        ExtensionSignalDB.created_at >= cutoff,
    ).all()
    titles = []
    for r in rows:
        if not r.enrichment_metadata:
            continue
        try:
            meta = json.loads(r.enrichment_metadata)
            titles.extend(meta.get("hiring_titles") or [])
        except Exception:
            continue
    return titles or None

def _signal_count_30d(company: CompanyDB, db: Session) -> Optional[int]:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    count = db.query(ExtensionSignalDB).filter(
        ExtensionSignalDB.company_id == company.id,
        ExtensionSignalDB.created_at >= cutoff,
    ).count()
    return count

FIELD_RESOLVERS = {
    "industry": _industry,
    "country": _country,
    "employee_count": _employee_count,
    "discovery_source": _discovery_source,
    "has_funding_signal_90d": _has_funding_signal_90d,
    "has_hiring_signal_30d": _has_hiring_signal_30d,
    "hiring_titles": _hiring_titles_90d,
    "signal_count_30d": _signal_count_30d,
}

def resolve_field(field: str, company: CompanyDB, db: Session) -> Any:
    """Returns None for any field with no resolver - callers must treat that as 'unknown', never fabricate a value."""
    resolver = FIELD_RESOLVERS.get(field)
    if not resolver:
        return None
    return resolver(company, db)

def list_available_fields() -> list:
    return sorted(FIELD_RESOLVERS.keys())
