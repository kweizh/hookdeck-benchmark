import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/project"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"


def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key, "HOOKDECK_API_KEY must be set for verification."
    return key


def _run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID must be set for verification."
    return rid


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}"}


@pytest.fixture(scope="session")
def parsed_log() -> dict:
    assert os.path.isfile(LOG_PATH), f"Log file not found at {LOG_PATH}"
    with open(LOG_PATH, "r") as f:
        content = f.read()

    def _extract(prefix: str) -> str:
        m = re.search(rf"^{re.escape(prefix)}\s*(.+)$", content, re.MULTILINE)
        assert m, f"Log file missing required line with prefix `{prefix}`:\n{content}"
        return m.group(1).strip()

    return {
        "source_name": _extract("Source Name:"),
        "connection_id": _extract("Connection ID:"),
        "event_id": _extract("Event ID:"),
        "retry_event_id": _extract("Retry Response Event ID:"),
        "final_status": _extract("Final Status:"),
        "final_attempts": _extract("Final Attempts:"),
    }


def test_log_file_has_required_lines(parsed_log):
    assert parsed_log["source_name"], "Source Name is empty in log file."
    assert parsed_log["connection_id"].startswith("web_"), (
        f"Connection ID must start with `web_`, got `{parsed_log['connection_id']}`."
    )
    assert parsed_log["event_id"].startswith("evt_"), (
        f"Event ID must start with `evt_`, got `{parsed_log['event_id']}`."
    )
    assert parsed_log["retry_event_id"].startswith("evt_"), (
        f"Retry Response Event ID must start with `evt_`, got `{parsed_log['retry_event_id']}`."
    )
    assert parsed_log["final_status"] == "SUCCESSFUL", (
        f"Final Status in log must be `SUCCESSFUL`, got `{parsed_log['final_status']}`."
    )
    assert parsed_log["final_attempts"] == "2", (
        f"Final Attempts in log must be `2`, got `{parsed_log['final_attempts']}`."
    )


def test_log_source_name_matches_run_id_convention(parsed_log):
    expected = f"cli-replay-{_run_id()}".lower()
    assert parsed_log["source_name"] == expected, (
        f"Source Name in log must be `{expected}` (lowercased), "
        f"got `{parsed_log['source_name']}`."
    )


def test_retry_response_returns_event_at_root(parsed_log):
    """The Hookdeck docs state that POST /events/{id}/retry returns the Event
    object at the root of the response. The agent logs the `id` extracted from
    the root of the retry response; it MUST equal the original event id."""
    assert parsed_log["retry_event_id"] == parsed_log["event_id"], (
        f"Retry Response Event ID (`{parsed_log['retry_event_id']}`) must equal "
        f"Event ID (`{parsed_log['event_id']}`). The Hookdeck retry endpoint "
        "returns the Event object directly at the root, so reading `id` from the "
        "root of the response should yield the original event id."
    )


@pytest.fixture(scope="session")
def hookdeck_source(parsed_log) -> dict:
    expected_name = f"cli-replay-{_run_id()}".lower()
    resp = requests.get(
        f"{API_BASE}/sources",
        headers=_auth_headers(),
        params={"name": expected_name},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /sources failed: {resp.status_code} {resp.text[:500]}"
    )
    body = resp.json()
    models = body.get("models", [])
    assert len(models) == 1, (
        f"Expected exactly one Hookdeck source named `{expected_name}`, got {len(models)}."
    )
    return models[0]


def test_source_is_webhook_type(hookdeck_source):
    assert hookdeck_source.get("type") == "WEBHOOK", (
        f"Expected source.type == 'WEBHOOK', got `{hookdeck_source.get('type')}`."
    )


@pytest.fixture(scope="session")
def hookdeck_connection(parsed_log, hookdeck_source) -> dict:
    resp = requests.get(
        f"{API_BASE}/connections",
        headers=_auth_headers(),
        params={"source_id": hookdeck_source["id"]},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /connections failed: {resp.status_code} {resp.text[:500]}"
    )
    body = resp.json()
    models = body.get("models", [])
    assert len(models) >= 1, (
        f"Expected at least one connection for source `{hookdeck_source['id']}`, got 0."
    )
    logged = parsed_log["connection_id"]
    matching = [m for m in models if m.get("id") == logged]
    assert matching, (
        f"Logged Connection ID `{logged}` not found among connections for source "
        f"`{hookdeck_source['id']}`. Got: {[m.get('id') for m in models]}."
    )
    return matching[0]


def test_destination_is_cli_with_correct_path(hookdeck_connection):
    destination = hookdeck_connection.get("destination") or {}
    assert destination.get("type") == "CLI", (
        f"Expected destination.type == 'CLI', got `{destination.get('type')}`."
    )
    config = destination.get("config") or {}
    cli_path = config.get("cli_path") or config.get("path")
    assert cli_path == "/hooks", (
        f"Expected destination.config.cli_path == '/hooks', got `{cli_path}`. "
        f"Full destination config: {config}"
    )


def test_event_state_via_api(parsed_log, hookdeck_source, hookdeck_connection):
    event_id = parsed_log["event_id"]

    # Mild poll loop in case the verifier runs immediately after the retry.
    deadline = time.time() + 60
    event = None
    while time.time() < deadline:
        resp = requests.get(
            f"{API_BASE}/events/{event_id}",
            headers=_auth_headers(),
            timeout=30,
        )
        assert resp.status_code == 200, (
            f"GET /events/{event_id} failed: {resp.status_code} {resp.text[:500]}"
        )
        event = resp.json()
        if event.get("status") == "SUCCESSFUL" and event.get("attempts") == 2:
            break
        time.sleep(2)

    assert event is not None, "Failed to fetch event."
    assert event.get("status") == "SUCCESSFUL", (
        f"Expected event.status == 'SUCCESSFUL', got `{event.get('status')}`. "
        f"Full event: {event}"
    )
    assert event.get("attempts") == 2, (
        f"Expected event.attempts == 2, got `{event.get('attempts')}`. Full event: {event}"
    )
    assert event.get("source_id") == hookdeck_source["id"], (
        f"Expected event.source_id == `{hookdeck_source['id']}`, "
        f"got `{event.get('source_id')}`."
    )
    assert event.get("webhook_id") == hookdeck_connection["id"], (
        f"Expected event.webhook_id == `{hookdeck_connection['id']}`, "
        f"got `{event.get('webhook_id')}`."
    )


def test_only_one_event_for_source(parsed_log, hookdeck_source):
    resp = requests.get(
        f"{API_BASE}/events",
        headers=_auth_headers(),
        params={"source_id": hookdeck_source["id"], "limit": 10},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /events?source_id={hookdeck_source['id']} failed: "
        f"{resp.status_code} {resp.text[:500]}"
    )
    body = resp.json()
    models = body.get("models", [])
    assert len(models) == 1, (
        f"Expected exactly one event for source `{hookdeck_source['id']}`, "
        f"got {len(models)}: {[m.get('id') for m in models]}."
    )
    assert models[0].get("id") == parsed_log["event_id"], (
        f"The single event for the source must match the logged Event ID. "
        f"Logged: `{parsed_log['event_id']}`, actual: `{models[0].get('id')}`."
    )


def test_attempt_history_shows_initial_failure_then_success(parsed_log):
    event_id = parsed_log["event_id"]
    resp = requests.get(
        f"{API_BASE}/attempts",
        headers=_auth_headers(),
        params={"event_id": event_id, "limit": 50},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /attempts?event_id={event_id} failed: {resp.status_code} {resp.text[:500]}"
    )
    body = resp.json()
    attempts = body.get("models", [])
    # The Hookdeck docs note that /attempts only returns attempts with status
    # SUCCESSFUL or FAILED, so we expect to see both.
    assert len(attempts) >= 2, (
        f"Expected at least 2 attempts for event `{event_id}`, got {len(attempts)}: "
        f"{attempts}"
    )

    successful = [a for a in attempts if a.get("status") == "SUCCESSFUL"]
    failed = [
        a
        for a in attempts
        if a.get("status") == "FAILED" or a.get("response_status") == 500
    ]
    assert successful, (
        f"Expected at least one SUCCESSFUL attempt for event `{event_id}`. Got: {attempts}"
    )
    assert failed, (
        f"Expected at least one FAILED attempt (or response_status 500) for event "
        f"`{event_id}`. Got: {attempts}"
    )
