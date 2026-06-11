import json
import os
import re
import time

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"


# ---------- helpers ----------

def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key, "HOOKDECK_API_KEY environment variable is not set."
    return key


def _run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable is not set."
    return rid


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def result_ids() -> dict:
    """Parse the executor-produced log file and return the recorded IDs."""
    assert os.path.isfile(LOG_FILE), (
        f"Expected log file {LOG_FILE} to exist after the task; it does not."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"^\s*RESULT:\s*(\{.*\})\s*$", content, re.MULTILINE)
    assert match, (
        f"Could not find a 'RESULT: {{...}}' JSON line in {LOG_FILE}. Content was:\n"
        f"{content}"
    )
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        pytest.fail(f"RESULT payload is not valid JSON: {exc}\nRaw: {match.group(1)}")
    for key in ("transformation_id", "source_id", "destination_id", "connection_id"):
        assert key in data and isinstance(data[key], str) and data[key], (
            f"RESULT JSON is missing string field '{key}'. Got: {data}"
        )
    return data


# ---------- resource checks ----------

def test_source_exists_and_is_webhook(result_ids):
    rid = _run_id()
    resp = requests.get(
        f"{API_BASE}/sources/{result_ids['source_id']}",
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /sources/{result_ids['source_id']} returned {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("name") == f"flatten-src-{rid}", (
        f"Source name mismatch: expected 'flatten-src-{rid}', got {body.get('name')!r}."
    )
    assert body.get("type") == "WEBHOOK", (
        f"Source type must be 'WEBHOOK', got {body.get('type')!r}."
    )


def test_destination_exists_and_is_mock_api(result_ids):
    rid = _run_id()
    resp = requests.get(
        f"{API_BASE}/destinations/{result_ids['destination_id']}",
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /destinations/{result_ids['destination_id']} returned"
        f" {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("name") == f"flatten-dest-{rid}", (
        f"Destination name mismatch: expected 'flatten-dest-{rid}',"
        f" got {body.get('name')!r}."
    )
    assert body.get("type") == "MOCK_API", (
        f"Destination type must be 'MOCK_API', got {body.get('type')!r}."
    )


def test_connection_references_transformation(result_ids):
    rid = _run_id()
    resp = requests.get(
        f"{API_BASE}/connections/{result_ids['connection_id']}",
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /connections/{result_ids['connection_id']} returned"
        f" {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("name") == f"flatten-conn-{rid}", (
        f"Connection name mismatch: expected 'flatten-conn-{rid}',"
        f" got {body.get('name')!r}."
    )
    source = body.get("source") or {}
    destination = body.get("destination") or {}
    assert source.get("id") == result_ids["source_id"], (
        f"Connection source mismatch: expected {result_ids['source_id']},"
        f" got {source.get('id')!r}."
    )
    assert destination.get("id") == result_ids["destination_id"], (
        f"Connection destination mismatch: expected {result_ids['destination_id']},"
        f" got {destination.get('id')!r}."
    )
    rules = body.get("rules") or []
    matching = [
        r for r in rules
        if isinstance(r, dict)
        and r.get("type") == "transformation"
        and r.get("transformation_id") == result_ids["transformation_id"]
    ]
    assert matching, (
        "Connection.rules must contain a transformation rule referencing"
        f" transformation_id={result_ids['transformation_id']}. Got rules={rules!r}."
    )


def test_transformation_code_contract(result_ids):
    rid = _run_id()
    resp = requests.get(
        f"{API_BASE}/transformations/{result_ids['transformation_id']}",
        headers=_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /transformations/{result_ids['transformation_id']} returned"
        f" {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert body.get("name") == f"flatten-rename-{rid}", (
        f"Transformation name mismatch: expected 'flatten-rename-{rid}',"
        f" got {body.get('name')!r}."
    )
    code = body.get("code") or ""
    assert isinstance(code, str) and code.strip(), "Transformation code is empty."
    # The handler must be registered for the 'transform' event.
    assert "addHandler" in code, "Transformation code must register an addHandler."
    assert re.search(r"""addHandler\(\s*['\"]transform['\"]""", code), (
        "Transformation must register a handler for the 'transform' event."
    )
    # Rename customer_email -> email.
    assert "customer_email" in code, (
        "Transformation code must reference the input field 'customer_email' to rename"
        " it."
    )
    assert re.search(r"""['\"]?email['\"]?""", code), (
        "Transformation code must reference the output field 'email'."
    )
    # Header injection.
    assert "x-hookdeck-transformed" in code, (
        "Transformation code must inject the 'x-hookdeck-transformed' header."
    )
    # Flatten body.data.object -> body.
    assert "data" in code and "object" in code, (
        "Transformation code must reference body.data.object to flatten it."
    )
    # Drop threshold and explicit null return.
    assert "100" in code, (
        "Transformation code must reference the drop threshold value 100."
    )
    assert re.search(r"return\s+null", code), (
        "Transformation code must return null to drop low-amount events."
    )


# ---------- event delivery checks ----------

def _list_events_for_connection(connection_id: str) -> list:
    """Return all events for the given connection (single page is sufficient here)."""
    resp = requests.get(
        f"{API_BASE}/events",
        headers=_headers(),
        params={"webhook_id": connection_id, "limit": 50},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /events?webhook_id={connection_id} returned {resp.status_code}:"
        f" {resp.text}"
    )
    payload = resp.json()
    models = payload.get("models")
    assert isinstance(models, list), (
        f"Inspect API response is missing 'models' list: {payload!r}"
    )
    return models


def _wait_for_terminal_events(connection_id: str, expected: int = 2,
                              max_seconds: int = 60) -> list:
    """Poll until at least `expected` events have a terminal status."""
    deadline = time.time() + max_seconds
    terminal_statuses = {"SUCCESSFUL", "FAILED"}
    last = []
    while time.time() < deadline:
        last = _list_events_for_connection(connection_id)
        terminal = [e for e in last if e.get("status") in terminal_statuses]
        if len(terminal) >= expected:
            return last
        time.sleep(3)
    return last


def test_exactly_two_events_delivered(result_ids):
    events = _wait_for_terminal_events(result_ids["connection_id"], expected=2)
    successful = [e for e in events if e.get("status") == "SUCCESSFUL"]
    assert len(successful) == 2, (
        "Expected exactly 2 SUCCESSFUL events on the connection (the two amount=200"
        f" events); got {len(successful)}. All events: {events!r}"
    )


def test_delivered_event_bodies_and_headers(result_ids):
    events = _wait_for_terminal_events(result_ids["connection_id"], expected=2)
    successful = [e for e in events if e.get("status") == "SUCCESSFUL"]
    assert len(successful) >= 2, (
        f"Need at least 2 successful events to check shape; got {len(successful)}."
    )

    expected_keys = {"id", "amount", "currency", "email"}
    forbidden_keys = {"data", "object", "customer_email"}

    for event in successful[:2]:
        event_id = event.get("id")
        assert event_id, f"Successful event is missing id: {event!r}"
        detail_resp = requests.get(
            f"{API_BASE}/events/{event_id}",
            headers=_headers(),
            timeout=30,
        )
        assert detail_resp.status_code == 200, (
            f"GET /events/{event_id} returned {detail_resp.status_code}:"
            f" {detail_resp.text}"
        )
        detail = detail_resp.json()
        data = detail.get("data") or {}
        # The delivered body is at data.body.body per the Inspect API schema.
        outer_body = data.get("body")
        assert isinstance(outer_body, dict), (
            f"Event {event_id}: data.body is not an object: {outer_body!r}"
        )
        inner_body = outer_body.get("body")
        assert isinstance(inner_body, dict), (
            f"Event {event_id}: data.body.body must be an object (the transformed"
            f" payload); got {inner_body!r}"
        )
        body_keys = set(inner_body.keys())
        assert body_keys == expected_keys, (
            f"Event {event_id}: delivered body keys must be exactly {expected_keys},"
            f" got {body_keys}."
        )
        assert not (body_keys & forbidden_keys), (
            f"Event {event_id}: delivered body still contains forbidden keys"
            f" {body_keys & forbidden_keys}; flatten/rename did not happen."
        )
        assert inner_body.get("amount") == 200, (
            f"Event {event_id}: delivered amount must be 200 (low-amount events should"
            f" have been dropped); got {inner_body.get('amount')!r}."
        )
        email = inner_body.get("email")
        assert isinstance(email, str) and email, (
            f"Event {event_id}: delivered body 'email' must be a non-empty string;"
            f" got {email!r}."
        )

        # The transformation must have injected the header.
        delivered_headers = data.get("headers") or {}
        assert isinstance(delivered_headers, dict), (
            f"Event {event_id}: data.headers must be an object; got"
            f" {delivered_headers!r}."
        )
        lower_headers = {k.lower(): v for k, v in delivered_headers.items()}
        assert "x-hookdeck-transformed" in lower_headers, (
            f"Event {event_id}: delivered headers must include"
            f" 'x-hookdeck-transformed'; got headers={list(delivered_headers)!r}."
        )
        assert str(lower_headers["x-hookdeck-transformed"]).lower() == "true", (
            f"Event {event_id}: 'x-hookdeck-transformed' must equal 'true';"
            f" got {lower_headers['x-hookdeck-transformed']!r}."
        )


def test_dropped_event_recorded_as_ignored(result_ids):
    """The amount=50 event must NOT be delivered. It should appear as an ignored
    (filtered) event on the source's requests."""
    resp = requests.get(
        f"{API_BASE}/requests",
        headers=_headers(),
        params={"source_id": result_ids["source_id"], "limit": 50},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /requests?source_id={result_ids['source_id']} returned"
        f" {resp.status_code}: {resp.text}"
    )
    payload = resp.json()
    models = payload.get("models") or []
    assert models, (
        "Expected at least one request to have been ingested for the source;"
        f" got none. Response: {payload!r}"
    )
    total_events = sum(int(r.get("events_count") or 0) for r in models)
    total_ignored = sum(int(r.get("ignored_count") or 0) for r in models)
    assert total_events == 2, (
        "Sum of events_count across all requests for the source must be exactly 2"
        f" (only the two amount=200 events should produce events); got {total_events}."
        f" Requests: {models!r}"
    )
    assert total_ignored >= 1, (
        "At least one request must have ignored_count >= 1 (the amount=50 event"
        f" dropped by the transformation); got total_ignored={total_ignored}."
        f" Requests: {models!r}"
    )
