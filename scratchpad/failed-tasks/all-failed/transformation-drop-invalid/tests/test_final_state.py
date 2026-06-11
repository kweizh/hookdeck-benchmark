import os
import re
import time
import pytest
import requests

LOG_FILE = "/home/user/hookdeck-task/output.log"
API_BASE = "https://api.hookdeck.com/2025-07-01"
PUBLISH_URL = "https://hkdk.events/v1/publish"

VALID_PAYLOADS = [
    {"user_id": "u-valid-1", "amount": 12.5},
    {"user_id": "u-valid-2", "amount": 99},
]

INVALID_PAYLOADS = [
    {"amount": 10},                           # missing user_id, offending: user_id
    {"user_id": "u-bad", "amount": "10"},     # wrong type amount, offending: amount
    {"user_id": "", "amount": 5},             # empty user_id, offending: user_id
]


@pytest.fixture(scope="session")
def run_id():
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid is not None, "ZEALT_RUN_ID environment variable is not set"
    return rid


@pytest.fixture(scope="session")
def api_key():
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key is not None, "HOOKDECK_API_KEY environment variable is not set"
    return key


@pytest.fixture(scope="session")
def auth_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="session")
def log_contents():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist"
    with open(LOG_FILE, "r") as f:
        return f.read()


@pytest.fixture(scope="session")
def source_id(log_contents):
    m = re.search(r"Source ID:\s*(src_[A-Za-z0-9]+)", log_contents)
    assert m is not None, (
        f"Could not find 'Source ID: src_...' in {LOG_FILE}. "
        f"File contents:\n{log_contents}"
    )
    return m.group(1)


@pytest.fixture(scope="session")
def transformation_id(log_contents):
    m = re.search(r"Transformation ID:\s*(trs?_[A-Za-z0-9]+)", log_contents)
    assert m is not None, (
        f"Could not find 'Transformation ID: trs_... or tr_...' in {LOG_FILE}. "
        f"File contents:\n{log_contents}"
    )
    return m.group(1)


@pytest.fixture(scope="session")
def publish_and_wait(run_id, auth_headers, source_id, transformation_id):
    """Publish all payloads (valid + invalid) once per session and let Hookdeck process them."""
    publish_headers = {
        **auth_headers,
        "X-Hookdeck-Source-Name": f"src-{run_id}",
        "Content-Type": "application/json",
    }

    for payload in VALID_PAYLOADS + INVALID_PAYLOADS:
        resp = requests.post(PUBLISH_URL, headers=publish_headers, json=payload)
        assert resp.status_code == 200, (
            f"Failed to publish payload {payload!r}: {resp.status_code} {resp.text}"
        )

    # Allow Hookdeck to ingest, transform, and deliver the events.
    time.sleep(10)
    return True


def _fetch_all_requests(auth_headers, source_id):
    resp = requests.get(
        f"{API_BASE}/requests",
        headers=auth_headers,
        params={"source_id": source_id, "limit": 50},
    )
    assert resp.status_code == 200, (
        f"Failed to retrieve requests: {resp.status_code} {resp.text}"
    )
    data = resp.json()
    return data.get("models", [])


def _body_of(req):
    return req.get("data", {}).get("body", {}).get("body", {})


def _find_request_matching(requests_list, predicate):
    return next((r for r in requests_list if predicate(_body_of(r))), None)


def test_connection_and_transformation_wired(run_id, auth_headers, transformation_id):
    """The Connection conn-${run-id} must reference the Transformation in its rules."""
    resp = requests.get(
        f"{API_BASE}/connections",
        headers=auth_headers,
        params={"name": f"conn-{run_id}"},
    )
    assert resp.status_code == 200, (
        f"Failed to retrieve connections: {resp.status_code} {resp.text}"
    )
    models = resp.json().get("models", [])
    assert len(models) >= 1, f"No connection named 'conn-{run_id}' found"

    conn = models[0]
    rules = conn.get("rules", []) or []
    transformation_rules = [r for r in rules if r.get("type") == "transformation"]
    assert transformation_rules, (
        f"Connection 'conn-{run_id}' has no transformation rule. Rules: {rules}"
    )
    attached_ids = [r.get("transformation_id") for r in transformation_rules]
    assert transformation_id in attached_ids, (
        f"Transformation {transformation_id} not attached to conn-{run_id}. "
        f"Attached transformation_ids: {attached_ids}"
    )


def test_valid_payloads_delivered_and_invalid_dropped(
    publish_and_wait, auth_headers, source_id
):
    """Each valid payload yields events_count>=1 and ignored_count==0;
    each invalid payload yields events_count==0 and ignored_count>=1."""
    requests_list = _fetch_all_requests(auth_headers, source_id)

    # Valid payloads must have been turned into events.
    for vp in VALID_PAYLOADS:
        match = _find_request_matching(
            requests_list,
            lambda body, vp=vp: body.get("user_id") == vp["user_id"]
            and body.get("amount") == vp["amount"],
        )
        assert match is not None, (
            f"Could not find request for valid payload {vp!r} in Hookdeck"
        )
        assert match.get("events_count", 0) >= 1, (
            f"Valid payload {vp!r} should have created at least one event; "
            f"events_count={match.get('events_count')}"
        )
        assert match.get("ignored_count", 0) == 0, (
            f"Valid payload {vp!r} should NOT have been ignored; "
            f"ignored_count={match.get('ignored_count')}"
        )

    # Invalid payloads must have been ignored (dropped).
    invalid_predicates = [
        # missing user_id -> body has 'amount' but no 'user_id'
        lambda body: body.get("amount") == 10 and "user_id" not in body,
        # wrong-typed amount -> amount is the string "10"
        lambda body: body.get("user_id") == "u-bad" and body.get("amount") == "10",
        # empty user_id
        lambda body: body.get("user_id") == "" and body.get("amount") == 5,
    ]
    for idx, pred in enumerate(invalid_predicates):
        match = _find_request_matching(requests_list, pred)
        assert match is not None, (
            f"Could not find invalid payload #{idx} in Hookdeck requests"
        )
        assert match.get("events_count", 0) == 0, (
            f"Invalid payload #{idx} should NOT have created an event; "
            f"events_count={match.get('events_count')}"
        )
        assert match.get("ignored_count", 0) >= 1, (
            f"Invalid payload #{idx} should have been ignored; "
            f"ignored_count={match.get('ignored_count')}"
        )


def test_only_valid_events_delivered_to_destination(
    publish_and_wait, auth_headers, source_id
):
    """Inspect API: only the 2 valid payloads should appear as SUCCESSFUL events."""
    resp = requests.get(
        f"{API_BASE}/events",
        headers=auth_headers,
        params={"source_id": source_id, "status": "SUCCESSFUL", "limit": 50},
    )
    assert resp.status_code == 200, (
        f"Failed to retrieve events: {resp.status_code} {resp.text}"
    )
    events = resp.json().get("models", [])
    bodies = [
        ev.get("data", {}).get("body", {}).get("body", {}) for ev in events
    ]

    # Each valid payload must be represented by at least one delivered event.
    for vp in VALID_PAYLOADS:
        assert any(
            b.get("user_id") == vp["user_id"] and b.get("amount") == vp["amount"]
            for b in bodies
        ), (
            f"Valid payload {vp!r} not found among successful events. "
            f"Delivered bodies: {bodies}"
        )

    # No invalid payload should ever have been delivered.
    invalid_checks = [
        lambda b: "user_id" not in b and b.get("amount") == 10,
        lambda b: b.get("user_id") == "u-bad" and b.get("amount") == "10",
        lambda b: b.get("user_id") == "" and b.get("amount") == 5,
    ]
    for idx, check in enumerate(invalid_checks):
        assert not any(check(b) for b in bodies), (
            f"Invalid payload #{idx} was unexpectedly delivered as an event"
        )


def test_transformation_logs_structured_validation_failure(
    publish_and_wait, auth_headers, transformation_id
):
    """Among recent transformation executions, at least 3 must include a console.log
    line containing 'validation_failed'. The set of those messages must collectively
    mention 'user_id' (>=2 times) and 'amount' (>=1 time)."""
    resp = requests.get(
        f"{API_BASE}/transformations/{transformation_id}/executions",
        headers=auth_headers,
        params={"limit": 100},
    )
    assert resp.status_code == 200, (
        f"Failed to retrieve transformation executions: "
        f"{resp.status_code} {resp.text}"
    )
    executions = resp.json().get("models", [])
    assert executions, (
        f"No transformation executions found for {transformation_id}"
    )

    validation_failed_messages: list[str] = []
    for ex in executions:
        ex_id = ex.get("id")
        if not ex_id:
            continue
        # Fetch the detailed execution to make sure logs are populated.
        detail_resp = requests.get(
            f"{API_BASE}/transformations/{transformation_id}/executions/{ex_id}",
            headers=auth_headers,
        )
        assert detail_resp.status_code == 200, (
            f"Failed to retrieve execution {ex_id}: "
            f"{detail_resp.status_code} {detail_resp.text}"
        )
        logs = detail_resp.json().get("logs") or []
        for line in logs:
            msg = line.get("message", "") or ""
            if "validation_failed" in msg:
                validation_failed_messages.append(msg)

    assert len(validation_failed_messages) >= 3, (
        f"Expected at least 3 executions with a 'validation_failed' log entry, "
        f"got {len(validation_failed_messages)}. Messages: {validation_failed_messages}"
    )

    user_id_hits = sum(1 for m in validation_failed_messages if "user_id" in m)
    amount_hits = sum(1 for m in validation_failed_messages if "amount" in m)

    assert user_id_hits >= 2, (
        f"Expected at least 2 'validation_failed' messages mentioning 'user_id' "
        f"(missing + empty), got {user_id_hits}. Messages: {validation_failed_messages}"
    )
    assert amount_hits >= 1, (
        f"Expected at least 1 'validation_failed' message mentioning 'amount' "
        f"(wrong type), got {amount_hits}. Messages: {validation_failed_messages}"
    )
