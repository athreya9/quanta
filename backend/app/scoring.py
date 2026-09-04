import logging
from typing import Dict, Any, List

logger = logging.getLogger("quanta.scoring")

def calculate_multi_factor_intent_score(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    QUANTA 8-Factor Behavioral Intent Scoring Engine:
    Calculates weighted intent_score (70–99) based on real signals:
    1. Hiring velocity (Greenhouse/LinkedIn job posts)
    2. Tech stack shifts (BuiltWith/Wappalyzer detections)
    3. Funding rounds (Crunchbase funding signals)
    4. Pricing page dwell time (>3 mins or multiple visits)
    5. Multi-IP cluster behavior (multiple HQ IPs visiting pricing/compare path)
    6. Buyer persona detection (VP/Executive level interactions)
    7. Executive hires (VP RevOps, CMO, CRO appointees)
    8. Competitor research (visiting competitor comparison matrices)
    """
    base_score = 70.0
    breakdown = {}

    # 1. Hiring Velocity (+3 to +12 pts)
    hiring_roles = telemetry.get("hiring_roles_count", 0)
    if hiring_roles >= 5:
        hiring_score = 12.0
    elif hiring_roles >= 2:
        hiring_score = 7.0
    elif hiring_roles >= 1:
        hiring_score = 4.0
    else:
        hiring_score = 0.0
    breakdown["hiring_velocity"] = hiring_score

    # 2. Tech Stack Shifts (+4 to +15 pts)
    tech_shifts = telemetry.get("tech_stack_changes_count", 0)
    if tech_shifts >= 3:
        tech_score = 15.0
    elif tech_shifts >= 1:
        tech_score = 8.0
    else:
        tech_score = 0.0
    breakdown["tech_stack_shifts"] = tech_score

    # 3. Funding Rounds (+5 to +18 pts)
    funding_round = telemetry.get("funding_round", "").lower()
    if any(tier in funding_round for tier in ["series b", "series c", "growth"]):
        funding_score = 18.0
    elif any(tier in funding_round for tier in ["series a", "seed"]):
        funding_score = 12.0
    else:
        funding_score = 0.0
    breakdown["funding_rounds"] = funding_score

    # 4. Pricing Dwell Time (+5 to +16 pts)
    dwell_seconds = telemetry.get("dwell_time_seconds", 0)
    if dwell_seconds >= 300:
        dwell_score = 16.0
    elif dwell_seconds >= 120:
        dwell_score = 10.0
    elif dwell_seconds >= 30:
        dwell_score = 5.0
    else:
        dwell_score = 0.0
    breakdown["pricing_dwell_time"] = dwell_score

    # 5. Multi-IP Cluster Behavior (+6 to +15 pts)
    concurrent_ips = telemetry.get("concurrent_hq_ips", 1)
    if concurrent_ips >= 4:
        cluster_score = 15.0
    elif concurrent_ips >= 2:
        cluster_score = 8.0
    else:
        cluster_score = 0.0
    breakdown["multi_ip_cluster"] = cluster_score

    # 6. Buyer Persona (+4 to +10 pts)
    persona = telemetry.get("persona_role", "").lower()
    if any(title in persona for title in ["vp", "cmo", "cro", "ceo", "head"]):
        persona_score = 10.0
    elif any(title in persona for title in ["director", "lead", "manager"]):
        persona_score = 6.0
    else:
        persona_score = 0.0
    breakdown["buyer_persona"] = persona_score

    # 7. Executive Hires (+5 to +12 pts)
    exec_hire = telemetry.get("executive_hire_event", False)
    exec_score = 12.0 if exec_hire else 0.0
    breakdown["executive_hires"] = exec_score

    # 8. Competitor Research (+4 to +10 pts)
    competitor_eval = telemetry.get("competitor_evaluation", False)
    competitor_score = 10.0 if competitor_eval else 0.0
    breakdown["competitor_research"] = competitor_score

    # Total Raw Score
    total_raw = base_score + sum(breakdown.values())
    final_intent_score = min(99, max(70, int(round(total_raw))))

    return {
        "intent_score": final_intent_score,
        "base_score": base_score,
        "score_breakdown": breakdown
    }
