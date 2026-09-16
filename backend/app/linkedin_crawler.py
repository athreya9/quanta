import os
import json
import logging
import datetime
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import LinkedInProfileDB
from app.telemetry import log_telemetry_event
from app.enrichment import verify_domain_mx

logger = logging.getLogger("quanta.linkedin_crawler")

# User Agents for URL Verification & Extraction
LINKEDIN_HEADERS = {
    'User-Agent': 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9'
}

def verify_linkedin_url(url: str) -> Dict[str, Any]:
    """
    LinkedIn URL Verification Checker:
    Sends a real HTTP request (with facebookexternalhit headers, since LinkedIn
    serves a public OG-tag page to that crawler) to check whether a profile URL
    is live. Honestly reports when a result cannot be determined (LinkedIn very
    commonly returns HTTP 999 to automated requests) instead of assuming valid.
    """
    clean_url = url.strip()
    if not clean_url or "linkedin.com/in/" not in clean_url:
        result = {
            "url": clean_url,
            "valid": False,
            "http_status": 400,
            "title": "",
            "reason": "Invalid LinkedIn URL structure"
        }
        log_telemetry_event(
            tool_name="LinkedIn URL Checker",
            status="ERROR",
            raw_payload={"url": clean_url},
            raw_output=result,
            raw_error="URL structure invalid"
        )
        return result

    try:
        r = httpx.get(clean_url, headers=LINKEDIN_HEADERS, follow_redirects=True, timeout=8.0)
        status_code = r.status_code

        if status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            title_tag = soup.find('title')
            title_text = title_tag.text.strip() if title_tag else ''

            og_title = soup.find('meta', {'property': 'og:title'})
            og_t = og_title.get('content', '').strip() if og_title else ''

            is_404_title = "profile not found" in title_text.lower() or "404" in title_text.lower() or "page not found" in title_text.lower()

            if is_404_title:
                result = {
                    "url": clean_url,
                    "valid": False,
                    "http_status": 404,
                    "title": title_text,
                    "reason": "Profile page returned a 'not found' page"
                }
            else:
                result = {
                    "url": clean_url,
                    "valid": True,
                    "http_status": 200,
                    "title": title_text or og_t or "LinkedIn Public Profile",
                    "reason": "HTTP 200 - page title/OG tags parsed successfully"
                }
        elif status_code in (301, 302, 303, 307, 308):
            result = {
                "url": clean_url,
                "valid": False,
                "http_status": status_code,
                "title": "",
                "reason": f"HTTP {status_code} redirect - likely an auth wall, not confirmed live"
            }
        elif status_code in (404, 410):
            result = {
                "url": clean_url,
                "valid": False,
                "http_status": 404,
                "title": "Profile Not Found",
                "reason": "HTTP 404 - profile does not exist"
            }
        else:
            # LinkedIn frequently returns 999 (or other non-standard codes) to
            # automated/datacenter requests. This is NOT evidence the profile
            # is valid or invalid - report it honestly as unverifiable.
            result = {
                "url": clean_url,
                "valid": None,
                "http_status": status_code,
                "title": "",
                "reason": f"HTTP {status_code} - LinkedIn blocked or rate-limited the automated check; verify manually"
            }

        log_telemetry_event(
            tool_name="LinkedIn URL Checker",
            status="COMPLETED" if result["valid"] else "WARNING",
            raw_payload={"url": clean_url},
            raw_output=result
        )
        return result

    except Exception as e:
        err_res = {
            "url": clean_url,
            "valid": None,
            "http_status": 0,
            "title": "",
            "reason": f"Connection error during LinkedIn verification: {str(e)}"
        }
        log_telemetry_event(
            tool_name="LinkedIn URL Checker",
            status="ERROR",
            raw_payload={"url": clean_url},
            raw_output=err_res,
            raw_error=str(e)
        )
        return err_res

def add_linkedin_profile(db: Session, data: Dict[str, Any]) -> LinkedInProfileDB:
    """
    Adds a real, user-supplied LinkedIn profile to the ICP tracker.
    This is the only way profiles enter the table now - there is no synthetic
    seed data. The URL is verified live before being trusted, and any email is
    only marked with an MX status, never "verified deliverable" (mailbox-level
    verification isn't possible without a paid provider).
    """
    url = (data.get("linkedin_profile_url") or "").strip()
    verification = verify_linkedin_url(url) if url else {"valid": None, "http_status": 0}

    if verification.get("valid") is True:
        verification_status = "VERIFIED_LIVE"
    elif verification.get("valid") is False:
        verification_status = "VERIFICATION_FAILED"
    else:
        verification_status = "UNVERIFIED"

    email = (data.get("verified_email") or "").strip() or None
    if email:
        domain = email.split("@")[-1]
        mx_status = "MX_RECORD_FOUND" if verify_domain_mx(domain) else "NO_MX_RECORD"
    else:
        mx_status = "NOT_PROVIDED"

    profile = LinkedInProfileDB(
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        full_name=data.get("full_name") or f"{data.get('first_name', '')} {data.get('last_name', '')}".strip(),
        current_job_title=data.get("current_job_title", ""),
        company=data.get("company", ""),
        country=data.get("country") or "Unknown",
        industry=data.get("industry", ""),
        company_website=data.get("company_website"),
        approximate_company_size=data.get("approximate_company_size"),
        linkedin_profile_url=url,
        linkedin_url_verification_status=verification_status,
        icp_fit=data.get("icp_fit") or "UNSCORED",
        priority=data.get("priority") or "UNSET",
        industry_fit=data.get("industry_fit"),
        geography_fit=data.get("geography_fit"),
        seniority_fit=data.get("seniority_fit"),
        direct_material_procurement_fit=data.get("direct_material_procurement_fit"),
        supplier_discovery_relevance=data.get("supplier_discovery_relevance"),
        status_lifecycle="NEW",
        connection_sent=False,
        connection_accepted=False,
        message_sent=False,
        followup_date=data.get("followup_date"),
        activity_timeline=json.dumps([
            {"timestamp": datetime.datetime.utcnow().isoformat(), "event": f"Profile added manually. URL check: HTTP {verification.get('http_status')} ({verification_status})"}
        ]),
        notes=data.get("notes"),
        requirement_information=data.get("requirement_information"),
        verified_email=email,
        mx_verification_status=mx_status
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    log_telemetry_event(
        tool_name="LinkedIn Profile Finder",
        status="COMPLETED",
        raw_payload={"linkedin_profile_url": url},
        raw_output={"verification_status": verification_status, "mx_status": mx_status}
    )
    return profile

def crawl_linkedin_icp_profiles(db: Session) -> Dict[str, Any]:
    """
    Re-verifies the HTTP-liveness of every LinkedIn profile currently stored
    (all of which were added manually with real data - no fabrication).
    Does NOT invent or seed any new profiles.
    """
    logger.info("Re-verifying stored LinkedIn ICP profile URLs...")
    all_profiles = db.query(LinkedInProfileDB).order_by(LinkedInProfileDB.created_at.desc()).all()

    verified_results = []
    for prof in all_profiles:
        url_res = verify_linkedin_url(prof.linkedin_profile_url)
        if url_res.get("valid") is True:
            prof.linkedin_url_verification_status = "VERIFIED_LIVE"
        elif url_res.get("valid") is False:
            prof.linkedin_url_verification_status = "VERIFICATION_FAILED"
        else:
            prof.linkedin_url_verification_status = "UNVERIFIED"
        verified_results.append({
            "name": prof.full_name,
            "url": prof.linkedin_profile_url,
            "http_status": url_res["http_status"],
            "status": prof.linkedin_url_verification_status
        })

    if all_profiles:
        db.commit()

    log_telemetry_event(
        tool_name="LinkedIn Extraction Engine",
        status="COMPLETED",
        raw_payload={"checked_count": len(all_profiles)},
        raw_output={"profiles": verified_results[:5]}
    )

    return {
        "status": "completed",
        "total_icp_profiles": len(all_profiles),
        "re_verified": len(all_profiles)
    }
