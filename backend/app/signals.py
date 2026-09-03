import random
from datetime import datetime, timedelta
from typing import List
from app.models import SignalItem

SAMPLE_SIGNALS = [
    {
        "type": "TECHNOGRAPHIC_SHIFT",
        "company": "Stripe Competitor Corp",
        "signal_text": "Removed Hubspot tracking tag & installed custom intent webhook API on pricing path.",
        "intent_score": 96,
        "category": "High Buying Intent",
        "location": "San Francisco, CA",
        "action_playbook": "Trigger Executive Outreach + Slack Alert #growth-leads"
    },
    {
        "type": "EXECUTIVE_HIRE",
        "company": "Nexus B2B SaaS",
        "signal_text": "Appointed new VP of Revenue Operations (ex-Gong, ex-Salesforce).",
        "intent_score": 92,
        "category": "Org Expansion",
        "location": "Austin, TX",
        "action_playbook": "Dispatch RevOps playbook via Chrome Extension"
    },
    {
        "type": "COMPETITOR_RESEARCH",
        "company": "Apex Financial Software",
        "signal_text": "8 concurrent IPs from HQ domain spending 14m on pricing comparison table.",
        "intent_score": 98,
        "category": "Immediate Evaluation",
        "location": "London, UK",
        "action_playbook": "Auto-assign High-Priority SDR & send Slack Ping"
    },
    {
        "type": "JOB_POST_BURST",
        "company": "Vanguard Tech Inc.",
        "signal_text": "Posted 5 open roles for 'Outbound Sales Development' & 'Salesforce Admin' in 24 hours.",
        "intent_score": 88,
        "category": "Team Expansion",
        "location": "Chicago, IL",
        "action_playbook": "Enroll in RevOps Acceleration campaign"
    },
    {
        "type": "FUNDING_ANNOUNCEMENT",
        "company": "HyperScale AI",
        "signal_text": "Closed $18M Series A. Securing lead-gen infrastructure stack.",
        "intent_score": 94,
        "category": "Capital Deployment",
        "location": "New York, NY",
        "action_playbook": "Trigger Founders Outreach Playbook"
    }
]

def generate_live_signals() -> List[SignalItem]:
    signals = []
    now = datetime.now()
    for idx, s in enumerate(SAMPLE_SIGNALS):
        timestamp_str = (now - timedelta(minutes=idx * 7 + random.randint(1, 4))).strftime("%H:%M:%S UTC")
        signals.append(
            SignalItem(
                id=f"sig_{1000 + idx}",
                type=s["type"],
                company=s["company"],
                signal_text=s["signal_text"],
                timestamp=timestamp_str,
                intent_score=s["intent_score"],
                category=s["category"],
                location=s["location"],
                action_playbook=s["action_playbook"]
            )
        )
    return signals
