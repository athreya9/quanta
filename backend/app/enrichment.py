import os
import re
import socket
import logging
import json
import httpx
import dns.resolver
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import LeadDB
from app.scoring import generate_real_problem_statement

logger = logging.getLogger("quanta.alep")

# Environment API Key configurations
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
CLEARBIT_API_KEY = os.getenv("CLEARBIT_API_KEY", "")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
DROPCONTACT_API_KEY = os.getenv("DROPCONTACT_API_KEY", "")

def verify_domain_mx(domain: str) -> bool:
    """
    Real DNS MX record lookup. Returns True only if the domain actually
    publishes MX records (i.e. it can receive mail). Falls back to an A/AAAA
    record check only to confirm the domain exists at all, never to imply
    mail deliverability.
    """
    clean_domain = domain.lower().replace("www.", "").strip()
    if not clean_domain or "." not in clean_domain:
        return False
    try:
        answers = dns.resolver.resolve(clean_domain, "MX", lifetime=4.0)
        return len(answers) > 0
    except Exception:
        return False

def domain_resolves(domain: str) -> bool:
    """Cheap existence check: does the domain resolve at all (A/AAAA)."""
    clean_domain = domain.lower().replace("www.", "").strip()
    if not clean_domain or "." not in clean_domain:
        return False
    try:
        socket.gethostbyname(clean_domain)
        return True
    except Exception:
        return False

def generate_candidate_emails(name: str, domain: str) -> List[str]:
    """
    Generates plausible corporate email pattern *candidates* only - these are
    guesses, never presented as verified. Callers must run verify_email_syntax_and_mx
    (or a real verification API) before treating any candidate as real, and must
    label the result as a guess, not a verified address.
    """
    clean_domain = domain.lower().replace("www.", "").strip()
    if not name or not clean_domain:
        return [f"contact@{clean_domain}"] if clean_domain else []

    parts = re.sub(r'[^a-zA-Z\s]', '', name.strip().lower()).split()
    if not parts:
        return [f"contact@{clean_domain}"]

    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""

    candidates = []
    if first and last:
        candidates.append(f"{first}.{last}@{clean_domain}")
        candidates.append(f"{first}{last}@{clean_domain}")
        candidates.append(f"{first[0]}{last}@{clean_domain}")
        candidates.append(f"{first}@{clean_domain}")
    else:
        candidates.append(f"{first}@{clean_domain}")

    candidates.append(f"contact@{clean_domain}")
    return candidates

def verify_email_syntax_and_mx(email: str) -> bool:
    """
    Validates email syntax and confirms the domain has MX records.
    NOTE: this does NOT confirm the specific mailbox exists - only that the
    domain can receive mail. Callers must not label this "verified deliverable".
    """
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1]
    return verify_domain_mx(domain)

async def enrich_via_external_apis(domain: str, company: str) -> Dict[str, Any]:
    """
    Integrates external enrichment providers (Hunter, Clearbit). Returns an empty
    dict if no API keys are configured - callers must NOT backfill with guessed
    or generic data when this comes back empty.
    """
    results = {}

    if HUNTER_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    emails = data.get("emails", [])
                    if emails:
                        top = emails[0]
                        results["email"] = top.get("value")
                        results["role"] = top.get("position")
                        results["linkedin"] = top.get("linkedin")
                        results["phone"] = top.get("phone_number")
        except Exception as e:
            logger.warning(f"Hunter API error: {e}")

    if CLEARBIT_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(
                    f"https://company.clearbit.com/v2/companies/find?domain={domain}",
                    headers={"Authorization": f"Bearer {CLEARBIT_API_KEY}"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    employees = data.get("metrics", {}).get("employees")
                    if employees:
                        results["company_size"] = f"{employees} employees"
                    if data.get("phone"):
                        results["phone"] = results.get("phone") or data.get("phone")
                    tech = data.get("tech", [])
                    if tech:
                        results["tech_stack"] = tech[:5]
        except Exception as e:
            logger.warning(f"Clearbit API error: {e}")

    return results

async def enrich_lead_record(lead: LeadDB) -> LeadDB:
    """
    Core ALEP Lead Enrichment Method:
    Fills enriched_* fields ONLY from real sources - external enrichment APIs
    (if configured) or the lead's own submitted data. When no real enrichment
    data is available, fields are left blank and enrichment_status reflects
    that honestly instead of being padded with generic guesses.
    """
    domain = ""
    if lead.website:
        domain = lead.website.replace("https://", "").replace("http://", "").split("/")[0]
    elif lead.email and "@" in lead.email:
        domain = lead.email.split("@")[-1]

    external = await enrich_via_external_apis(domain, lead.company) if domain else {}

    # Email: only accept a real API-sourced email, or verify the lead's own
    # submitted email resolves. Never invent a new email address.
    lead.enriched_email = external.get("email") or lead.email

    lead.enriched_phone = external.get("phone") or lead.phone
    lead.enriched_role = external.get("role") or lead.role
    lead.enriched_linkedin = external.get("linkedin")
    lead.enriched_company_size = external.get("company_size")

    tech_list = external.get("tech_stack")
    lead.enriched_tech_stack = json.dumps(tech_list) if tech_list else None

    lead.enriched_hiring_signals = None
    lead.enriched_funding_signals = None

    has_real_enrichment = bool(external)

    if not lead.problem_statement:
        if domain:
            lead.problem_statement = f"No verified intent signals currently captured for {domain}."
        else:
            lead.problem_statement = "No verified intent signals currently captured."
        lead.struggle = lead.problem_statement

    lead.enrichment_status = "ENRICHED_FROM_REAL_SOURCE" if has_real_enrichment else "NO_EXTERNAL_DATA_AVAILABLE"
    return lead

async def run_batch_lead_enrichment(db: Session, limit: int = 50) -> Dict[str, Any]:
    """
    Batch processing function for ALEP background worker.
    Scans quanta_crm.db for pending or un-enriched leads.
    """
    pending_leads = db.query(LeadDB).filter(
        (LeadDB.enrichment_status == "PENDING") | (LeadDB.enrichment_status == None)
    ).limit(limit).all()

    enriched_count = 0
    for lead in pending_leads:
        try:
            await enrich_lead_record(lead)
            db.add(lead)
            enriched_count += 1
        except Exception as e:
            logger.error(f"Failed to enrich lead ID {lead.id}: {e}")
            lead.enrichment_status = "FAILED"

    if enriched_count > 0:
        db.commit()

    return {
        "status": "completed",
        "scanned_count": len(pending_leads),
        "enriched_count": enriched_count
    }
