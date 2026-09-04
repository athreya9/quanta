import random
from datetime import datetime, timedelta
from typing import List
from app.models import SignalItem

SAMPLE_SIGNALS = [
    {
        "id": "sig_101",
        "company": "Stripe Competitor Corp",
        "event_type": "TECH_STACK_CHANGE",
        "description": "Removed legacy tracking scripts and installed custom intent webhook API on enterprise pricing path.",
        "source_url": "https://github.com/stripe-comp/web-analytics",
        "intent_score": 96,
        "category": "TECH_STACK_CHANGE",
        "location": "San Francisco, CA",
        "action_playbook": "Trigger Executive Outreach + Slack Alert #growth-leads"
    },
    {
        "id": "sig_102",
        "company": "Nexus B2B SaaS",
        "event_type": "EXEC_HIRE",
        "description": "Appointed new VP of Revenue Operations (ex-Gong, ex-Salesforce) to scale GTM engine.",
        "source_url": "https://linkedin.com/company/nexus-b2b/jobs",
        "intent_score": 92,
        "category": "EXEC_HIRE",
        "location": "Austin, TX",
        "action_playbook": "Dispatch RevOps playbook via Chrome Extension"
    },
    {
        "id": "sig_103",
        "company": "Apex Financial Software",
        "event_type": "PRICING_PAGE",
        "description": "8 concurrent IPs from corporate HQ spent 14 minutes evaluating enterprise tier pricing comparison matrix.",
        "source_url": "https://apexfinancial.com/pricing",
        "intent_score": 98,
        "category": "PRICING_PAGE",
        "location": "London, UK",
        "action_playbook": "Auto-assign High-Priority SDR & send Slack Ping"
    },
    {
        "id": "sig_104",
        "company": "Vanguard Tech Inc.",
        "event_type": "JOB_POST",
        "description": "Posted 6 open roles for 'Outbound Sales Development Rep' & 'Salesforce Administrator' in 24 hours.",
        "source_url": "https://careers.vanguardtech.io/openings",
        "intent_score": 88,
        "category": "JOB_POST",
        "location": "Chicago, IL",
        "action_playbook": "Enroll in RevOps Acceleration campaign"
    },
    {
        "id": "sig_105",
        "company": "HyperScale AI",
        "event_type": "FUNDING",
        "description": "Closed $18.5M Series A funding round. Allocating budget for sales intelligence stack.",
        "source_url": "https://techcrunch.com/hyperscale-ai-series-a",
        "intent_score": 95,
        "category": "FUNDING",
        "location": "New York, NY",
        "action_playbook": "Trigger Founders Outreach Playbook"
    },
    {
        "id": "sig_106",
        "company": "CloudScale Systems",
        "event_type": "PRICING_PAGE",
        "description": "4 executive IPs from corporate HQ hit competitor feature breakdown page 3 times in 15 mins.",
        "source_url": "https://cloudscale.io/compare",
        "intent_score": 94,
        "category": "PRICING_PAGE",
        "location": "Seattle, WA",
        "action_playbook": "Dispatch Rep Overlay & Ping #quanta-alerts"
    }
]

def generate_live_signals() -> List[SignalItem]:
    signals = []
    now = datetime.now()
    for idx, s in enumerate(SAMPLE_SIGNALS):
        time_offset = idx * 6 + random.randint(1, 3)
        detected_str = f"{time_offset}m ago" if time_offset > 0 else "Just now"
        timestamp_str = (now - timedelta(minutes=time_offset)).strftime("%H:%M:%S UTC")
        
        signals.append(
            SignalItem(
                id=s["id"],
                company=s["company"],
                event_type=s["event_type"],
                description=s["description"],
                signal_text=s["description"],
                source_url=s["source_url"],
                detected_at=detected_str,
                timestamp=timestamp_str,
                intent_score=s["intent_score"],
                category=s["category"],
                location=s["location"],
                action_playbook=s["action_playbook"]
            )
        )
    return signals
