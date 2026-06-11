import os
import re
import time

import pytest
import requests


LOG_FILE = "/home/user/hookdeck-task/output.log"
HOOKDECK_API_BASE = "https://api.hookdeck.com/2025-07-01"


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
        "Accept": "application/json",
    }


def _parse_log_id(content: str, label: str, prefix: str) -> str:
    pattern = rf"^{re.escape(label)}:\s*({re.escape(prefix)}[A-Za-z0-9_\-]+)\s*$"
    match = re.search(pattern, content, flags=re.MULTILINE)
    assert match, (
        f"Could not find '{label}: <{prefix}...>' line in log file. "
        f"Log contents:\n{content}"
    )
    return match.group(1)


@pytest.fixture(scope="session")
def log_contents() -> str:
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert content.strip(), f"Log file {LOG_FILE} is empty."
    return content


@pytest.fixture(scope="session")
def ids(log_contents: str) -> dict:
    return {
        "connection_id": _parse_log_id(log_contents, "Connection ID", "web_"),
        "source_id": _parse_log_id(log_contents, "Source ID", "src_"),
        "destination_id": _parse_log_id(log_contents, "Destination ID", "des_"),
        "delivered_event_id": _parse_log_id(log_contents, "Delivered Event ID", "evt_"),
    }


@pytest.fixture(scope="session")
def connection(ids: dict) -> dict:
    url = f"{HOOKDECK_API_BASE}/connections/{ids['connection_id']}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    assert resp.status_code == 200, (
        f"Failed to GET {url}: status={resp.status_code} body={resp.text!r}"
    )
    return resp.json()


def test_connection_name_matches_run_id(connection: dict):
    run_id = _run_id()
    expected = f"stripe-charge-succeeded-{run_id}"
    assert connection.get("name") == expected, (
        f"Expected connection name {expected!r}, got {connection.get('name')!r}."
    )


def test_connection_is_active(connection: dict):
    assert connection.get("disabled_at") in (None, ""), (
        f"Connection should not be disabled, got disabled_at={connection.get('disabled_at')!r}."
    )
    assert connection.get("paused_at") in (None, ""), (
        f"Connection should not be paused, got paused_at={connection.get('paused_at')!r}."
    )


def test_source_type_stripe_and_name(connection: dict, ids: dict):
    run_id = _run_id()
    source = connection.get("source") or {}
    assert source.get("id") == ids["source_id"], (
        f"Connection source.id {source.get('id')!r} does not match logged Source ID {ids['source_id']!r}."
    )
    assert source.get("type") == "STRIPE", (
        f"Expected source.type 'STRIPE', got {source.get('type')!r}."
    )
    expected_name = f"stripe-src-{run_id}"
    assert source.get("name") == expected_name, (
        f"Expected source.name {expected_name!r}, got {source.get('name')!r}."
    )


def test_destination_type_mock_api_and_name(connection: dict, ids: dict):
    run_id = _run_id()
    destination = connection.get("destination") or {}
    assert destination.get("id") == ids["destination_id"], (
        f"Connection destination.id {destination.get('id')!r} does not match logged "
        f"Destination ID {ids['destination_id']!r}."
    )
    assert destination.get("type") == "MOCK_API", (
        f"Expected destination.type 'MOCK_API', got {destination.get('type')!r}."
    )
    expected_name = f"mock-dest-{run_id}"
    assert destination.get("name") == expected_name, (
        f"Expected destination.name {expected_name!r}, got {destination.get('name')!r}."
    )


def test_filter_rule_on_charge_succeeded(connection: dict):
    rules = connection.get("rules") or []
    matched = [
        r for r in rules
        if isinstance(r, dict)
        and r.get("type") == "filter"
        and isinstance(r.get("body"), dict)
        and r["body"].get("type") == "charge.succeeded"
    ]
    assert matched, (
        f"Expected a filter rule with body.type == 'charge.succeeded' in connection rules, "
        f"got rules={rules!r}."
    )


def _list_events_for_connection(connection_id: str) -> list[dict]:
    url = f"{HOOKDECK_API_BASE}/events"
    params = {"webhook_id": connection_id, "limit": 100}
    resp = requests.get(url, headers=_headers(), params=params, timeout=30)
    assert resp.status_code == 200, (
        f"Failed to GET {url}: status={resp.status_code} body={resp.text!r}"
    )
    body = resp.json()
    return body.get("models") or []


def test_exactly_one_event_delivered(ids: dict):
    # Allow up to 90 seconds for asynchronous delivery to settle.
    deadline = time.time() + 90
    events: list[dict] = []
    while time.time() < deadline:
        events = _list_events_for_connection(ids["connection_id"])
        if len(events) == 1 and events[0].get("status") == "SUCCESSFUL":
            break
        time.sleep(3)

    assert len(events) == 1, (
        f"Expected exactly 1 event routed through the connection, got {len(events)}. "
        f"Events: {events!r}"
    )
    event = events[0]
    assert event.get("status") == "SUCCESSFUL", (
        f"Expected event status 'SUCCESSFUL', got {event.get('status')!r}. Event: {event!r}"
    )
    assert event.get("destination_id") == ids["destination_id"], (
        f"Event destination_id {event.get('destination_id')!r} != logged "
        f"Destination ID {ids['destination_id']!r}."
    )
    assert event.get("source_id") == ids["source_id"], (
        f"Event source_id {event.get('source_id')!r} != logged Source ID {ids['source_id']!r}."
    )
    assert event.get("id") == ids["delivered_event_id"], (
        f"Event id {event.get('id')!r} != logged Delivered Event ID "
        f"{ids['delivered_event_id']!r}."
    )


def test_delivered_event_body_is_charge_succeeded(ids: dict):
    url = f"{HOOKDECK_API_BASE}/events/{ids['delivered_event_id']}"
    resp = requests.get(url, headers=_headers(), timeout=30)
    assert resp.status_code == 200, (
        f"Failed to GET {url}: status={resp.status_code} body={resp.text!r}"
    )
    event = resp.json()
    data = event.get("data") or {}
    body = data.get("body") or {}
    inner = body.get("body") if isinstance(body, dict) else None
    # Hookdeck stores the original request body under data.body.body for JSON payloads.
    if isinstance(inner, dict) and "type" in inner:
        observed_type = inner.get("type")
    elif isinstance(body, dict) and "type" in body:
        observed_type = body.get("type")
    else:
        observed_type = None
    assert observed_type == "charge.succeeded", (
        f"Expected the delivered event body type to be 'charge.succeeded', "
        f"got {observed_type!r}. Full data: {data!r}"
    )


def test_other_events_were_filtered_out(ids: dict):
    """The 3 non-matching publishes must result in ignored events with cause FILTERED."""
    requests_url = f"{HOOKDECK_API_BASE}/requests"
    params = {"source_id": ids["source_id"], "limit": 100}
    resp = requests.get(requests_url, headers=_headers(), params=params, timeout=30)
    assert resp.status_code == 200, (
        f"Failed to GET {requests_url}: status={resp.status_code} body={resp.text!r}"
    )
    req_body = resp.json()
    requests_list = req_body.get("models") or []
    assert requests_list, (
        f"Expected at least one request for source {ids['source_id']!r}, got none."
    )

    filtered_count = 0
    for req in requests_list:
        req_id = req.get("id")
        if not req_id:
            continue
        ig_url = f"{HOOKDECK_API_BASE}/requests/{req_id}/ignored_events"
        ig_resp = requests.get(ig_url, headers=_headers(), timeout=30)
        if ig_resp.status_code != 200:
            continue
        ignored = (ig_resp.json() or {}).get("models") or []
        for ev in ignored:
            if (
                ev.get("cause") == "FILTERED"
                and ev.get("webhook_id") == ids["connection_id"]
            ):
                filtered_count += 1

    assert filtered_count >= 3, (
        f"Expected at least 3 FILTERED ignored events for connection "
        f"{ids['connection_id']!r}, got {filtered_count}."
    )
