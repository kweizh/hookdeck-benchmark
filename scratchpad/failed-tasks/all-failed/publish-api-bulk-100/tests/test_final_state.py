import json
import os
import time
from urllib.parse import quote

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
API_BASE_URL = "https://api.hookdeck.com/2025-07-01"
EXPECTED_COUNT = 100
BATCH_ID = "BATCH-001"

# Poll up to this many seconds for Hookdeck to fully ingest publishes
# and deliver them to the Mock API destination.
POLL_TIMEOUT_SEC = 180
POLL_INTERVAL_SEC = 5


@pytest.fixture(scope="session")
def run_id():
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable is not set."
    return rid


@pytest.fixture(scope="session")
def api_headers():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return {"Authorization": f"Bearer {api_key}"}


def _paginate(url, headers, params):
    """Iterate all models across paginated Hookdeck list endpoints."""
    collected = []
    next_cursor = None
    while True:
        q = dict(params)
        if next_cursor:
            q["next"] = next_cursor
        resp = requests.get(url, headers=headers, params=q, timeout=30)
        assert resp.status_code == 200, (
            f"GET {url} with params {q} failed: "
            f"{resp.status_code} {resp.text}"
        )
        payload = resp.json()
        models = payload.get("models", []) or []
        collected.extend(models)
        next_cursor = (payload.get("pagination") or {}).get("next")
        if not next_cursor:
            break
    return collected


def _find_single_by_name(api_headers, resource_path, name, kind):
    resp = requests.get(
        f"{API_BASE_URL}/{resource_path}",
        headers=api_headers,
        params={"name": name},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list {kind} by name={name}: {resp.status_code} {resp.text}"
    )
    models = resp.json().get("models", []) or []
    # Defensive: filter exact match in case API does partial matching
    exact = [m for m in models if m.get("name") == name]
    assert len(exact) == 1, (
        f"Expected exactly one {kind} named '{name}', found {len(exact)}: "
        f"{[m.get('name') for m in models]}"
    )
    return exact[0]


@pytest.fixture(scope="session")
def source(run_id, api_headers):
    return _find_single_by_name(
        api_headers, "sources", f"bulk-source-{run_id}", "source"
    )


@pytest.fixture(scope="session")
def destination(run_id, api_headers):
    return _find_single_by_name(
        api_headers, "destinations", f"bulk-dest-{run_id}", "destination"
    )


@pytest.fixture(scope="session")
def connection(api_headers, source, destination):
    resp = requests.get(
        f"{API_BASE_URL}/connections",
        headers=api_headers,
        params={
            "source_id": source["id"],
            "destination_id": destination["id"],
        },
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list connections for source={source['id']} "
        f"destination={destination['id']}: {resp.status_code} {resp.text}"
    )
    models = resp.json().get("models", []) or []
    assert len(models) == 1, (
        f"Expected exactly one Connection linking source '{source['name']}' "
        f"to destination '{destination['name']}', found {len(models)}."
    )
    return models[0]


def test_output_log_contents(run_id):
    log_file = os.path.join(PROJECT_DIR, "output.log")
    assert os.path.isfile(log_file), f"Log file {log_file} does not exist."

    with open(log_file, "r") as f:
        content = f.read()

    expected_lines = [
        f"Source Name: bulk-source-{run_id}",
        f"Destination Name: bulk-dest-{run_id}",
        "Published Count: 100",
        f"Batch ID: {BATCH_ID}",
    ]
    for line in expected_lines:
        assert line in content, (
            f"Expected line '{line}' in {log_file}, but it was not found. "
            f"File contents:\n{content}"
        )


def test_source_exists(source):
    assert source.get("id"), f"Source object is missing an id: {source}"


def test_destination_is_mock_api(destination):
    assert destination.get("type") == "MOCK_API", (
        f"Expected destination type 'MOCK_API', got '{destination.get('type')}'."
    )


def test_connection_links_source_and_destination(connection, source, destination):
    # `connection` fixture already asserts a single match for the (source, destination) pair.
    src = connection.get("source") or {}
    dst = connection.get("destination") or {}
    assert src.get("id") == source["id"], (
        f"Connection source id mismatch: expected {source['id']}, got {src.get('id')}."
    )
    assert dst.get("id") == destination["id"], (
        f"Connection destination id mismatch: expected {destination['id']}, "
        f"got {dst.get('id')}."
    )


def _list_batch_requests(api_headers, source_id):
    """List all Hookdeck Requests on the given source that carry the batch header."""
    header_filter = quote(json.dumps({"x-batch-id": BATCH_ID}))
    # Pass already-encoded JSON via raw query string to avoid double-encoding.
    url = (
        f"{API_BASE_URL}/requests"
        f"?source_id={source_id}&headers={header_filter}&limit=250"
    )
    collected = []
    next_cursor = None
    while True:
        full_url = url if not next_cursor else f"{url}&next={next_cursor}"
        resp = requests.get(full_url, headers=api_headers, timeout=30)
        assert resp.status_code == 200, (
            f"GET {full_url} failed: {resp.status_code} {resp.text}"
        )
        payload = resp.json()
        collected.extend(payload.get("models", []) or [])
        next_cursor = (payload.get("pagination") or {}).get("next")
        if not next_cursor:
            break
    return collected


def test_exactly_100_requests_with_batch_header(api_headers, source):
    deadline = time.time() + POLL_TIMEOUT_SEC
    requests_list = []
    last_count = -1
    while time.time() < deadline:
        requests_list = _list_batch_requests(api_headers, source["id"])
        if len(requests_list) == EXPECTED_COUNT:
            break
        last_count = len(requests_list)
        time.sleep(POLL_INTERVAL_SEC)

    assert len(requests_list) == EXPECTED_COUNT, (
        f"Expected exactly {EXPECTED_COUNT} requests with header "
        f"'x-batch-id: {BATCH_ID}' on source '{source['name']}', "
        f"found {len(requests_list)} (last observed: {last_count})."
    )


def _extract_i_value(req, api_headers):
    """Get the integer field `i` from a request's body, falling back to raw_body."""
    data = req.get("data") or {}
    body = data.get("body")

    # The Inspect API can wrap the actual JSON body as data.body.body
    candidate = None
    if isinstance(body, dict) and "body" in body:
        candidate = body["body"]
    elif body is not None:
        candidate = body

    if isinstance(candidate, dict) and "i" in candidate:
        return candidate["i"]
    if isinstance(candidate, str):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "i" in parsed:
                return parsed["i"]
        except json.JSONDecodeError:
            pass

    # Fallback: fetch the raw body
    rid = req.get("id")
    if not rid:
        return None
    raw_resp = requests.get(
        f"{API_BASE_URL}/requests/{rid}/raw_body",
        headers=api_headers,
        timeout=30,
    )
    if raw_resp.status_code != 200:
        return None
    try:
        parsed = raw_resp.json()
    except ValueError:
        try:
            parsed = json.loads(raw_resp.text)
        except json.JSONDecodeError:
            return None
    if isinstance(parsed, dict) and "i" in parsed:
        return parsed["i"]
    return None


def test_request_bodies_cover_0_to_99(api_headers, source):
    requests_list = _list_batch_requests(api_headers, source["id"])
    assert len(requests_list) == EXPECTED_COUNT, (
        f"Expected {EXPECTED_COUNT} requests for body inspection, "
        f"found {len(requests_list)}."
    )

    values = []
    for req in requests_list:
        i_val = _extract_i_value(req, api_headers)
        assert i_val is not None, (
            f"Could not extract 'i' field from request id={req.get('id')}."
        )
        # Accept either int or numeric string for robustness.
        if isinstance(i_val, str):
            assert i_val.lstrip("-").isdigit(), (
                f"Request id={req.get('id')} has non-integer 'i': {i_val!r}."
            )
            i_val = int(i_val)
        assert isinstance(i_val, int), (
            f"Request id={req.get('id')} has non-integer 'i': {i_val!r}."
        )
        values.append(i_val)

    assert len(values) == EXPECTED_COUNT, (
        f"Expected {EXPECTED_COUNT} 'i' values, got {len(values)}."
    )
    assert len(set(values)) == EXPECTED_COUNT, (
        f"Found duplicate 'i' values. Counts: "
        f"{sorted([(v, values.count(v)) for v in set(values) if values.count(v) > 1])}"
    )
    assert set(values) == set(range(EXPECTED_COUNT)), (
        f"Request bodies do not cover i=0..{EXPECTED_COUNT - 1}. "
        f"Missing: {sorted(set(range(EXPECTED_COUNT)) - set(values))}; "
        f"Extra: {sorted(set(values) - set(range(EXPECTED_COUNT)))}."
    )


def test_exactly_100_successful_events_on_connection(
    api_headers, connection, destination
):
    deadline = time.time() + POLL_TIMEOUT_SEC
    events = []
    last_count = -1
    while time.time() < deadline:
        events = _paginate(
            f"{API_BASE_URL}/events",
            api_headers,
            {
                "webhook_id": connection["id"],
                "status": "SUCCESSFUL",
                "limit": 250,
            },
        )
        if len(events) == EXPECTED_COUNT:
            break
        last_count = len(events)
        time.sleep(POLL_INTERVAL_SEC)

    assert len(events) == EXPECTED_COUNT, (
        f"Expected exactly {EXPECTED_COUNT} SUCCESSFUL events on connection "
        f"{connection['id']}, found {len(events)} (last observed: {last_count})."
    )
    for evt in events:
        assert evt.get("status") == "SUCCESSFUL", (
            f"Event {evt.get('id')} status is {evt.get('status')}, expected SUCCESSFUL."
        )
        assert evt.get("destination_id") == destination["id"], (
            f"Event {evt.get('id')} destination_id is {evt.get('destination_id')}, "
            f"expected {destination['id']}."
        )
