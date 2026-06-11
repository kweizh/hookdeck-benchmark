import os
import re
from datetime import datetime, timezone

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"
EVENT_ID_RE = re.compile(r"^Event ID:\s*(\S+)\s*$")


def _api_key() -> str:
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable must be set for verification."
    return api_key


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set for verification."
    return run_id


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
    }


def _parse_iso(ts: str) -> datetime:
    # Normalize a trailing Z into +00:00 so fromisoformat can parse it.
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@pytest.fixture(scope="module")
def event_ids() -> list[str]:
    assert os.path.isfile(LOG_FILE), f"Expected log file at {LOG_FILE}, but it does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    ids: list[str] = []
    for line in lines:
        m = EVENT_ID_RE.match(line)
        assert m, (
            f"Log line does not match required format 'Event ID: <event_id>': {line!r}"
        )
        ids.append(m.group(1))
    assert len(ids) == 3, (
        f"Expected exactly 3 'Event ID:' lines in {LOG_FILE}, found {len(ids)}: {ids}"
    )
    return ids


@pytest.fixture(scope="module")
def connection() -> dict:
    run_id = _run_id()
    conn_name = f"delay-conn-{run_id}"
    resp = requests.get(
        f"{API_BASE}/connections",
        params={"name": conn_name},
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Listing connections by name failed: HTTP {resp.status_code} body={resp.text}"
    )
    payload = resp.json()
    models = payload.get("models", [])
    assert len(models) == 1, (
        f"Expected exactly 1 connection named {conn_name!r}, got {len(models)}: "
        f"{[m.get('name') for m in models]}"
    )
    return models[0]


def test_connection_destination_is_mock_api(connection: dict):
    destination = connection.get("destination") or {}
    dest_type = destination.get("type")
    assert dest_type == "MOCK_API", (
        f"Expected destination.type == 'MOCK_API', got {dest_type!r}. "
        f"Destination object: {destination}"
    )


def test_connection_has_delay_rule_with_5000(connection: dict):
    rules = connection.get("rules") or []
    delay_rules = [r for r in rules if isinstance(r, dict) and r.get("type") == "delay"]
    assert len(delay_rules) >= 1, (
        f"Expected at least one rule of type 'delay' on the connection, got rules: {rules}"
    )
    # The Hookdeck API delay rule uses a `delay` field expressed in milliseconds.
    matching = [r for r in delay_rules if r.get("delay") == 5000]
    assert matching, (
        f"Expected a delay rule with delay == 5000 (ms); delay rules found: {delay_rules}"
    )


def test_each_event_delivered_with_correct_delay(event_ids: list[str], connection: dict):
    conn_id = connection.get("id")
    assert conn_id, f"Connection object is missing an id: {connection}"

    failures: list[str] = []
    for event_id in event_ids:
        resp = requests.get(
            f"{API_BASE}/events/{event_id}",
            headers=_headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            failures.append(
                f"event {event_id}: GET /events failed with HTTP {resp.status_code}: {resp.text}"
            )
            continue
        event = resp.json()

        webhook_id = event.get("webhook_id")
        if webhook_id != conn_id:
            failures.append(
                f"event {event_id}: webhook_id {webhook_id!r} does not match the "
                f"connection id {conn_id!r}"
            )
            continue

        status = event.get("status")
        if status != "SUCCESSFUL":
            failures.append(
                f"event {event_id}: expected status 'SUCCESSFUL', got {status!r}"
            )
            continue

        created_at = event.get("created_at")
        successful_at = event.get("successful_at")
        if not created_at or not successful_at:
            failures.append(
                f"event {event_id}: missing created_at or successful_at "
                f"(created_at={created_at!r}, successful_at={successful_at!r})"
            )
            continue

        try:
            t_created = _parse_iso(created_at)
            t_success = _parse_iso(successful_at)
        except ValueError as exc:
            failures.append(f"event {event_id}: could not parse timestamps: {exc}")
            continue

        delta_ms = (t_success - t_created).total_seconds() * 1000.0
        if not (delta_ms >= 5000.0 and delta_ms < 10000.0):
            failures.append(
                f"event {event_id}: delivery delay {delta_ms:.1f}ms is outside the "
                f"expected [5000, 10000) ms window "
                f"(created_at={created_at}, successful_at={successful_at})"
            )

    assert not failures, "Per-event delay verification failed:\n  - " + "\n  - ".join(failures)
