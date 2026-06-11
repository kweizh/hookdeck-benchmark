"""Initial-state verification for the bulk_retry_failed_events task.

Besides verifying the executor environment, this script also seeds the Hookdeck
project with a connection whose destination initially returns HTTP 500 errors,
publishes a small batch of events through the source so they end up with
``status=FAILED``, then flips the destination URL to a healthy endpoint that
returns HTTP 200. This is the canonical starting state the candidate has to
recover from by bulk-retrying every previously-FAILED event.

All resource names are scoped by ``ZEALT_RUN_ID`` so concurrent evaluation runs
do not collide. The seeding logic is idempotent: re-running the test will not
create duplicate sources/destinations/connections and will only top up the seed
FAILED-event count if it is below ``SEED_FAILED_COUNT``.
"""

import os
import shutil
import time

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
API_BASE = "https://api.hookdeck.com/2025-07-01"

# Number of events that must end up with ``status=FAILED`` on the seeded
# connection before the candidate starts working.
SEED_FAILED_COUNT = 3

# An HTTP endpoint that reliably returns a 500 response (used to force the
# seeded events to fail their initial delivery attempt).
FAILING_URL = "https://httpbin.org/status/500"

# A healthy HTTP endpoint that always returns 200 (used after the seed phase so
# that the candidate's bulk retry can succeed).
HEALTHY_URL = "https://mock.hookdeck.com/healthy"


def _auth_headers():
    api_key = os.environ["HOOKDECK_API_KEY"]
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _list_headers():
    api_key = os.environ["HOOKDECK_API_KEY"]
    return {"Authorization": f"Bearer {api_key}"}


def _upsert_connection_with_failing_destination(run_id):
    """Upsert the seeded connection so the destination initially returns 500."""
    payload = {
        "name": f"bulk-conn-{run_id}",
        "source": {
            "name": f"bulk-src-{run_id}",
            "type": "WEBHOOK",
        },
        "destination": {
            "name": f"bulk-dest-{run_id}",
            "type": "HTTP",
            "config": {
                "url": FAILING_URL,
            },
        },
        "rules": [
            # count=0 means no automatic retries, so failed events transition to
            # FAILED quickly and stay there until the candidate retries them.
            {
                "type": "retry",
                "strategy": "linear",
                "interval": 30000,
                "count": 0,
                "response_status_codes": [">=500"],
            }
        ],
    }
    resp = requests.put(
        f"{API_BASE}/connections", headers=_auth_headers(), json=payload, timeout=60
    )
    assert resp.status_code in (200, 201), (
        f"Failed to upsert seeded connection: {resp.status_code} {resp.text}"
    )
    return resp.json()


def _count_failed_events(connection_id):
    resp = requests.get(
        f"{API_BASE}/events",
        headers=_list_headers(),
        params={
            "webhook_id": connection_id,
            "status": "FAILED",
            "limit": 100,
        },
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list FAILED events: {resp.status_code} {resp.text}"
    )
    return resp.json().get("count", 0)


def _publish_event(source_url, run_id, idx):
    body = {
        "event": "bulk.retry.seed",
        "data": {"run_id": run_id, "idx": idx},
    }
    resp = requests.post(
        source_url,
        headers={"Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    assert resp.status_code < 400, (
        f"Failed to publish seed event #{idx} to {source_url}: "
        f"{resp.status_code} {resp.text}"
    )


def _wait_for_failed_events(connection_id, target_count, timeout_s=240):
    deadline = time.time() + timeout_s
    observed = 0
    while time.time() < deadline:
        observed = _count_failed_events(connection_id)
        if observed >= target_count:
            return observed
        time.sleep(3)
    return observed


def _flip_destination_to_healthy(destination_id):
    resp = requests.put(
        f"{API_BASE}/destinations/{destination_id}",
        headers=_auth_headers(),
        json={"config": {"url": HEALTHY_URL}},
        timeout=30,
    )
    assert resp.status_code in (200, 201), (
        f"Failed to flip destination to healthy URL: "
        f"{resp.status_code} {resp.text}"
    )


# --- Tests ----------------------------------------------------------------


def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck binary not found in PATH."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_environment_variables_set():
    assert os.environ.get("ZEALT_RUN_ID"), (
        "ZEALT_RUN_ID environment variable is not set."
    )
    assert os.environ.get("HOOKDECK_API_KEY"), (
        "HOOKDECK_API_KEY environment variable is not set."
    )


def test_seed_connection_and_failed_events():
    run_id = os.environ["ZEALT_RUN_ID"]

    conn = _upsert_connection_with_failing_destination(run_id)
    connection_id = conn.get("id")
    source = conn.get("source") or {}
    destination = conn.get("destination") or {}
    source_url = source.get("url")
    destination_id = destination.get("id")
    assert connection_id, f"Upserted connection has no id: {conn}"
    assert source_url, f"Upserted source has no public url: {conn}"
    assert destination_id, f"Upserted connection has no destination id: {conn}"

    existing_failed = _count_failed_events(connection_id)
    needed = SEED_FAILED_COUNT - existing_failed
    if needed > 0:
        for i in range(needed):
            _publish_event(source_url, run_id, i)
        observed = _wait_for_failed_events(
            connection_id, SEED_FAILED_COUNT, timeout_s=240
        )
        assert observed >= SEED_FAILED_COUNT, (
            f"Expected at least {SEED_FAILED_COUNT} FAILED events on seeded "
            f"connection {connection_id}, only observed {observed} within "
            f"the timeout window."
        )

    # After the seed events have failed, switch the destination URL to a
    # healthy endpoint so a bulk retry will actually succeed.
    _flip_destination_to_healthy(destination_id)
