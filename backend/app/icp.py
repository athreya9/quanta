import json
import logging
import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import ICPProfileDB, CompanyDB, CompanyICPScoreDB
from app.icp_fields import resolve_field

logger = logging.getLogger("quanta.icp")

def _loads(text: Optional[str], default):
    if not text:
        return default
    try:
        return json.loads(text)
    except Exception:
        return default

# ============ CRUD ============

def create_icp_profile(db: Session, data: Dict[str, Any]) -> ICPProfileDB:
    criteria = data.get("criteria")
    profile = ICPProfileDB(
        name=data["name"],
        description=data.get("description"),
        is_active=data.get("is_active", True),
        criteria=json.dumps(criteria) if criteria else None,
        excluded_domains=json.dumps(data.get("excluded_domains")) if data.get("excluded_domains") else None,
        outreach_pitch=data.get("outreach_pitch"),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

def clone_icp_profile(db: Session, profile_id: int, new_name: str) -> Optional[ICPProfileDB]:
    """Duplicates an existing project's ICP as a starting point for a new one."""
    original = db.query(ICPProfileDB).filter(ICPProfileDB.id == profile_id).first()
    if not original:
        return None
    clone = ICPProfileDB(
        name=new_name,
        description=f"Cloned from '{original.name}'" + (f": {original.description}" if original.description else ""),
        is_active=True,
        criteria=original.criteria,
        excluded_domains=original.excluded_domains,
        outreach_pitch=original.outreach_pitch,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone

def list_icp_profiles(db: Session, active_only: bool = False) -> List[ICPProfileDB]:
    query = db.query(ICPProfileDB)
    if active_only:
        query = query.filter(ICPProfileDB.is_active == True)
    return query.order_by(ICPProfileDB.created_at.desc()).all()

def get_icp_profile(db: Session, profile_id: int) -> Optional[ICPProfileDB]:
    return db.query(ICPProfileDB).filter(ICPProfileDB.id == profile_id).first()

def set_icp_active(db: Session, profile_id: int, active: bool) -> Optional[ICPProfileDB]:
    profile = get_icp_profile(db, profile_id)
    if not profile:
        return None
    profile.is_active = active
    db.commit()
    db.refresh(profile)
    return profile

def active_industry_keywords(db: Session) -> List[str]:
    """
    Unions the 'industry' criterion values of every active profile. This is
    what discovery workers (SEC EDGAR etc.) use to decide what's worth
    looking at - cast one net wide enough for every current project, while
    scoring stays separate and precise per profile.
    """
    keywords = set()
    for profile in list_icp_profiles(db, active_only=True):
        for rule in _loads(profile.criteria, []):
            if rule.get("field") == "industry" and rule.get("value"):
                val = rule["value"]
                vals = val if isinstance(val, list) else [val]
                keywords.update(v.lower() for v in vals if isinstance(v, str))
    return list(keywords)

# ============ Rule evaluation ============

def _op_match(operator: str, known: Any, rule_value: Any) -> Optional[bool]:
    """Returns True/False, or None if the operator/value combination can't be evaluated."""
    try:
        if operator == "is_true":
            return bool(known) is True
        if operator == "is_false":
            return bool(known) is False

        if known is None:
            return None

        if operator == "contains_any":
            rule_list = rule_value if isinstance(rule_value, list) else [rule_value]
            if isinstance(known, list):
                known_norm = [str(k).lower() for k in known]
                return any(str(rv).lower() in kn for rv in rule_list for kn in known_norm)
            known_norm = str(known).lower()
            return any(str(rv).lower() in known_norm for rv in rule_list)

        if operator == "contains_all":
            rule_list = rule_value if isinstance(rule_value, list) else [rule_value]
            if isinstance(known, list):
                known_norm = [str(k).lower() for k in known]
                return all(any(str(rv).lower() in kn for kn in known_norm) for rv in rule_list)
            known_norm = str(known).lower()
            return all(str(rv).lower() in known_norm for rv in rule_list)

        if operator == "in":
            rule_list = rule_value if isinstance(rule_value, list) else [rule_value]
            return str(known).lower() in [str(v).lower() for v in rule_list]

        if operator == "equals":
            return str(known).lower() == str(rule_value).lower()

        if operator == "between":
            lo, hi = rule_value[0], rule_value[1]
            lo = lo if lo is not None else float("-inf")
            hi = hi if hi is not None else float("inf")
            return lo <= float(known) <= hi

        if operator == "gte":
            return float(known) >= float(rule_value)

        if operator == "lte":
            return float(known) <= float(rule_value)
    except Exception:
        return None
    return None

def evaluate_company(company: CompanyDB, icp: ICPProfileDB, db: Session) -> Dict[str, Any]:
    """
    Scores a company against one ICP's rules using ONLY facts we actually
    have (via app.icp_fields). A rule whose field resolves to None is
    reported as unknown and doesn't count toward the score either way. The
    result is the percentage of *evaluable weight* that actually matched -
    a company with little known data honestly shows low confidence rather
    than a fabricated score.
    """
    excluded = set(d.lower() for d in _loads(icp.excluded_domains, []))
    if company.domain.lower() in excluded:
        return {"fit": "EXCLUDED", "score": 0, "reasons": ["Domain is on this ICP's excluded list"]}

    rules = _loads(icp.criteria, [])
    if not rules:
        return {"fit": "UNSCORED", "score": None, "reasons": ["This ICP profile has no criteria defined yet"]}

    reasons: List[str] = []
    known_weight = 0.0
    matched_weight = 0.0

    for rule in rules:
        field = rule.get("field")
        operator = rule.get("operator")
        weight = float(rule.get("weight", 10.0))
        known_value = resolve_field(field, company, db)

        if known_value is None or (isinstance(known_value, list) and not known_value):
            reasons.append(f"{field}: unknown - not scored")
            continue

        result = _op_match(operator, known_value, rule.get("value"))
        if result is None:
            reasons.append(f"{field}: could not evaluate '{operator}' - not scored")
            continue

        known_weight += weight
        if result:
            matched_weight += weight
            reasons.append(f"{field}={known_value!r} matches rule ({operator})")
        else:
            reasons.append(f"{field}={known_value!r} does not match rule ({operator})")

    if known_weight == 0:
        return {"fit": "UNSCORED", "score": None, "reasons": reasons or ["No ICP-relevant company data available yet"]}

    pct = round(100 * matched_weight / known_weight)
    if pct >= 70:
        fit = "HIGH"
    elif pct >= 40:
        fit = "MEDIUM"
    else:
        fit = "LOW"

    return {"fit": fit, "score": pct, "reasons": reasons}

def score_and_store(db: Session, company: CompanyDB, icp: ICPProfileDB) -> CompanyICPScoreDB:
    result = evaluate_company(company, icp, db)
    existing = db.query(CompanyICPScoreDB).filter(
        CompanyICPScoreDB.company_id == company.id,
        CompanyICPScoreDB.icp_profile_id == icp.id,
    ).first()
    if existing:
        existing.fit = result["fit"]
        existing.score = result["score"]
        existing.reasons = json.dumps(result["reasons"])
        existing.computed_at = datetime.datetime.utcnow()
        row = existing
    else:
        row = CompanyICPScoreDB(
            company_id=company.id,
            icp_profile_id=icp.id,
            fit=result["fit"],
            score=result["score"],
            reasons=json.dumps(result["reasons"]),
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
