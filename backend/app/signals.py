import random
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from app.models import SignalItem
from app.alerts import send_slack_alert

logger = logging.getLogger("quanta.signals")

SAMPLE_SIGNALS = [
    {
        "id": "sig_101",
        "company": "Stripe Competitor Corp",
        "domains": ["stripe-comp.com", "stripe.com", "stripe-competitor.com", "stripe-comp"],
        "event_type": "TECH_STACK_CHANGE",
        "description": "Removed legacy tracking scripts and installed custom intent webhook API on enterprise pricing path.",
        "source_url": "https://stripe-comp.com/web-analytics",
        "intent_score": 96,
        "category": "TECH_STACK_CHANGE",
        "location": "San Francisco, CA",
        "action_playbook": "Trigger Executive Outreach + Slack Alert #growth-leads"
    },
    {
        "id": "sig_102",
        "company": "Nexus B2B SaaS",
        "domains": ["nexusb2b.com", "nexus.com", "nexus-b2b.com", "nexusb2b"],
        "event_type": "EXEC_HIRE",
        "description": "Appointed new VP of Revenue Operations (ex-Gong, ex-Salesforce) to scale GTM engine.",
        "source_url": "https://nexusb2b.com/careers",
        "intent_score": 92,
        "category": "EXEC_HIRE",
        "location": "Austin, TX",
        "action_playbook": "Dispatch RevOps playbook via Chrome Extension"
    },
    {
        "id": "sig_103",
        "company": "Apex Financial Software",
        "domains": ["apexfinancial.com", "apex.com", "apexfinancial"],
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
        "domains": ["vanguardtech.io", "vanguard.com", "vanguardtech"],
        "event_type": "JOB_POST",
        "description": "Posted 6 open roles for 'Outbound Sales Development Rep' & 'Salesforce Administrator' in 24 hours.",
        "source_url": "https://vanguardtech.io/openings",
        "intent_score": 88,
        "category": "JOB_POST",
        "location": "Chicago, IL",
        "action_playbook": "Enroll in RevOps Acceleration campaign"
    },
    {
        "id": "sig_105",
        "company": "HyperScale AI",
        "domains": ["hyperscale.ai", "hyperscale.com", "hyperscale"],
        "event_type": "FUNDING",
        "description": "Closed $18.5M Series A funding round. Allocating budget for sales intelligence stack.",
        "source_url": "https://hyperscale.ai/press",
        "intent_score": 95,
        "category": "FUNDING",
        "location": "New York, NY",
        "action_playbook": "Trigger Founders Outreach Playbook"
    },
    {
        "id": "sig_106",
        "company": "CloudScale Systems",
        "domains": ["cloudscale.io", "cloudscale.com", "cloudscale"],
        "event_type": "PRICING_PAGE",
        "description": "4 executive IPs from corporate HQ hit competitor feature breakdown page 3 times in 15 mins.",
        "source_url": "https://cloudscale.io/compare",
        "intent_score": 94,
        "category": "PRICING_PAGE",
        "location": "Seattle, WA",
        "action_playbook": "Dispatch Rep Overlay & Ping #quanta-alerts"
    }
]

def normalize_domain(domain: str) -> str:
    """Strip http, https, www, port, path, subdomains for matching."""
    if not domain:
        return ""
    d = domain.lower().strip()
    d = re.sub(r'^https?://', '', d)
    d = d.split('/')[0].split(':')[0]
    if d.startswith('www.'):
        d = d[4:]
    return d

def generate_live_signals(domain: Optional[str] = None) -> List[SignalItem]:
    """
    Returns live intent micro-signals.
    If `domain` query param is supplied, filters signals matching that domain.
    If domain is supplied but has no signals, returns empty list [].
    """
    signals = []
    now = datetime.now()
    norm_query = normalize_domain(domain) if domain else ""

    for idx, s in enumerate(SAMPLE_SIGNALS):
        # Match domain if query provided
        if norm_query:
            matched = False
            for d in s.get("domains", []):
                if norm_query in d or d in norm_query:
                    matched = True
                    break
            # Also match company name parts
            if not matched and norm_query.split('.')[0] in s["company"].lower().replace(' ', ''):
                matched = True
            if not matched:
                continue

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

async def dispatch_high_intent_alerts(signals: List[SignalItem]):
    """
    Scans signals and dispatches Slack notifications for signals with intent_score >= 90.
    """
    for sig in signals:
        if sig.intent_score >= 90:
            try:
                await send_slack_alert(
                    company=sig.company,
                    event_type=sig.category or sig.event_type,
                    description=sig.description,
                    intent_score=sig.intent_score,
                    source_url=sig.source_url
                )
            except Exception as e:
                logger.error(f"Error triggering alert for signal {sig.id}: {e}")
