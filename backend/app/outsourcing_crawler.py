import os
import json
import logging
import datetime
import httpx
import feedparser
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import ExtensionSignalDB
from app.deduplication import is_duplicate_signal
from app.scoring import calculate_multi_factor_intent_score

logger = logging.getLogger("quanta.outsourcing")

HIRING_KEYWORDS = [
    "looking for a developer", "need an ai engineer", "hiring a contractor",
    "seeking outsourcing partner", "rfp", "looking for react", "looking for fastapi",
    "devops needed", "cloud architect needed", "need help with", "[hiring]"
]

async def crawl_reddit_forhire_rss() -> List[Dict[str, Any]]:
    """Crawls the real, public Reddit r/forhire RSS feed. No paid API."""
    results = []
    feed_url = "https://www.reddit.com/r/forhire/new/.rss"
    try:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:15]:
            title = entry.get("title", "")
            if "[hiring]" in title.lower():
                results.append({
                    "title": title,
                    "link": entry.get("link", "https://reddit.com/r/forhire"),
                    "source": "Reddit r/forhire RSS Feed",
                    "published": entry.get("published", "")
                })
    except Exception as e:
        logger.debug(f"Reddit RSS crawl info: {e}")
    return results

async def crawl_upwork_public_rss() -> List[Dict[str, Any]]:
    """Crawls Upwork's public project RSS feed. No paid API."""
    results = []
    feed_url = "https://www.upwork.com/ab/feed/jobs/rss?q=full+stack+developer&sort=recency"
    try:
        parsed = feedparser.parse(feed_url)
        for entry in parsed.entries[:15]:
            title = entry.get("title", "")
            if title:
                results.append({
                    "title": title,
                    "link": entry.get("link", "https://upwork.com"),
                    "source": "Upwork Public Project RSS Feed",
                    "published": entry.get("published", "")
                })
    except Exception as e:
        logger.debug(f"Upwork RSS crawl info: {e}")
    return results

async def execute_outsourcing_intent_crawl(db: Session) -> Dict[str, Any]:
    """
    Pulls real, public outsourcing-intent postings from Reddit r/forhire and
    Upwork's RSS feeds and stores each one as a raw signal - title, real link,
    real source. No company name, budget, executive contact, or phone number
    is invented; those simply aren't present in an RSS post title and are left
    out rather than guessed.
    """
    logger.info("Executing OUTSOURCING INTENT crawl pass across real public RSS feeds...")

    reddit_items = await crawl_reddit_forhire_rss()
    upwork_items = await crawl_upwork_public_rss()
    all_items = reddit_items + upwork_items

    new_signals_count = 0

    for item in all_items:
        link = item["link"]
        event_type = "OUTSOURCING_INTENT"

        if is_duplicate_signal(link, event_type):
            continue

        db_signal = ExtensionSignalDB(
            domain=link.split("/")[2] if "//" in link else link,
            company=None,
            url=link,
            event_type=event_type,
            intent_score=calculate_multi_factor_intent_score({})["intent_score"],
            source="outsourcing_crawler",
            geo_location=None,
            browser_fingerprint="Outsourcing RSS Crawler",
            enrichment_metadata=json.dumps({
                "title": item["title"],
                "source_channel": item["source"],
                "published": item.get("published", ""),
                "note": "Raw public posting - no company/contact identity is known, none was invented."
            }),
            demo_sample=False
        )
        db.add(db_signal)
        new_signals_count += 1

    if new_signals_count > 0:
        db.commit()

    return {
        "status": "completed",
        "scanned_sources": ["Reddit r/forhire RSS", "Upwork Public RSS"],
        "new_outsourcing_signals": new_signals_count,
        "new_outsourcing_leads": 0
    }
