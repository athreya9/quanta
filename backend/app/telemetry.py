import json
import datetime
import threading
from typing import Dict, Any, List, Optional

# Thread-safe ring buffer for real-time telemetry events
_TELEMETRY_BUFFER: List[Dict[str, Any]] = []
_TELEMETRY_LOCK = threading.Lock()
MAX_TELEMETRY_CAPACITY = 200

def log_telemetry_event(
    tool_name: str,
    status: str,
    raw_payload: Optional[Dict[str, Any]] = None,
    raw_output: Optional[Dict[str, Any]] = None,
    raw_error: Optional[str] = None,
    raw_ingestion: Optional[Dict[str, Any]] = None,
    raw_enrichment: Optional[Dict[str, Any]] = None,
    raw_scoring_breakdown: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Logs a real-time system event into QUANTA's live telemetry buffer.
    """
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    event_id = f"tel_{int(datetime.datetime.utcnow().timestamp() * 1000)}"

    event = {
        "id": event_id,
        "timestamp": timestamp,
        "tool_name": tool_name,
        "status": status.upper(),  # ACTIVE, IDLE, COMPLETED, ERROR, WARNING
        "raw_payload": raw_payload or {},
        "raw_output": raw_output or {},
        "raw_error": raw_error or None,
        "raw_ingestion": raw_ingestion or {},
        "raw_enrichment": raw_enrichment or {},
        "raw_scoring_breakdown": raw_scoring_breakdown or {}
    }

    with _TELEMETRY_LOCK:
        _TELEMETRY_BUFFER.insert(0, event)
        if len(_TELEMETRY_BUFFER) > MAX_TELEMETRY_CAPACITY:
            _TELEMETRY_BUFFER.pop()

    return event

def get_recent_telemetry(limit: int = 100, tool_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves recent telemetry events for the real-time Telemetry Dashboard.
    """
    with _TELEMETRY_LOCK:
        events = list(_TELEMETRY_BUFFER)

    if tool_filter and tool_filter != "all":
        events = [e for e in events if tool_filter.lower() in e["tool_name"].lower()]

    return events[:limit]

# No fake seed events - the telemetry buffer starts empty and only ever
# contains events that were actually logged by real engine activity.
