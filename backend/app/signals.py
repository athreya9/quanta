import random
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from app.models import SignalItem
from app.alerts import send_slack_alert

logger = logging.getLogger("quanta.signals")

# Real Signal Sources: Tech Stack (BuiltWith/Wappalyzer), Hiring (Greenhouse/LinkedIn), Pricing Telemetry, Exec Hires, Crunchbase Funding
SAMPLE_SIGNALS = [
    {
        "id": "sig_101",
        "company": "Stripe Competitor Corp",
        "domain": "stripe-comp.com",
        "domains": ["stripe-comp.com", "stripe.com", "stripe-competitor.com", "stripe-comp"],
        "event_type": "TECH_STACK_CHANGE",
        "description": "Installed enterprise intent API webhook & removed legacy tracking via Wappalyzer detection.",
        "source_url": "https://stripe-comp.com/web-analytics",
        "intent_score": 96,
        "category": "TECH_STACK_CHANGE",
        "source": "backend_ingestion",
        "location": "San Francisco, CA",
        "geo_location": "San Francisco, CA, USA",
        "action_playbook": "Trigger Executive Outreach + Slack Alert #growth-leads",
        "tech_stack_signals": ["Installed QUANTA Intent Webhook API", "Removed Legacy Google Universal Analytics", "Added Segment Enterprise CDN"],
        "hiring_signals": ["Senior Sales Engineer (Greenhouse)", "Outbound SDR Lead (LinkedIn)"],
        "pricing_page_behavior": "4 concurrent HQ IPs spent 18 mins on /enterprise-pricing matrix",
        "funding_signals": "Series B ($35M) led by Sequoia Capital"
    },
    {
        "id": "sig_102",
        "company": "Nexus B2B SaaS",
        "domain": "nexusb2b.com",
        "domains": ["nexusb2b.com", "nexus.com", "nexus-b2b.com", "nexusb2b"],
        "event_type": "EXEC_HIRE",
        "description": "Appointed new VP of Revenue Operations (ex-Gong, ex-Salesforce) to scale outbound engine.",
        "source_url": "https://linkedin.com/company/nexus-b2b/jobs",
        "intent_score": 92,
        "category": "EXEC_HIRE",
        "source": "backend_ingestion",
        "location": "Austin, TX",
        "geo_location": "Austin, TX, USA",
        "action_playbook": "Dispatch RevOps acceleration playbook via Chrome Extension",
        "tech_stack_signals": ["Salesforce Enterprise CRM", "Outreach.io", "Gong.io"],
        "hiring_signals": ["VP of Revenue Operations (LinkedIn Public Signal)", "Head of SDRs (Greenhouse)"],
        "pricing_page_behavior": "6 visits to competitor breakdown table in past 24 hours",
        "funding_signals": "Series A ($12M) - Accelerating RevOps tooling"
    },
    {
        "id": "sig_103",
        "company": "Apex Financial Software",
        "domain": "apexfinancial.com",
        "domains": ["apexfinancial.com", "apex.com", "apexfinancial"],
        "event_type": "PRICING_PAGE",
        "description": "8 concurrent IPs from corporate HQ spent 14 minutes evaluating enterprise tier pricing comparison matrix.",
        "source_url": "https://apexfinancial.com/pricing",
        "intent_score": 98,
        "category": "PRICING_PAGE",
        "source": "pricing_page",
        "location": "London, UK",
        "geo_location": "London, Greater London, UK",
        "action_playbook": "Auto-assign High-Priority SDR & send Slack Ping",
        "tech_stack_signals": ["Marketo Enterprise", "HubSpot Sales Hub Pro", "React 18 PWA"],
        "hiring_signals": ["Enterprise SDR - FinTech (Indeed)"],
        "pricing_page_behavior": "8 concurrent IPs from corporate HQ spent 14 minutes evaluating enterprise tier pricing comparison matrix",
        "funding_signals": "Growth Equity Round ($45M)"
    },
    {
        "id": "sig_104",
        "company": "Vanguard Tech Inc.",
        "domain": "vanguardtech.io",
        "domains": ["vanguardtech.io", "vanguard.com", "vanguardtech"],
        "event_type": "JOB_POST",
        "description": "Posted 6 open roles for 'Outbound Sales Development Rep' & 'Salesforce Administrator' on Greenhouse.",
        "source_url": "https://vanguardtech.io/openings",
        "intent_score": 88,
        "category": "JOB_POST",
        "source": "backend_ingestion",
        "location": "Chicago, IL",
        "geo_location": "Chicago, IL, USA",
        "action_playbook": "Enroll in RevOps Acceleration campaign",
        "tech_stack_signals": ["Salesforce CRM", "HubSpot Marketing Pro"],
        "hiring_signals": ["6 open roles on Greenhouse & Indeed in 24 hours (Outbound SDR, RevOps Mgr)"],
        "pricing_page_behavior": "2 pricing page visits from HQ domain",
        "funding_signals": "Series A ($10M)"
    },
    {
        "id": "sig_105",
        "company": "HyperScale AI",
        "domain": "hyperscale.ai",
        "domains": ["hyperscale.ai", "hyperscale.com", "hyperscale"],
        "event_type": "FUNDING",
        "description": "Closed $18.5M Series A funding round on Crunchbase RSS feed. Allocating budget for sales intelligence stack.",
        "source_url": "https://hyperscale.ai/press",
        "intent_score": 95,
        "category": "FUNDING",
        "source": "backend_ingestion",
        "location": "New York, NY",
        "geo_location": "New York, NY, USA",
        "action_playbook": "Trigger Founders Outreach Playbook",
        "tech_stack_signals": ["Next.js", "Python FastAPI", "Segment Analytics"],
        "hiring_signals": ["Head of Growth", "Enterprise Account Executive"],
        "pricing_page_behavior": "5 pricing page visits from investor & executive IPs",
        "funding_signals": "Closed $18.5M Series A round (Crunchbase Public Signal)"
    },
    {
        "id": "sig_106",
        "company": "CloudScale Systems",
        "domain": "cloudscale.io",
        "domains": ["cloudscale.io", "cloudscale.com", "cloudscale"],
        "event_type": "PRICING_PAGE",
        "description": "4 executive IPs from corporate HQ hit competitor feature breakdown page 3 times in 15 mins via extension telemetry.",
        "source_url": "https://cloudscale.io/compare",
        "intent_score": 94,
        "category": "PRICING_PAGE",
        "source": "chrome_extension",
        "location": "Seattle, WA",
        "geo_location": "Seattle, WA, USA",
        "action_playbook": "Dispatch Rep Overlay & Ping #quanta-alerts",
        "tech_stack_signals": ["BuiltWith Detection: Wappalyzer Webhooks", "HubSpot Sales Hub"],
        "hiring_signals": ["Senior Sales Development Rep (LinkedIn)"],
        "pricing_page_behavior": "4 executive IPs from corporate HQ hit competitor feature breakdown page 3 times in 15 mins",
        "funding_signals": "Series C ($60M)"
    }
]

def normalize_domain(domain: str) -> str:
    """Strip http, https, www, port, path, subdomains for domain-to-company matching."""
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
    Returns enriched intent micro-signals.
    Filter by query parameter ?domain=<domain_name> if provided.
    """
    signals = []
    now = datetime.now()
    norm_query = normalize_domain(domain) if domain else ""

    for idx, s in enumerate(SAMPLE_SIGNALS):
        # Filter domain if query provided
        if norm_query:
            matched = False
            for d in s.get("domains", []):
                if norm_query in d or d in norm_query:
                    matched = True
                    break
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
                domain=s.get("domain", s.get("domains", [""])[0]),
                event_type=s["event_type"],
                description=s["description"],
                signal_text=s["description"],
                source_url=s["source_url"],
                detected_at=detected_str,
                timestamp=timestamp_str,
                intent_score=s["intent_score"],
                category=s["category"],
                source=s.get("source", "backend_ingestion"),
                location=s["location"],
                geo_location=s.get("geo_location", s["location"]),
                action_playbook=s["action_playbook"],
                tech_stack_signals=s.get("tech_stack_signals"),
                hiring_signals=s.get("hiring_signals"),
                pricing_page_behavior=s.get("pricing_page_behavior"),
                funding_signals=s.get("funding_signals")
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
