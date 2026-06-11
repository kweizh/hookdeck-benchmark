import json
import os
import re
import time
from datetime import datetime, timedelta, timezone

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"
TRANSFORM_RULE_TYPES = {"transformation", "transform"}


def _api_key() -> str:
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing."
    return api_key


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is missing."
    return run_id


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}", "Content-Type": "application/json"}


def _read_connection_id_from_log() -> str:
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    match = re.search(r"Connection ID:\s*(web_[A-Za-z0-9]+)", content)
    assert match, (
        "Connection ID not found in the log file. "
        "Expected a line matching 'Connection ID: web_...'."
    )
    return match.group(1)


def _fetch_connection(connection_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/connections/{connection_id}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to fetch connection {connection_id}: {resp.status_code} {resp.text}"
    )
    return resp.json()


def _normalize_iso(ts: str) -> datetime:
    # Accept trailing Z by converting to +00:00 for fromisoformat
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def _flatten_headers(headers_obj) -> dict:
    flat = {}
    if not isinstance(headers_obj, dict):
        return flat
    for k, v in headers_obj.items():
        flat[k.lower()] = v
    return flat


def _extract_outgoing_body(event_data: dict):
    """Return the body of the request sent to the destination.

    The Hookdeck event payload nests body in either `data.body` or
    `data.body.body` depending on which payload shape the source produced.
    """
    body = event_data.get("body")
    if isinstance(body, dict) and "body" in body and isinstance(body["body"], (dict, list, str)):
        return body["body"]
    return body


def _extract_outgoing_headers(event_data: dict) -> dict:
    # Headers added by a transformation appear in the outgoing request headers.
    # The Hookdeck event payload often nests headers in `data.headers`, and
    # sometimes also nests a copy under `data.body.headers` for the inbound side.
    flat = _flatten_headers(event_data.get("headers"))
    body = event_data.get("body")
    if isinstance(body, dict):
        flat.update(_flatten_headers(body.get("headers")))
    return flat


def test_connection_metadata_and_rule_order():
    run_id = _run_id()
    connection_id = _read_connection_id_from_log()
    connection = _fetch_connection(connection_id)

    assert connection.get("name") == f"chain-conn-{run_id}", (
        f"Expected connection name 'chain-conn-{run_id}', got '{connection.get('name')}'."
    )

    source = connection.get("source") or {}
    assert source.get("name") == f"chain-src-{run_id}", (
        f"Expected source name 'chain-src-{run_id}', got '{source.get('name')}'."
    )
    assert source.get("type") == "WEBHOOK", (
        f"Expected source type 'WEBHOOK', got '{source.get('type')}'."
    )

    destination = connection.get("destination") or {}
    assert destination.get("name") == f"chain-dest-{run_id}", (
        f"Expected destination name 'chain-dest-{run_id}', got '{destination.get('name')}'."
    )
    assert destination.get("type") == "MOCK_API", (
        f"Expected destination type 'MOCK_API', got '{destination.get('type')}'."
    )

    rules = connection.get("rules") or []
    assert len(rules) == 2, f"Expected exactly 2 rules, got {len(rules)}: {rules}"

    first, second = rules[0], rules[1]
    assert first.get("type") == "filter", (
        f"Expected rules[0].type == 'filter', got '{first.get('type')}'. Rules: {rules}"
    )
    assert second.get("type") in TRANSFORM_RULE_TYPES, (
        f"Expected rules[1].type in {TRANSFORM_RULE_TYPES}, got '{second.get('type')}'. Rules: {rules}"
    )

    # Filter should restrict body.type == "order.created"
    filter_blob = json.dumps(first)
    assert "order.created" in filter_blob, (
        f"Filter rule does not reference 'order.created': {first}"
    )
    body_filter = first.get("body")
    assert isinstance(body_filter, dict), (
        f"Filter rule does not include a body condition: {first}"
    )
    body_type = body_filter.get("type")
    # Body condition may be a plain string match or an operator object {"eq": "..."}.
    if isinstance(body_type, dict):
        flattened = json.dumps(body_type)
        assert "order.created" in flattened, (
            f"Filter rule body.type does not match 'order.created': {body_filter}"
        )
    else:
        assert body_type == "order.created", (
            f"Filter rule body.type does not equal 'order.created': {body_filter}"
        )


def test_transformation_code_references_expected_keys():
    connection_id = _read_connection_id_from_log()
    connection = _fetch_connection(connection_id)
    rules = connection.get("rules") or []
    assert len(rules) >= 2, f"Expected at least 2 rules to inspect transformation: {rules}"
    transform_rule = rules[1]
    transformation_id = transform_rule.get("transformation_id")
    if not transformation_id:
        # Some API versions embed the code directly; fall back to that.
        code = transform_rule.get("code") or ""
        assert "processed_at" in code and "x-processed" in code, (
            f"Inline transformation code does not reference required keys: {transform_rule}"
        )
        return

    resp = requests.get(
        f"{API_BASE}/transformations/{transformation_id}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to fetch transformation {transformation_id}: {resp.status_code} {resp.text}"
    )
    code = resp.json().get("code") or ""
    assert "processed_at" in code, (
        f"Transformation code does not reference 'processed_at': {code}"
    )
    assert "x-processed" in code, (
        f"Transformation code does not reference 'x-processed' header: {code}"
    )


def _list_events(connection_id: str) -> list:
    resp = requests.get(
        f"{API_BASE}/events",
        headers=_auth_headers(),
        params={"webhook_id": connection_id, "limit": 50},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list events: {resp.status_code} {resp.text}"
    )
    payload = resp.json()
    return payload.get("models", []) or []


def _wait_for_events(connection_id: str, expected_count: int = 2, timeout_s: int = 60):
    deadline = time.time() + timeout_s
    last_models: list = []
    while time.time() < deadline:
        last_models = _list_events(connection_id)
        if len(last_models) >= expected_count:
            return last_models
        time.sleep(3)
    return last_models


def test_only_order_created_events_delivered_with_transformation():
    connection_id = _read_connection_id_from_log()

    events = _wait_for_events(connection_id, expected_count=2, timeout_s=90)
    assert len(events) == 2, (
        f"Expected exactly 2 events delivered through the connection, got {len(events)}. "
        f"Filter rule should drop non order.created events. Events: {events}"
    )

    now = datetime.now(timezone.utc)
    earliest_allowed = now - timedelta(hours=1)
    latest_allowed = now + timedelta(minutes=5)

    for event_summary in events:
        event_id = event_summary.get("id")
        assert event_id, f"Event is missing an id: {event_summary}"
        assert event_summary.get("response_status") == 200, (
            f"Event {event_id} response_status is not 200: {event_summary.get('response_status')}"
        )

        detail_resp = requests.get(
            f"{API_BASE}/events/{event_id}",
            headers=_auth_headers(),
            timeout=30,
        )
        assert detail_resp.status_code == 200, (
            f"Failed to fetch event {event_id}: {detail_resp.status_code} {detail_resp.text}"
        )
        event = detail_resp.json()
        data = event.get("data") or {}

        body = _extract_outgoing_body(data)
        assert isinstance(body, dict), (
            f"Event {event_id} outgoing body is not a JSON object: {body}"
        )
        assert body.get("type") == "order.created", (
            f"Event {event_id} body.type is not 'order.created' (filter should reject others): {body}"
        )
        processed_at = body.get("processed_at")
        assert isinstance(processed_at, str) and processed_at, (
            f"Event {event_id} body is missing string field 'processed_at': {body}"
        )
        try:
            parsed = _normalize_iso(processed_at)
        except ValueError as exc:
            pytest.fail(
                f"Event {event_id} body.processed_at is not a valid ISO 8601 timestamp "
                f"({processed_at!r}): {exc}"
            )
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        assert earliest_allowed <= parsed <= latest_allowed, (
            f"Event {event_id} body.processed_at ({processed_at}) is not within the last hour."
        )

        headers = _extract_outgoing_headers(data)
        assert headers.get("x-processed") == "true", (
            f"Event {event_id} headers missing 'x-processed: true'. Got: {headers}"
        )
