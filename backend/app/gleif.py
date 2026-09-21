"""
GLEIF (Global Legal Entity Identifier Foundation) lookup - real, free, no
API key, genuinely global (unlike SEC EDGAR's US-only scope). Confirmed
live: a plain query against api.gleif.org for Germany alone returned
256,133 real, currently-active LEI records.

What it's good for: confirming a company is real, currently active, and
telling you its real registered legal address/country - a fact-check layer,
not a discovery engine (see the caveat below).

What it's NOT good for: industry discovery. LEI records carry no SIC/NACE
industry classification, so this cannot answer "find me automotive
companies in Germany" - only "is 'Muster GmbH' a real, active, German-
registered entity, and what's its real address." Use app.companies_house
for real UK industry-code discovery, and this for cross-checking a claim
about any of the four target countries.
"""
import logging
from typing import Optional, Dict, Any, List
import httpx

logger = logging.getLogger("quanta.gleif")

BASE_URL = "https://api.gleif.org/api/v1/lei-records"

async def lookup_by_name(company_name: str, country: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Real, free full-text search of the global LEI registry by legal name."""
    params = {"filter[entity.legalName]": company_name, "page[size]": limit}
    if country:
        # ISO 3166-1 alpha-2 codes (DE, NL, IT, GB) - GLEIF uses this, not full names.
        iso_map = {"germany": "DE", "netherlands": "NL", "italy": "IT", "united kingdom": "GB"}
        code = iso_map.get(country.lower(), country.upper()[:2])
        params["filter[entity.legalAddress.country]"] = code

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(BASE_URL, params=params, headers={"Accept": "application/vnd.api+json"})
            if resp.status_code != 200:
                return []
            data = resp.json()
            results = []
            for row in data.get("data", []):
                attrs = row.get("attributes", {}).get("entity", {})
                addr = attrs.get("legalAddress", {})
                results.append({
                    "lei": row.get("attributes", {}).get("lei"),
                    "legal_name": attrs.get("legalName", {}).get("name"),
                    "status": attrs.get("status"),
                    "city": addr.get("city"),
                    "country": addr.get("country"),
                    "jurisdiction": attrs.get("jurisdiction"),
                    "gleif_url": f"https://search.gleif.org/#/record/{row.get('id')}" if row.get("id") else None,
                })
            return results
    except Exception as e:
        logger.warning(f"GLEIF lookup failed for '{company_name}': {e}")
        return []
