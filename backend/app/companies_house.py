"""
UK Companies House discovery engine.

Companies House is the UK's official company registry. Its REST API is
free - registration required, zero cost, not a paid data provider - and
gives:
  - Real, searchable SIC (industry) codes, so unlike SEC EDGAR (US-only,
    no clean industry filter) this can actually target "automotive /
    industrial machinery / electrical & electronics manufacturers" by real
    government classification, not a keyword guess.
  - Real, legally-filed company officers (directors/secretaries) - the same
    honest category as SEC Form D's "related persons": government-filed,
    citable, but NOT auto-escalated to an outreach contact. A name/role
    here is supporting evidence, not a verified way to reach that person.

Requires COMPANIES_HOUSE_API_KEY (see app.config) - without one, every
function here returns empty rather than guessing or failing loudly. This
module has NOT been exercised against a live key as of writing - the shape
follows Companies House's stable, documented public API, but treat it as
unverified until a real key is configured and a live pass is checked.
"""
import logging
from typing import Optional, Dict, Any, List
import httpx

from app.config import COMPANIES_HOUSE_API_KEY

logger = logging.getLogger("quanta.companies_house")

BASE_URL = "https://api.company-information.service.gov.uk"

# UK SIC 2007 codes for the industries in Connect1to1's stated ICP
# (automotive, industrial machinery, electrical/electronics manufacturing).
# Real government classification codes, not invented buckets.
SIC_CODES_BY_INDUSTRY = {
    "automotive": ["29100", "29200", "29310", "29320", "45111", "45112"],
    "industrial machinery": [
        "28110", "28120", "28130", "28140", "28150", "28210", "28220",
        "28230", "28240", "28250", "28290", "28920", "28930", "28940",
        "28950", "28960", "28990",
    ],
    "electrical": ["27110", "27120", "27200", "27310", "27320", "27330", "27400", "27500", "27900"],
    "electronics": ["26110", "26120", "26200", "26300", "26400", "26510", "26520", "26600", "26700", "26800"],
}

def _configured() -> bool:
    return bool(COMPANIES_HOUSE_API_KEY)

async def search_companies_by_sic(sic_codes: List[str], limit: int = 20) -> List[Dict[str, Any]]:
    """Real advanced search against Companies House, filtered to active companies with a matching SIC code."""
    if not _configured():
        logger.info("COMPANIES_HOUSE_API_KEY not configured - skipping (no guessed results).")
        return []

    results = []
    try:
        async with httpx.AsyncClient(timeout=10.0, auth=(COMPANIES_HOUSE_API_KEY, "")) as client:
            for sic in sic_codes:
                resp = await client.get(
                    f"{BASE_URL}/advanced-search/companies",
                    params={"sic_codes": sic, "company_status": "active", "size": limit},
                )
                if resp.status_code != 200:
                    logger.warning(f"Companies House search HTTP {resp.status_code} for SIC {sic}")
                    continue
                data = resp.json()
                for item in data.get("items", []):
                    results.append({
                        "company_number": item.get("company_number"),
                        "company_name": item.get("company_name"),
                        "sic_codes": item.get("sic_codes", []),
                        "address": item.get("registered_office_address", {}),
                        "date_of_creation": item.get("date_of_creation"),
                    })
    except Exception as e:
        logger.warning(f"Companies House search failed: {e}")
    # De-dupe by company_number across the multiple SIC queries
    seen = {}
    for r in results:
        seen[r["company_number"]] = r
    return list(seen.values())[:limit]

async def get_company_officers(company_number: str) -> List[Dict[str, Any]]:
    """Real, legally-filed officers (directors/secretaries) for one company."""
    if not _configured():
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0, auth=(COMPANIES_HOUSE_API_KEY, "")) as client:
            resp = await client.get(f"{BASE_URL}/company/{company_number}/officers")
            if resp.status_code != 200:
                return []
            data = resp.json()
            return [
                {"name": o.get("name"), "role": o.get("officer_role"), "appointed_on": o.get("appointed_on")}
                for o in data.get("items", [])
                if o.get("resigned_on") is None  # only current officers
            ]
    except Exception as e:
        logger.debug(f"Companies House officers fetch failed for {company_number}: {e}")
        return []

async def discover_from_companies_house(db, industries: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Discovery pass: real active UK companies matching real SIC codes for the
    given industry keywords. Companies House doesn't publish a website field,
    so unlike SEC EDGAR this can't resolve a verified domain and therefore
    does NOT create/attach a companies-table row (that table is domain-keyed
    by design - see app.companies.normalize_domain). Instead this stores each
    find as a standalone signal citing the real Companies House profile URL,
    with the real company name/number/SIC codes/officers in its metadata -
    the same pattern app.outsourcing_crawler already uses for "real find, no
    confirmed company domain yet". A human who confirms a real domain for one
    of these can attach it properly via POST /api/v1/companies/seed.
    """
    from app.models import ExtensionSignalDB
    from app.deduplication import is_duplicate_signal, is_duplicate_citation
    from app.scoring import calculate_multi_factor_intent_score

    if not _configured():
        return {"status": "not_configured", "reason": "COMPANIES_HOUSE_API_KEY not set - see app.config", "signals_created": 0}

    industries = industries or list(SIC_CODES_BY_INDUSTRY.keys())
    sic_codes = []
    for ind in industries:
        sic_codes.extend(SIC_CODES_BY_INDUSTRY.get(ind.lower(), []))
    sic_codes = list(set(sic_codes))
    if not sic_codes:
        return {"status": "completed", "reason": "No matching SIC codes for given industries", "signals_created": 0}

    companies_found = await search_companies_by_sic(sic_codes, limit=30)
    signals_created = 0
    citation_host = "find-and-update.company-information.service.gov.uk"

    for item in companies_found:
        company_number = item["company_number"]
        profile_url = f"https://{citation_host}/company/{company_number}"

        if is_duplicate_signal(company_number, "UK_REGISTRY_MATCH") or is_duplicate_citation(profile_url):
            continue

        officers = await get_company_officers(company_number)

        score_res = calculate_multi_factor_intent_score({})
        db_signal = ExtensionSignalDB(
            domain=citation_host,  # real citation host, NOT a guess at the company's own domain
            company=item["company_name"],
            url=profile_url,
            event_type="UK_REGISTRY_MATCH",
            intent_score=score_res["intent_score"],
            source="uk_companies_house",
            geo_location="United Kingdom",
            browser_fingerprint="UK Companies House SIC Discovery",
            enrichment_metadata=__import__("json").dumps({
                "company_number": company_number,
                "company_name": item["company_name"],
                "sic_codes": item.get("sic_codes"),
                "registered_address": item.get("address"),
                "officers_per_companies_house": officers,
                "citation": profile_url,
                "note": "No verified website domain from this source - confirm the real domain and add it via POST /api/v1/companies/seed to start real hiring/funding monitoring. Officer names are real/government-filed, not auto-promoted to a contact record.",
            }),
            company_id=None,
            demo_sample=False,
        )
        db.add(db_signal)
        signals_created += 1

    if signals_created:
        db.commit()

    return {
        "status": "completed",
        "sic_codes_searched": sic_codes,
        "companies_found": len(companies_found),
        "signals_created": signals_created,
    }
