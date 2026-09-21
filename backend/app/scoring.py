import logging
from typing import Dict, Any, List

logger = logging.getLogger("quanta.scoring")

def calculate_multi_factor_intent_score(telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    QUANTA 8-Factor Behavioral Intent Scoring Engine:
    Calculates weighted intent_score (0-99) from whatever real signals are present.
    Unlike earlier versions, there is no artificial floor - a record with no real
    signals attached scores low, not "70 minimum". Every factor below only awards
    points when the caller passed real, observed data - never a guessed default.
    1. Hiring velocity (real Greenhouse/Lever job posts)
    2. Tech stack shifts (only if actually detected)
    3. Funding rounds (only if actually sourced from a real feed)
    4. Pricing page dwell time (only from real extension/pixel telemetry)
    5. Multi-IP cluster behavior (only from real extension/pixel telemetry)
    6. Buyer persona detection (only if a real submitted/known role)
    7. Executive hires (only if actually observed)
    8. Competitor research (only if actually observed)
    """
    base_score = 20.0
    breakdown = {}

    # 1. Hiring Velocity (+3 to +12 pts)
    hiring_roles = telemetry.get("hiring_roles_count", 0) or 0
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
    tech_shifts = telemetry.get("tech_stack_changes_count", 0) or 0
    if tech_shifts >= 3:
        tech_score = 15.0
    elif tech_shifts >= 1:
        tech_score = 8.0
    else:
        tech_score = 0.0
    breakdown["tech_stack_shifts"] = tech_score

    # 3. Funding Rounds (+5 to +18 pts)
    funding_round = (telemetry.get("funding_round") or "").lower()
    if any(tier in funding_round for tier in ["series b", "series c", "growth"]):
        funding_score = 18.0
    elif any(tier in funding_round for tier in ["series a", "seed", "regulation d", "reg d", "private placement"]):
        funding_score = 12.0
    else:
        funding_score = 0.0
    breakdown["funding_rounds"] = funding_score

    # 4. Pricing Dwell Time (+5 to +16 pts)
    dwell_seconds = telemetry.get("dwell_time_seconds", 0) or 0
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
    concurrent_ips = telemetry.get("concurrent_hq_ips", 0) or 0
    if concurrent_ips >= 4:
        cluster_score = 15.0
    elif concurrent_ips >= 2:
        cluster_score = 8.0
    else:
        cluster_score = 0.0
    breakdown["multi_ip_cluster"] = cluster_score

    # 6. Buyer Persona (+4 to +10 pts)
    persona = (telemetry.get("persona_role") or "").lower()
    if any(title in persona for title in ["vp", "cmo", "cro", "ceo", "head"]):
        persona_score = 10.0
    elif any(title in persona for title in ["director", "lead", "manager"]):
        persona_score = 6.0
    else:
        persona_score = 0.0
    breakdown["buyer_persona"] = persona_score

    # 7. Executive Hires (+12 pts) - must be an explicit, real, observed event
    exec_hire = bool(telemetry.get("executive_hire_event", False))
    exec_score = 12.0 if exec_hire else 0.0
    breakdown["executive_hires"] = exec_score

    # 8. Competitor Research (+10 pts) - must be an explicit, real, observed event
    competitor_eval = bool(telemetry.get("competitor_evaluation", False))
    competitor_score = 10.0 if competitor_eval else 0.0
    breakdown["competitor_research"] = competitor_score

    total_raw = base_score + sum(breakdown.values())
    final_intent_score = min(99, max(0, int(round(total_raw))))

    return {
        "intent_score": final_intent_score,
        "base_score": base_score,
        "score_breakdown": breakdown
    }

def generate_real_problem_statement(domain: str, breakdown: Dict[str, float], telemetry: Dict[str, Any]) -> str:
    """
    Generates a problem statement strictly from real telemetry signals that were
    actually present. If nothing real was captured, says so plainly instead of
    inventing a generic "active evaluation" claim.
    """
    parts = []

    ips = telemetry.get("concurrent_hq_ips", 0) or 0
    dwell = telemetry.get("dwell_time_seconds", 0) or 0
    if ips > 1 or dwell > 30:
        parts.append(f"{ips} concurrent HQ IPs spent {max(1, dwell // 60)}m evaluating pricing matrix")

    tech = telemetry.get("tech_stack_changes_count", 0) or 0
    if tech > 0:
        parts.append("tech stack script modifications detected")

    hiring = telemetry.get("hiring_roles_count", 0) or 0
    if hiring > 0:
        parts.append(f"{hiring} active sales/growth hiring roles posted on a public job board")

    funding = telemetry.get("funding_round") or ""
    if funding:
        parts.append(f"{funding} capital raise referenced in a public source")

    if parts:
        return f"Signals on {domain}: " + " | ".join(parts) + "."
    return f"No verified intent signals currently captured for {domain}."
