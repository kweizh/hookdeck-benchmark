import os
import re
from datetime import datetime, timezone

import pytest
import requests

LOG_FILE = "/home/user/hookdeck-task/output.log"
API_BASE = "https://api.hookdeck.com/2025-07-01"


def _read_log_text() -> str:
    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _api_headers() -> dict:
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set"
    return {"Authorization": f"Bearer {api_key}"}


def _parse_iso8601(value: str) -> datetime:
    # Hookdeck timestamps look like '2026-01-14T13:36:06.675Z' or with fractional secs.
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@pytest.fixture(scope="module")
def run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable is not set"
    return rid


@pytest.fixture(scope="module")
def log_text() -> str:
    return _read_log_text()


@pytest.fixture(scope="module")
def destination_id(log_text: str) -> str:
    m = re.search(r"Destination ID:\s*(des_[A-Za-z0-9]+)", log_text)
    assert m is not None, "Could not find 'Destination ID: des_...' in the log file"
    return m.group(1)


@pytest.fixture(scope="module")
def source_id(log_text: str) -> str:
    m = re.search(r"Source ID:\s*(src_[A-Za-z0-9]+)", log_text)
    assert m is not None, "Could not find 'Source ID: src_...' in the log file"
    return m.group(1)


@pytest.fixture(scope="module")
def connection_id(log_text: str) -> str:
    m = re.search(r"Connection ID:\s*(web_[A-Za-z0-9]+)", log_text)
    assert m is not None, "Could not find 'Connection ID: web_...' in the log file"
    return m.group(1)


@pytest.fixture(scope="module")
def event_ids(log_text: str) -> list[str]:
    m = re.search(r"Event IDs:\s*([A-Za-z0-9_,\s]+)", log_text)
    assert m is not None, "Could not find 'Event IDs: ...' line in the log file"
    raw_ids = [s.strip() for s in m.group(1).split(",")]
    raw_ids = [s for s in raw_ids if s]
    assert len(raw_ids) == 5, (
        f"Expected exactly 5 event IDs in log file, got {len(raw_ids)}: {raw_ids}"
    )
    for eid in raw_ids:
        assert eid.startswith("evt_"), f"Event ID '{eid}' does not start with 'evt_'"
    return raw_ids


def test_destination_config(run_id: str, destination_id: str):
    """The Mock API destination must exist with rate_limit=2 and rate_limit_period=minute."""
    resp = requests.get(
        f"{API_BASE}/destinations/{destination_id}",
        headers=_api_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /destinations/{destination_id} failed: {resp.status_code} {resp.text}"
    )
    dest = resp.json()
    expected_name = f"rl-dest-{run_id}"
    assert dest.get("name") == expected_name, (
        f"Expected destination name '{expected_name}', got '{dest.get('name')}'"
    )
    assert dest.get("type") == "MOCK_API", (
        f"Expected destination type 'MOCK_API', got '{dest.get('type')}'"
    )
    config = dest.get("config") or {}
    assert config.get("rate_limit") == 2, (
        f"Expected config.rate_limit == 2, got {config.get('rate_limit')!r}"
    )
    assert config.get("rate_limit_period") == "minute", (
        f"Expected config.rate_limit_period == 'minute', got {config.get('rate_limit_period')!r}"
    )


def test_source_config(run_id: str, source_id: str):
    """The Webhook source must exist with the expected name and type."""
    resp = requests.get(
        f"{API_BASE}/sources/{source_id}",
        headers=_api_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /sources/{source_id} failed: {resp.status_code} {resp.text}"
    )
    src = resp.json()
    expected_name = f"rl-src-{run_id}"
    assert src.get("name") == expected_name, (
        f"Expected source name '{expected_name}', got '{src.get('name')}'"
    )
    assert src.get("type") == "WEBHOOK", (
        f"Expected source type 'WEBHOOK', got '{src.get('type')}'"
    )


def test_connection_links_source_and_destination(
    run_id: str, connection_id: str, source_id: str, destination_id: str
):
    """The connection must link the created source to the created destination."""
    resp = requests.get(
        f"{API_BASE}/connections/{connection_id}",
        headers=_api_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /connections/{connection_id} failed: {resp.status_code} {resp.text}"
    )
    conn = resp.json()
    expected_name = f"rl-conn-{run_id}"
    assert conn.get("name") == expected_name, (
        f"Expected connection name '{expected_name}', got '{conn.get('name')}'"
    )
    src = conn.get("source") or {}
    dest = conn.get("destination") or {}
    assert src.get("id") == source_id, (
        f"Expected connection.source.id == '{source_id}', got '{src.get('id')}'"
    )
    assert dest.get("id") == destination_id, (
        f"Expected connection.destination.id == '{destination_id}', got '{dest.get('id')}'"
    )


def test_all_five_events_successful(event_ids: list[str], destination_id: str):
    """Every event referenced in the log file must be SUCCESSFUL and target the destination."""
    headers = _api_headers()
    for eid in event_ids:
        resp = requests.get(f"{API_BASE}/events/{eid}", headers=headers, timeout=30)
        assert resp.status_code == 200, (
            f"GET /events/{eid} failed: {resp.status_code} {resp.text}"
        )
        event = resp.json()
        assert event.get("status") == "SUCCESSFUL", (
            f"Event {eid} has status {event.get('status')!r}; expected 'SUCCESSFUL'"
        )
        assert event.get("destination_id") == destination_id, (
            f"Event {eid} destination_id is {event.get('destination_id')!r}; "
            f"expected {destination_id!r}"
        )
        assert event.get("successful_at"), (
            f"Event {eid} has no successful_at timestamp"
        )


def test_delivery_pacing_matches_rate_limit(event_ids: list[str]):
    """The 5 deliveries must be spread out by Hookdeck's per-minute rate limiter."""
    headers = _api_headers()
    timestamps: list[datetime] = []
    for eid in event_ids:
        resp = requests.get(f"{API_BASE}/events/{eid}", headers=headers, timeout=30)
        assert resp.status_code == 200, (
            f"GET /events/{eid} failed: {resp.status_code} {resp.text}"
        )
        event = resp.json()
        ts = event.get("successful_at")
        assert ts, f"Event {eid} has no successful_at timestamp"
        timestamps.append(_parse_iso8601(ts))

    timestamps.sort()
    spread = (timestamps[-1] - timestamps[0]).total_seconds()
    assert spread >= 60, (
        f"Expected successful_at spread >= 60s for rate_limit=2/minute, got {spread:.2f}s. "
        f"Timestamps: {[t.isoformat() for t in timestamps]}"
    )

    gaps = [
        (timestamps[i + 1] - timestamps[i]).total_seconds()
        for i in range(len(timestamps) - 1)
    ]
    assert any(g > 25 for g in gaps), (
        f"Expected at least one consecutive successful_at gap > 25s, got gaps={gaps}. "
        f"Timestamps: {[t.isoformat() for t in timestamps]}"
    )
