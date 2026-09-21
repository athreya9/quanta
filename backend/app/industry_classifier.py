"""
Real (if imperfect) industry classification from a company's own homepage.

Company records that enter via SEC EDGAR arrive with a real industry_group
from the filing. Companies that enter via a seed list or a job-board crawl
often don't - and an ICP rule keyed on "industry" silently can't score them,
which starves the whole system of matches for no real reason.

This module closes that gap the honest way: fetch the company's own real
homepage, look for real keyword evidence of what business they're actually
in, and only assign a label when there's enough of it. No paid
classification API, no guessing from the domain name alone - it's reading
what the company itself publicly says about itself. If nothing matches with
enough confidence, industry stays None rather than getting a forced guess.
"""
import logging
from typing import Optional, Dict, List
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("quanta.industry_classifier")

# Keyword sets are deliberately narrow/specific rather than broad, to keep
# false-positive matches rare. Extend this as new ICPs need new categories -
# same "registry, not hardcoded logic" pattern as app.icp_fields.
INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
    "Manufacturing & Industrial": [
        "precision machining", "cnc machining", "injection molding", "fabrication",
        "manufacturer", "manufacturing facility", "industrial equipment", "supply chain",
        "contract manufacturer", "tooling", "metal stamping", "assembly line",
    ],
    "Healthcare": [
        "patient care", "clinic", "medical center", "dental practice", "healthcare provider",
        "physician", "urgent care", "telehealth", "appointment booking", "hipaa",
    ],
    "Real Estate": [
        "real estate agency", "property management", "realtor", "listings", "brokerage",
        "residential property", "commercial real estate",
    ],
    "Hospitality": [
        "hotel", "resort", "hospitality group", "restaurant group", "reservations",
        "guest experience", "booking.com", "front desk",
    ],
    "Home Services": [
        "hvac", "plumbing service", "electrician", "home repair", "pest control",
        "landscaping service", "roofing contractor", "cleaning service",
    ],
    "SaaS & Software": [
        "software as a service", "saas platform", "api documentation", "free trial",
        "cloud platform", "integrations", "developer docs",
    ],
    "Financial Services": [
        "fintech", "payments platform", "banking", "investment fund", "asset management",
        "insurance provider", "wealth management",
    ],
}

async def infer_industry_from_homepage(domain: str) -> Optional[str]:
    """
    Fetches the real homepage and returns the best-matching industry label,
    or None if no category has enough keyword evidence (>=2 distinct hits).
    """
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            resp = await client.get(f"https://{domain}", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            text = ((soup.title.text if soup.title else "") + " " + soup.get_text(" "))[:5000].lower()
    except Exception as e:
        logger.debug(f"Industry classification fetch failed for {domain}: {e}")
        return None

    best_label = None
    best_hits = 1  # require at least 2 distinct keyword hits to assign anything
    for label, keywords in INDUSTRY_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_label = label

    return best_label
