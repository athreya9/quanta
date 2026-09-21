import json
import logging
import datetime
from typing import Optional, Dict, Any
import tldextract
from sqlalchemy.orm import Session
from app.models import CompanyDB, LeadDB, ExtensionSignalDB

logger = logging.getLogger("quanta.companies")

def normalize_domain(raw: str) -> str:
    """
    The single canonical way to turn any URL/domain/email-domain string into
    a root domain for deduplication (e.g. "https://www.Stripe.com/pricing"
    and "checkout.stripe.com" both -> "stripe.com"). Every module that touches
    a domain MUST use this - it's what makes "companies" a real single source
    of truth instead of the same company existing under three different
    string spellings across three tables (the mess this schema replaces).
    """
    if not raw:
        return ""
    raw = raw.strip().lower()
    if "@" in raw and "://" not in raw and "/" not in raw:
        # looks like an email address - use the part after @
        raw = raw.split("@")[-1]
    ext = tldextract.extract(raw)
    if not ext.domain or not ext.suffix:
        return ""
    return f"{ext.domain}.{ext.suffix}"

def get_or_create_company(
    db: Session,
    domain_or_url: str,
    company_name: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    source: str = "unknown",
) -> Optional[CompanyDB]:
    """
    Resolves a domain to its single canonical CompanyDB row, creating one if
    it doesn't exist yet. This is the ONLY sanctioned way to attach a
    signal/lead to a company - never insert a company_name/domain pair
    directly into another table. Returns None if no valid domain could be
    extracted (caller should then skip attaching a company_id rather than
    guessing one).

    `source` must be a real, named origin (e.g. "sec_edgar_form_d",
    "greenhouse_watchlist", "website_form", "manual") - never "random" or
    "seed". It's stored permanently as first_discovered_source the first
    time this company is seen, so it stays honest/traceable.
    """
    domain = normalize_domain(domain_or_url)
    if not domain:
        return None

    existing = db.query(CompanyDB).filter(CompanyDB.domain == domain).first()
    if existing:
        # Backfill name/industry/country only if we didn't have them before -
        # never overwrite a real value with a less specific one.
        changed = False
        if company_name and not existing.company_name:
            existing.company_name = company_name
            changed = True
        if industry and not existing.industry:
            existing.industry = industry
            changed = True
        if country and not existing.country:
            existing.country = country
            changed = True
        if changed:
            existing.updated_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(existing)
        return existing

    company = CompanyDB(
        domain=domain,
        company_name=company_name,
        industry=industry,
        country=country,
        first_discovered_source=source,
    )
    db.add(company)
    try:
        db.commit()
        db.refresh(company)
    except Exception:
        # Race: another request created the same domain between our SELECT
        # and INSERT. Roll back and fetch the row that won.
        db.rollback()
        existing = db.query(CompanyDB).filter(CompanyDB.domain == domain).first()
        if existing:
            return existing
        raise
    return company

def touch_last_signal(db: Session, company: CompanyDB) -> None:
    """Marks that a real signal was just attached to this company."""
    company.last_signal_at = datetime.datetime.utcnow()
    db.commit()

def backfill_companies_from_existing_data(db: Session, limit: int = 500) -> Dict[str, int]:
    """
    One-time-safe, idempotent backfill: links existing leads/extension_signals
    rows (created before the companies table existed) to a canonical Company
    row. Only touches rows where company_id IS NULL, so re-running this is
    always safe and never overwrites anything.
    """
    leads_linked = 0
    signals_linked = 0

    leads = db.query(LeadDB).filter(LeadDB.company_id == None).limit(limit).all()
    for lead in leads:
        domain_source = lead.website or (lead.email.split("@")[-1] if lead.email and "@" in lead.email else None)
        if not domain_source:
            continue
        company = get_or_create_company(
            db, domain_source,
            company_name=lead.company,
            country=lead.country,
            source=f"backfill:{lead.signal_source or 'website_form'}"
        )
        if company:
            lead.company_id = company.id
            leads_linked += 1

    signals = db.query(ExtensionSignalDB).filter(ExtensionSignalDB.company_id == None).limit(limit).all()
    for sig in signals:
        if not sig.domain:
            continue
        company = get_or_create_company(
            db, sig.domain,
            company_name=sig.company,
            source=f"backfill:{sig.source or 'unknown'}"
        )
        if company:
            sig.company_id = company.id
            signals_linked += 1

    if leads_linked or signals_linked:
        db.commit()

    return {"leads_linked": leads_linked, "signals_linked": signals_linked}
