import json
import os
import re
import time
import uuid
from datetime import datetime, timezone

import pytest
import requests


PROJECT_DIR = "/home/user/hookdeck-task"
LOG_PATH = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"
EXPECTED_BODY = "<ack><status>received</status></ack>"


def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY", "")
    assert key, "HOOKDECK_API_KEY must be set to verify Hookdeck resources."
    return key


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID must be set to derive resource names."
    return run_id


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}"}


@pytest.fixture(scope="session")
def parsed_log() -> dict:
    assert os.path.isfile(LOG_PATH), (
        f"Output log not found at {LOG_PATH}; the executor must record the "
        "Source URL and Connection ID there."
    )
    with open(LOG_PATH) as f:
        content = f.read()

    url_match = re.search(r"^Source URL:\s*(\S+)\s*$", content, re.MULTILINE)
    conn_match = re.search(
        r"^Connection ID:\s*(web_[A-Za-z0-9]+)\s*$", content, re.MULTILINE
    )
    assert url_match, (
        f"Log {LOG_PATH} is missing a `Source URL: <url>` line. Got:\n{content}"
    )
    assert conn_match, (
        f"Log {LOG_PATH} is missing a `Connection ID: web_<id>` line. "
        f"Got:\n{content}"
    )
    return {
        "source_url": url_match.group(1).strip(),
        "connection_id": conn_match.group(1).strip(),
    }


@pytest.fixture(scope="session")
def connection(parsed_log) -> dict:
    resp = requests.get(
        f"{API_BASE}/connections/{parsed_log['connection_id']}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /connections/{parsed_log['connection_id']} failed: "
        f"{resp.status_code} {resp.text}"
    )
    return resp.json()


def test_log_file_has_required_fields(parsed_log):
    assert parsed_log["source_url"].startswith("http"), (
        f"Source URL in log is not an HTTP URL: {parsed_log['source_url']}"
    )
    assert parsed_log["connection_id"].startswith("web_"), (
        f"Connection ID in log does not look like a Hookdeck connection id: "
        f"{parsed_log['connection_id']}"
    )


def test_connection_name_and_active(connection):
    expected_name = f"custom-xml-conn-{_run_id()}"
    assert connection.get("name") == expected_name, (
        f"Connection name mismatch: expected {expected_name!r}, "
        f"got {connection.get('name')!r}."
    )
    assert connection.get("disabled_at") in (None, ""), (
        f"Connection must not be disabled. disabled_at={connection.get('disabled_at')!r}"
    )
    assert connection.get("paused_at") in (None, ""), (
        f"Connection must not be paused. paused_at={connection.get('paused_at')!r}"
    )


def test_source_custom_response_configured(connection, parsed_log):
    source = connection.get("source") or {}
    source_id = source.get("id")
    assert source_id, f"Connection {connection.get('id')!r} has no source.id."

    resp = requests.get(
        f"{API_BASE}/sources/{source_id}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /sources/{source_id} failed: {resp.status_code} {resp.text}"
    )
    src = resp.json()

    expected_source_name = f"custom-xml-source-{_run_id()}"
    assert src.get("name") == expected_source_name, (
        f"Source name mismatch: expected {expected_source_name!r}, "
        f"got {src.get('name')!r}."
    )
    assert src.get("url") == parsed_log["source_url"], (
        f"Source URL mismatch: API reports {src.get('url')!r}, "
        f"log recorded {parsed_log['source_url']!r}."
    )

    config = src.get("config") or {}
    custom = config.get("custom_response")
    assert isinstance(custom, dict), (
        f"Source {source_id} has no custom_response configured: "
        f"config={json.dumps(config)}"
    )
    assert custom.get("content_type") == "xml", (
        "custom_response.content_type must be the enum value 'xml'; got "
        f"{custom.get('content_type')!r}."
    )
    assert custom.get("body") == EXPECTED_BODY, (
        f"custom_response.body mismatch: expected {EXPECTED_BODY!r}, "
        f"got {custom.get('body')!r}."
    )


def test_destination_is_mock_api(connection):
    dest = connection.get("destination") or {}
    dest_id = dest.get("id")
    assert dest_id, f"Connection {connection.get('id')!r} has no destination.id."

    resp = requests.get(
        f"{API_BASE}/destinations/{dest_id}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /destinations/{dest_id} failed: {resp.status_code} {resp.text}"
    )
    d = resp.json()

    expected_dest_name = f"mock-dest-{_run_id()}"
    assert d.get("name") == expected_dest_name, (
        f"Destination name mismatch: expected {expected_dest_name!r}, "
        f"got {d.get('name')!r}."
    )
    assert d.get("type") == "MOCK_API", (
        f"Destination type must be MOCK_API; got {d.get('type')!r}."
    )


def test_source_returns_configured_xml_response_and_delivers_event(connection, parsed_log):
    source_url = parsed_log["source_url"]
    connection_id = parsed_log["connection_id"]
    destination_id = (connection.get("destination") or {}).get("id")
    source_id = (connection.get("source") or {}).get("id")
    assert destination_id and source_id, (
        "Connection is missing source.id or destination.id."
    )

    marker = f"probe-{_run_id()}-{uuid.uuid4().hex[:8]}"
    payload = {
        "probe": marker,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    # Step 1: POST to source URL and validate the synchronous XML response.
    resp = requests.post(
        source_url,
        json=payload,
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"POST {source_url} returned {resp.status_code}: {resp.text}"
    )
    content_type = resp.headers.get("Content-Type", "")
    assert "xml" in content_type.lower(), (
        "Response Content-Type must indicate XML (contain the substring "
        f"'xml'); got {content_type!r}."
    )
    assert resp.text.strip() == EXPECTED_BODY, (
        f"Response body must equal {EXPECTED_BODY!r}; got {resp.text!r}."
    )

    # Step 2: Poll the Inspect API and confirm the event was delivered to the
    # mock destination. We locate the request by probe payload, then find the
    # corresponding event.
    deadline = time.time() + 90
    matching_request_id = None
    while time.time() < deadline and matching_request_id is None:
        list_resp = requests.get(
            f"{API_BASE}/requests",
            headers=_auth_headers(),
            params={
                "source_id": source_id,
                "order_by": "created_at",
                "dir": "desc",
                "limit": 50,
            },
            timeout=30,
        )
        assert list_resp.status_code == 200, (
            f"GET /requests failed: {list_resp.status_code} {list_resp.text}"
        )
        for req in list_resp.json().get("models", []):
            body = (((req.get("data") or {}).get("body") or {}).get("body")) or {}
            if isinstance(body, dict) and body.get("probe") == marker:
                matching_request_id = req.get("id")
                break
        if matching_request_id is None:
            time.sleep(3)

    assert matching_request_id, (
        f"No Hookdeck request found whose body.probe matches {marker!r} on "
        f"source {source_id} within the polling window."
    )

    # Find an event for that request belonging to the verified connection.
    matching_event = None
    deadline = time.time() + 90
    while time.time() < deadline and matching_event is None:
        ev_resp = requests.get(
            f"{API_BASE}/events",
            headers=_auth_headers(),
            params={
                "webhook_id": connection_id,
                "request_id": matching_request_id,
                "order_by": "created_at",
                "dir": "desc",
                "limit": 20,
            },
            timeout=30,
        )
        assert ev_resp.status_code == 200, (
            f"GET /events failed: {ev_resp.status_code} {ev_resp.text}"
        )
        candidates = ev_resp.json().get("models", [])
        for ev in candidates:
            if ev.get("status") == "SUCCESSFUL":
                matching_event = ev
                break
        if matching_event is None:
            time.sleep(3)

    assert matching_event is not None, (
        f"No SUCCESSFUL event was found for request {matching_request_id!r} "
        f"on connection {connection_id!r} within the polling window. The event "
        "must be forwarded to the mock destination in addition to returning the "
        "custom XML response."
    )
    assert matching_event.get("destination_id") == destination_id, (
        "Event was delivered to an unexpected destination: "
        f"{matching_event.get('destination_id')!r} vs {destination_id!r}."
    )
    response_status = matching_event.get("response_status")
    assert isinstance(response_status, int) and 200 <= response_status < 300, (
        f"Mock destination delivery did not succeed with a 2xx status; got "
        f"response_status={response_status!r}."
    )
