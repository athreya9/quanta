import logging
import httpx
from typing import Optional
from app.config import SLACK_WEBHOOK_URL

logger = logging.getLogger("quanta.alerts")

async def send_slack_alert(
    company: str,
    event_type: str,
    description: str,
    intent_score: int,
    source_url: Optional[str] = None
) -> bool:
    """
    Posts real-time intent signal alert payload to Slack webhook if SLACK_WEBHOOK_URL is set.
    Handles network errors gracefully so API execution never crashes or hangs.
    """
    if not SLACK_WEBHOOK_URL:
        logger.info(f"[Slack Alert Skipped] SLACK_WEBHOOK_URL not configured for signal: {company} ({intent_score})")
        return False

    payload = {
        "text": f"🔥 *HIGH INTENT SIGNAL DETECTED*: {company} [{intent_score}/100]",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🔥 QUANTA Intent Alert: {company} ({intent_score}/100)",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Company:*\n{company}"},
                    {"type": "mrkdwn", "text": f"*Event Category:*\n`{event_type}`"},
                    {"type": "mrkdwn", "text": f"*Intent Score:*\n`{intent_score} / 100`"},
                    {"type": "mrkdwn", "text": f"*Source URL:*\n<{source_url or 'https://quanta.virtusol.com'}|View Signal Path>"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {description}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Open QUANTA Signal Console ⚡"},
                        "url": "https://quanta.virtusol.com",
                        "style": "primary"
                    }
                ]
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(SLACK_WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                logger.info(f"[Slack Alert Sent] Dispatched alert for {company}")
                try:
                    from app.telemetry import log_telemetry_event
                    log_telemetry_event(
                        tool_name="Slack Alerts Engine",
                        status="COMPLETED",
                        raw_payload={"company": company, "event_type": event_type, "intent_score": intent_score},
                        raw_output={"slack_status": 200, "message": f"Webhook alert delivered for {company}"}
                    )
                except Exception:
                    pass
                return True
            else:
                logger.warning(f"[Slack Alert Error] Status {response.status_code}: {response.text}")
                try:
                    from app.telemetry import log_telemetry_event
                    log_telemetry_event(
                        tool_name="Slack Alerts Engine",
                        status="ERROR",
                        raw_payload={"company": company, "event_type": event_type},
                        raw_error=f"Slack webhook HTTP {response.status_code}: {response.text}"
                    )
                except Exception:
                    pass
                return False
    except Exception as e:
        logger.error(f"[Slack Alert Exception] Failed to send alert for {company}: {e}")
        try:
            from app.telemetry import log_telemetry_event
            log_telemetry_event(
                tool_name="Slack Alerts Engine",
                status="ERROR",
                raw_payload={"company": company, "event_type": event_type},
                raw_error=str(e)
            )
        except Exception:
            pass
        return False
