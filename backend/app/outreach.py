"""
Outreach drafting: turns a company's REAL, ALREADY-STORED signals into a
draft message. This is the one place in the codebase allowed to produce
send-ready copy, and it has one hard rule: it will not invent, embellish, or
paraphrase-into-vagueness a claim that isn't traceable to a specific signal
row already in the database.

If a company has no real signal on file, this returns INSUFFICIENT_DATA and
generates nothing - there is no generic/demo fallback template. Every draft
this module produces carries its citations (signal id, real source URL,
real detected date) alongside the copy, so whoever sends it can verify every
factual claim before it goes out.

The persuasive/pitch copy (what the sender is actually offering) is NOT
generated here - it comes from ICPProfileDB.outreach_pitch, which the human
who owns that project writes and approves. This module only ever supplies
the verifiable "here's what we actually observed" part.
"""
import json
import datetime
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import CompanyDB, ICPProfileDB, ExtensionSignalDB

logger = logging.getLogger("quanta.outreach")

MAX_CITED_SIGNALS = 3
SIGNAL_FRESHNESS_DAYS = 120  # older than this, don't cite it as if it's current

def _signal_to_citation(sig: ExtensionSignalDB) -> Dict[str, Any]:
    meta = {}
    if sig.enrichment_metadata:
        try:
            meta = json.loads(sig.enrichment_metadata)
        except Exception:
            pass
    return {
        "signal_id": sig.id,
        "event_type": sig.event_type,
        "fact": meta.get("problem_statement") or f"{sig.event_type} observed on {sig.domain}",
        "source_url": sig.url,
        "source": sig.source,
        "detected_at": sig.created_at.isoformat() if sig.created_at else None,
    }

def draft_outreach_for_company(db: Session, company: CompanyDB, icp: ICPProfileDB) -> Dict[str, Any]:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=SIGNAL_FRESHNESS_DAYS)
    signals = (
        db.query(ExtensionSignalDB)
        .filter(ExtensionSignalDB.company_id == company.id, ExtensionSignalDB.created_at >= cutoff)
        .order_by(ExtensionSignalDB.created_at.desc())
        .limit(MAX_CITED_SIGNALS)
        .all()
    )

    if not signals:
        return {
            "status": "INSUFFICIENT_DATA",
            "company_id": company.id,
            "company_name": company.company_name,
            "icp_profile_id": icp.id,
            "icp_profile_name": icp.name,
            "subject_line": None,
            "email_body": None,
            "cited_signals": [],
            "reason": f"No real signal on file for {company.domain} within the last {SIGNAL_FRESHNESS_DAYS} days - nothing to cite, so no draft was generated. Run discovery/crawler passes first, or this company simply has no current activity worth reaching out about.",
        }

    citations = [_signal_to_citation(s) for s in signals]
    company_label = company.company_name or company.domain

    fact_lines = []
    for c in citations:
        date_str = c["detected_at"][:10] if c["detected_at"] else "recently"
        fact_lines.append(f"- {c['fact']} (observed {date_str}, source: {c['source_url'] or c['source']})")

    pitch = icp.outreach_pitch or "[PITCH NOT CONFIGURED - set ICPProfile.outreach_pitch for this project before sending anything]"

    subject_line = f"Quick note re: {company_label}"

    email_body = f"""Hi {{FirstName}},

I'm reaching out because I came across the following, specifically about {company_label}:

{chr(10).join(fact_lines)}

{pitch}

Would you be open to a short conversation?

Best,
{{YourName}}"""

    return {
        "status": "DRAFT_READY",
        "company_id": company.id,
        "company_name": company.company_name,
        "icp_profile_id": icp.id,
        "icp_profile_name": icp.name,
        "subject_line": subject_line,
        "email_body": email_body,
        "cited_signals": citations,
        "reason": None,
    }
