"""Final-state verification for the bulk_retry_failed_events task.

These tests assume ``test_initial_state.py`` has already seeded a connection
named ``bulk-conn-${ZEALT_RUN_ID}`` with several events whose initial delivery
failed (``status=FAILED``) and has since flipped the destination URL to a
healthy endpoint. After the candidate finishes, every previously-FAILED event
on that connection must have been bulk-retried and converged to ``SUCCESSFUL``.
"""

import os
import re

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"

CONNECTION_ID_RE = re.compile(r"Connection ID:\s*(web_[A-Za-z0-9_]+)")


@pytest.fixture(scope="session")
def run_id():
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable is not set."
    return rid


@pytest.fixture(scope="session")
def auth_headers():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="session")
def connection_id():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    match = CONNECTION_ID_RE.search(content)
    assert match, (
        f"Could not find a 'Connection ID: web_<id>' line in {LOG_FILE}. "
        f"File contents:\n{content!r}"
    )
    return match.group(1)


def test_output_log_contains_connection_id(connection_id):
    # The fixture itself asserts the format; we just keep an explicit test so a
    # missing log line shows up as its own clearly named failure.
    assert connection_id.startswith("web_"), (
        f"Connection ID from log does not look like a Hookdeck connection ID: "
        f"{connection_id!r}"
    )


def test_logged_connection_matches_seed_name(connection_id, auth_headers, run_id):
    resp = requests.get(
        f"{API_BASE}/connections/{connection_id}", headers=auth_headers, timeout=30
    )
    assert resp.status_code == 200, (
        f"Failed to fetch connection {connection_id}: "
        f"{resp.status_code} {resp.text}"
    )
    data = resp.json()
    expected_name = f"bulk-conn-{run_id}"
    assert data.get("name") == expected_name, (
        f"Connection {connection_id} has name {data.get('name')!r}, expected "
        f"{expected_name!r}. The logged connection must be the seeded one."
    )


def test_no_failed_events_remain(connection_id, auth_headers):
    resp = requests.get(
        f"{API_BASE}/events",
        headers=auth_headers,
        params={
            "webhook_id": connection_id,
            "status": "FAILED",
            "limit": 100,
        },
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list FAILED events for connection {connection_id}: "
        f"{resp.status_code} {resp.text}"
    )
    body = resp.json()
    failed_count = body.get("count", 0)
    failed_models = body.get("models", [])
    assert failed_count == 0 and not failed_models, (
        f"Expected 0 FAILED events on connection {connection_id}, but the "
        f"Events API still reports {failed_count} (sample: "
        f"{[m.get('id') for m in failed_models[:5]]})."
    )


def test_at_least_one_event_succeeded_after_retry(connection_id, auth_headers):
    resp = requests.get(
        f"{API_BASE}/events",
        headers=auth_headers,
        params={
            "webhook_id": connection_id,
            "status": "SUCCESSFUL",
            "attempts[gte]": 2,
            "limit": 100,
        },
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list SUCCESSFUL events with attempts>=2 for connection "
        f"{connection_id}: {resp.status_code} {resp.text}"
    )
    body = resp.json()
    models = body.get("models", [])
    assert len(models) >= 1, (
        f"Expected at least one SUCCESSFUL event with attempts>=2 on "
        f"connection {connection_id} (i.e., an event that failed initially "
        f"and was then delivered on a retry), but the Events API returned "
        f"{len(models)}."
    )

    # Stash the list of event IDs that should have a retry-triggered final
    # attempt so the next test can check them.
    pytest._bulk_retry_event_ids = [m["id"] for m in models if m.get("id")]


def test_latest_attempt_was_triggered_by_bulk_or_manual_retry(
    connection_id, auth_headers
):
    event_ids = getattr(pytest, "_bulk_retry_event_ids", None)
    if not event_ids:
        # Re-query in case the previous test did not run.
        resp = requests.get(
            f"{API_BASE}/events",
            headers=auth_headers,
            params={
                "webhook_id": connection_id,
                "status": "SUCCESSFUL",
                "attempts[gte]": 2,
                "limit": 100,
            },
            timeout=30,
        )
        assert resp.status_code == 200, (
            f"Failed to list SUCCESSFUL events for connection "
            f"{connection_id}: {resp.status_code} {resp.text}"
        )
        event_ids = [m["id"] for m in resp.json().get("models", []) if m.get("id")]
    assert event_ids, (
        f"No SUCCESSFUL events with attempts>=2 found on connection "
        f"{connection_id}; cannot verify retry trigger."
    )

    allowed_triggers = {"BULK_RETRY", "MANUAL"}
    bad_events = []
    for event_id in event_ids:
        resp = requests.get(
            f"{API_BASE}/attempts",
            headers=auth_headers,
            params={
                "event_id": event_id,
                "order_by": "created_at",
                "dir": "desc",
                "limit": 10,
            },
            timeout=30,
        )
        assert resp.status_code == 200, (
            f"Failed to list attempts for event {event_id}: "
            f"{resp.status_code} {resp.text}"
        )
        attempts = resp.json().get("models", [])
        assert attempts, (
            f"Expected at least one attempt record for event {event_id}, "
            f"got an empty list."
        )
        latest = attempts[0]
        if (
            latest.get("status") != "SUCCESSFUL"
            or latest.get("trigger") not in allowed_triggers
        ):
            bad_events.append(
                {
                    "event_id": event_id,
                    "latest_status": latest.get("status"),
                    "latest_trigger": latest.get("trigger"),
                }
            )

    assert not bad_events, (
        "Expected the latest attempt of every redelivered event to be a "
        "SUCCESSFUL attempt whose trigger is BULK_RETRY or MANUAL "
        f"(per Hookdeck attempt trigger enum). Offenders: {bad_events}"
    )
