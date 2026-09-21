"""
SEC EDGAR Form D discovery engine.

Form D is the filing every US company makes when it raises private capital
under a Regulation D exemption (the overwhelming majority of startup seed/
Series A/B rounds). It is:
  - Free, no API key, no rate-limit tier to pay for.
  - Authoritative - it's a legal filing, not a scraped/guessed number.
  - Rich - real entity name, address, industry classification, offering
    amount, and the real names + roles of executive officers/directors
    (Form D legally requires listing "related persons").

This is QUANTA's primary no-paid-API discovery + funding-signal source:
a company appearing here just told the government it's raising money, which
is about as strong and verifiable a "buying intent is coming" signal as
exists without a paid data provider.

What this module does NOT do:
  - It does not invent an email for any related person. Their name/role is
    stored as supporting evidence (with a citation to the real filing), never
    escalated into an outreach-ready contact automatically.
  - It does not accept a guessed domain on faith. A candidate domain must
    resolve AND its real page content must actually reference the company
    name before we attach a signal to it. If nothing verifies, the filing is
    counted as "discovered but unresolved" and simply isn't stored - under-
    reporting is fine, mislabeling a random domain as this company is not.
"""
import re
import logging
import datetime
from typing import Optional, Dict, Any, List
import httpx
from bs4 import BeautifulSoup

from app.enrichment import domain_resolves

logger = logging.getLogger("quanta.sec_edgar")

SEC_HEADERS = {
    # SEC's fair-access policy requires a descriptive User-Agent with contact
    # info for automated requests - this is not a secret/key, it's how SEC
    # asks bots to identify themselves.
    "User-Agent": "QUANTA-DataPlatform (open-source ICP discovery; contact: research@virtusol.com)"
}

CORP_SUFFIXES = {
    "inc", "incorporated", "llc", "l.l.c", "corp", "corporation", "co",
    "company", "ltd", "limited", "lp", "llp", "pllc", "pbc", "plc"
}

def _significant_tokens(name: str) -> List[str]:
    """Strips corporate suffixes/punctuation to get the distinctive words of a company name."""
    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", name.lower())
    tokens = [t for t in clean.split() if t and t not in CORP_SUFFIXES and len(t) > 1]
    return tokens

def search_recent_form_d(days_back: int = 7, limit: int = 40) -> List[Dict[str, Any]]:
    """Real SEC EDGAR full-text search for recent Form D filings. No key required."""
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days_back)
    url = (
        "https://efts.sec.gov/LATEST/search-index"
        f"?forms=D&dateRange=custom&startdt={start.isoformat()}&enddt={end.isoformat()}"
    )
    results = []
    try:
        with httpx.Client(timeout=10.0, headers=SEC_HEADERS) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                logger.warning(f"SEC EDGAR search returned HTTP {resp.status_code}")
                return []
            data = resp.json()
            for hit in data.get("hits", {}).get("hits", [])[:limit]:
                src = hit.get("_source", {})
                names = src.get("display_names", [])
                if not names:
                    continue
                entity_name = re.sub(r"\s*\(CIK\s*\d+\)", "", names[0]).strip()
                cik = (src.get("ciks") or [None])[0]
                accession = src.get("adsh", "").replace("-", "")
                if not cik or not accession:
                    continue
                results.append({
                    "entity_name": entity_name,
                    "cik": cik,
                    "accession": accession,
                    "filing_date": src.get("file_date"),
                    "state": (src.get("biz_states") or [None])[0],
                    "filing_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=D",
                })
    except Exception as e:
        logger.warning(f"SEC EDGAR search failed: {e}")
        return []
    return results

def fetch_form_d_detail(cik: str, accession: str) -> Optional[Dict[str, Any]]:
    """Fetches and parses the real primary_doc.xml for one filing."""
    cik_num = str(int(cik))
    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession}/primary_doc.xml"
    try:
        with httpx.Client(timeout=10.0, headers=SEC_HEADERS) as client:
            resp = client.get(doc_url)
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "xml")

            entity_name_tag = soup.find("entityName")
            city_tag = soup.find("issuerAddress")
            industry_tag = soup.find("industryGroupType")
            amount_tag = soup.find("totalOfferingAmount")

            related_persons = []
            for person in soup.find_all("relatedPersonInfo"):
                first = person.find("firstName")
                last = person.find("lastName")
                relationships = [r.text for r in person.find_all("relationship")]
                if first and last:
                    related_persons.append({
                        "name": f"{first.text} {last.text}".strip(),
                        "roles": relationships,
                    })

            return {
                "entity_name": entity_name_tag.text.strip() if entity_name_tag else None,
                "city": city_tag.find("city").text if city_tag and city_tag.find("city") else None,
                "state": city_tag.find("stateOrCountryDescription").text if city_tag and city_tag.find("stateOrCountryDescription") else None,
                "industry_group": industry_tag.text.strip() if industry_tag else None,
                "offering_amount": amount_tag.text.strip() if amount_tag else None,
                "related_persons": related_persons,
                "filing_url": doc_url,
            }
    except Exception as e:
        logger.debug(f"SEC EDGAR detail fetch failed for CIK {cik}: {e}")
        return None

def resolve_and_verify_domain(entity_name: str) -> Optional[str]:
    """
    Tries the single most likely .com domain for a company name and only
    accepts it if the domain resolves AND its real homepage content actually
    references the company's distinctive name tokens. No guess is trusted
    without this verification - if it doesn't check out, returns None rather
    than attaching a possibly-wrong domain.
    """
    tokens = _significant_tokens(entity_name)
    if not tokens:
        return None

    candidate_domain = "".join(tokens) + ".com"
    if not domain_resolves(candidate_domain):
        return None

    try:
        with httpx.Client(timeout=6.0, follow_redirects=True) as client:
            resp = client.get(f"https://{candidate_domain}", headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                return None
            soup = BeautifulSoup(resp.text, "html.parser")
            page_text = (soup.title.text if soup.title else "") + " " + soup.get_text(" ")[:3000]
            page_text_norm = re.sub(r"[^a-z0-9]", "", page_text.lower())

            # Require every significant token of the company name to appear
            # somewhere in the real page content - strict on purpose.
            if all(tok in page_text_norm for tok in tokens):
                return candidate_domain
    except Exception:
        return None
    return None

async def discover_from_sec_edgar(db, icp=None, days_back: int = 7) -> Dict[str, Any]:
    """
    Full discovery pass: real recent Form D filings -> verified domain ->
    canonical Company row + a FUNDING_FILING signal citing the real filing.
    ICP-filters on industry_group when an active ICP with industries is given.
    """
    from app.companies import get_or_create_company, touch_last_signal
    from app.models import ExtensionSignalDB
    from app.deduplication import is_duplicate_signal
    from app.scoring import calculate_multi_factor_intent_score, generate_real_problem_statement
    import json as json_module

    icp_industries = []
    if icp and icp.industries:
        icp_industries = [i.lower() for i in json_module.loads(icp.industries)]

    filings = search_recent_form_d(days_back=days_back)
    discovered = 0
    domain_verified = 0
    signals_created = 0
    skipped_no_domain = 0

    for filing in filings:
        detail = fetch_form_d_detail(filing["cik"], filing["accession"])
        if not detail or not detail.get("entity_name"):
            continue
        discovered += 1

        if icp_industries and detail.get("industry_group"):
            if not any(kw in detail["industry_group"].lower() for kw in icp_industries):
                continue

        domain = resolve_and_verify_domain(detail["entity_name"])
        if not domain:
            skipped_no_domain += 1
            continue
        domain_verified += 1

        if is_duplicate_signal(domain, "FUNDING_FILING"):
            continue

        company = get_or_create_company(
            db, domain,
            company_name=detail["entity_name"],
            industry=detail.get("industry_group"),
            country="United States",
            source="sec_edgar_form_d",
        )
        if not company:
            continue

        telemetry = {"funding_round": "Regulation D private placement"}
        score_res = calculate_multi_factor_intent_score(telemetry)
        problem_stmt = generate_real_problem_statement(domain, score_res["score_breakdown"], telemetry)

        db_signal = ExtensionSignalDB(
            domain=domain,
            company=detail["entity_name"],
            url=detail["filing_url"],
            event_type="FUNDING_FILING",
            intent_score=score_res["intent_score"],
            source="sec_edgar_form_d",
            geo_location=detail.get("state"),
            browser_fingerprint="SEC EDGAR Form D Discovery",
            enrichment_metadata=json_module.dumps({
                "problem_statement": problem_stmt,
                "offering_amount_usd": detail.get("offering_amount"),
                "industry_group": detail.get("industry_group"),
                "officers_per_sec_filing": detail.get("related_persons", []),
                "citation": detail["filing_url"],
                "note": "Officer names/roles are real, from the legally-required Form D filing above. Not auto-promoted to a contact record - verify and add manually if pursuing outreach."
            }),
            company_id=company.id,
            demo_sample=False,
        )
        db.add(db_signal)
        touch_last_signal(db, company)
        signals_created += 1

    if signals_created:
        db.commit()

    return {
        "status": "completed",
        "filings_scanned": len(filings),
        "filings_with_detail": discovered,
        "domains_verified": domain_verified,
        "domains_unresolved_skipped": skipped_no_domain,
        "signals_created": signals_created,
    }
