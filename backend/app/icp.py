import json
import logging
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import ICPProfileDB, CompanyDB

logger = logging.getLogger("quanta.icp")

def _loads(text: Optional[str], default):
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default

def get_active_icp(db: Session) -> Optional[ICPProfileDB]:
    return db.query(ICPProfileDB).filter(ICPProfileDB.is_active == True).first()

def create_icp_profile(db: Session, data: Dict[str, Any]) -> ICPProfileDB:
    if data.get("is_active"):
        # Only one active profile at a time - discovery/scoring always reads
        # a single unambiguous target definition.
        db.query(ICPProfileDB).update({ICPProfileDB.is_active: False})

    profile = ICPProfileDB(
        name=data["name"],
        is_active=bool(data.get("is_active", False)),
        industries=json.dumps(data.get("industries")) if data.get("industries") else None,
        geographies=json.dumps(data.get("geographies")) if data.get("geographies") else None,
        employee_min=data.get("employee_min"),
        employee_max=data.get("employee_max"),
        target_titles=json.dumps(data.get("target_titles")) if data.get("target_titles") else None,
        excluded_domains=json.dumps(data.get("excluded_domains")) if data.get("excluded_domains") else None,
        signal_weights=json.dumps(data.get("signal_weights")) if data.get("signal_weights") else None,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def list_icp_profiles(db: Session) -> List[ICPProfileDB]:
    return db.query(ICPProfileDB).order_by(ICPProfileDB.created_at.desc()).all()

def activate_icp_profile(db: Session, profile_id: int) -> Optional[ICPProfileDB]:
    profile = db.query(ICPProfileDB).filter(ICPProfileDB.id == profile_id).first()
    if not profile:
        return None
    db.query(ICPProfileDB).update({ICPProfileDB.is_active: False})
    profile.is_active = True
    db.commit()
    db.refresh(profile)
    return profile

def evaluate_company(company: CompanyDB, icp: ICPProfileDB) -> Dict[str, Any]:
    """
    Scores a company against an ICP using ONLY fields we actually know about
    the company. Never guesses a missing field to make the match look better
    or worse - unknown criteria are reported as unknown, not scored either way.
    Returns a percentage of the criteria we have real data for that actually
    matched, so a sparse company record honestly shows low confidence rather
    than a fabricated high score.
    """
    excluded = set(d.lower() for d in _loads(icp.excluded_domains, []))
    if company.domain.lower() in excluded:
        return {"fit": "EXCLUDED", "score": 0, "reasons": ["Domain is on this ICP's excluded list"]}

    reasons: List[str] = []
    known = 0
    matched = 0

    icp_industries = [i.lower() for i in _loads(icp.industries, [])]
    if icp_industries:
        if company.industry:
            known += 1
            company_industry = company.industry.lower()
            if any(kw in company_industry for kw in icp_industries):
                matched += 1
                reasons.append(f"industry '{company.industry}' matches ICP")
            else:
                reasons.append(f"industry '{company.industry}' does not match ICP industries")
        else:
            reasons.append("industry unknown - not scored")

    icp_geos = [g.lower() for g in _loads(icp.geographies, [])]
    if icp_geos:
        if company.country:
            known += 1
            if company.country.lower() in icp_geos:
                matched += 1
                reasons.append(f"country '{company.country}' matches ICP")
            else:
                reasons.append(f"country '{company.country}' does not match ICP geographies")
        else:
            reasons.append("country unknown - not scored")

    if icp.employee_min is not None or icp.employee_max is not None:
        if company.employee_count_value and str(company.employee_count_value).isdigit():
            known += 1
            n = int(company.employee_count_value)
            lo = icp.employee_min if icp.employee_min is not None else 0
            hi = icp.employee_max if icp.employee_max is not None else float("inf")
            if lo <= n <= hi:
                matched += 1
                reasons.append(f"employee count {n} in ICP range")
            else:
                reasons.append(f"employee count {n} outside ICP range {lo}-{hi}")
        else:
            reasons.append(f"employee count unknown (source: {company.employee_count_source or 'none'}) - not scored")

    if known == 0:
        return {"fit": "UNSCORED", "score": None, "reasons": reasons or ["No ICP-relevant company data available yet"]}

    pct = round(100 * matched / known)
    if pct >= 70:
        fit = "HIGH"
    elif pct >= 40:
        fit = "MEDIUM"
    else:
        fit = "LOW"

    return {"fit": fit, "score": pct, "reasons": reasons}

def score_and_store(db: Session, company: CompanyDB, icp: ICPProfileDB) -> CompanyDB:
    result = evaluate_company(company, icp)
    company.icp_fit = result["fit"]
    company.icp_score = result["score"]
    company.icp_reasons = json.dumps(result["reasons"])
    company.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(company)
    return company
