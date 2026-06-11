import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone

import pytest
import requests

LOG_FILE = "/home/user/myproject/output.log"
API_BASE = "https://api.hookdeck.com/2025-07-01"
PUBLISH_URL = "https://hkdk.events/v1/publish"


# ---------------------------------------------------------------------------
# Shared session-scoped state extracted from the executor's log file and the
# Hookdeck API.
# ---------------------------------------------------------------------------


def _read_env_or_skip():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert api_key, "HOOKDECK_API_KEY must be set in the verifier environment."
    assert run_id, "ZEALT_RUN_ID must be set in the verifier environment."
    return api_key, run_id


def _auth_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _parse_log_file() -> dict:
    assert os.path.isfile(LOG_FILE), f"Expected log file {LOG_FILE} to exist."
    with open(LOG_FILE) as f:
        content = f.read()
    fields = {}
    patterns = {
        "source_name": r"Source\s*Name\s*:\s*(\S+)",
        "destination_name": r"Destination\s*Name\s*:\s*(\S+)",
        "connection_id": r"Connection\s*ID\s*:\s*(\S+)",
        "transformation_id": r"Transformation\s*ID\s*:\s*(\S+)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, content)
        assert m, f"Could not find '{key}' in {LOG_FILE}. Contents:\n{content}"
        fields[key] = m.group(1).strip()
    return fields


def _ci_get(headers: dict, key: str):
    """Case-insensitive lookup helper for header dictionaries."""
    if not isinstance(headers, dict):
        return None
    lowered = {k.lower(): v for k, v in headers.items()}
    return lowered.get(key.lower())


def _expected_names(run_id: str) -> dict:
    return {
        "source_name": f"hmac-src-{run_id}",
        "destination_name": f"hmac-dst-{run_id}",
        "transformation_name": f"hmac-trf-{run_id}",
        "connection_name": f"hmac-conn-{run_id}",
        "expected_secret": f"s3cr3t-{run_id}",
    }


@pytest.fixture(scope="session")
def env_state():
    api_key, run_id = _read_env_or_skip()
    log_fields = _parse_log_file()
    names = _expected_names(run_id)
    return {
        "api_key": api_key,
        "run_id": run_id,
        "log": log_fields,
        "names": names,
    }


@pytest.fixture(scope="session")
def transformation(env_state):
    api_key = env_state["api_key"]
    trf_id = env_state["log"]["transformation_id"]
    r = requests.get(
        f"{API_BASE}/transformations/{trf_id}",
        headers=_auth_headers(api_key),
        timeout=30,
    )
    assert r.status_code == 200, (
        f"GET /transformations/{trf_id} failed: status={r.status_code} body={r.text}"
    )
    return r.json()


@pytest.fixture(scope="session")
def connection(env_state):
    api_key = env_state["api_key"]
    conn_id = env_state["log"]["connection_id"]
    r = requests.get(
        f"{API_BASE}/connections/{conn_id}",
        headers=_auth_headers(api_key),
        timeout=30,
    )
    assert r.status_code == 200, (
        f"GET /connections/{conn_id} failed: status={r.status_code} body={r.text}"
    )
    return r.json()


@pytest.fixture(scope="session")
def delivered_event(env_state, connection, transformation):
    """
    Publishes a deterministic JSON payload to the configured source and polls
    the Inspect API until a successful delivery is observed.
    """
    api_key = env_state["api_key"]
    run_id = env_state["run_id"]
    names = env_state["names"]
    source_name = env_state["log"]["source_name"]
    conn_id = env_state["log"]["connection_id"]

    # Sanity: log-declared source name must match the run-id-derived name so the
    # publish URL is correct.
    assert source_name == names["source_name"], (
        f"Log declares source name '{source_name}' but expected '{names['source_name']}'."
    )

    payload = {
        "order_id": f"ord-{run_id}",
        "amount": 4242,
        "status": "created",
    }
    publish_resp = requests.post(
        PUBLISH_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Hookdeck-Source-Name": source_name,
        },
        data=json.dumps(payload),
        timeout=30,
    )
    assert publish_resp.status_code < 300, (
        f"Publish API rejected the verifier event: status={publish_resp.status_code} body={publish_resp.text}"
    )

    deadline = time.time() + 90
    last_resp_text = ""
    event = None
    while time.time() < deadline:
        r = requests.get(
            f"{API_BASE}/events",
            headers=_auth_headers(api_key),
            params={
                "connection_id": conn_id,
                "limit": 20,
                "order_by": "created_at",
                "dir": "desc",
            },
            timeout=30,
        )
        last_resp_text = r.text
        if r.status_code == 200:
            for candidate in r.json().get("models", []):
                if candidate.get("status") == "SUCCESSFUL":
                    # Fetch the full event to ensure data.headers / data.body present
                    ev_id = candidate.get("id")
                    ev = requests.get(
                        f"{API_BASE}/events/{ev_id}",
                        headers=_auth_headers(api_key),
                        timeout=30,
                    )
                    if ev.status_code == 200:
                        ev_json = ev.json()
                        delivered_headers = (ev_json.get("data") or {}).get("headers")
                        if isinstance(delivered_headers, dict) and _ci_get(
                            delivered_headers, "x-hd-signature"
                        ):
                            event = ev_json
                            break
        if event is not None:
            break
        time.sleep(3)

    assert event is not None, (
        "Timed out waiting for a SUCCESSFUL delivered event with an "
        f"x-hd-signature header. Last list response: {last_resp_text[:500]}"
    )
    return {"payload": payload, "event": event}


# ---------------------------------------------------------------------------
# Tests — each maps to a numbered step in the verification plan.
# ---------------------------------------------------------------------------


def test_log_file_contains_required_fields(env_state):
    log = env_state["log"]
    names = env_state["names"]
    assert log["source_name"] == names["source_name"], (
        f"Expected Source Name '{names['source_name']}' in log, got '{log['source_name']}'."
    )
    assert log["destination_name"] == names["destination_name"], (
        f"Expected Destination Name '{names['destination_name']}' in log, got '{log['destination_name']}'."
    )
    assert log["connection_id"].startswith("web_"), (
        f"Connection ID '{log['connection_id']}' does not look like a Hookdeck connection ID."
    )
    assert (
        log["transformation_id"].startswith("trs_")
        or log["transformation_id"].startswith("trf_")
    ), f"Transformation ID '{log['transformation_id']}' does not look like a Hookdeck transformation ID."


def test_transformation_env_and_code(env_state, transformation):
    names = env_state["names"]
    assert transformation.get("name") == names["transformation_name"], (
        f"Expected transformation name '{names['transformation_name']}', got '{transformation.get('name')}'."
    )
    env = transformation.get("env") or {}
    assert isinstance(env, dict), (
        f"Transformation 'env' must be an object, got: {type(env).__name__}"
    )
    assert env.get("MY_SECRET") == names["expected_secret"], (
        f"Expected transformation env MY_SECRET='{names['expected_secret']}', got '{env.get('MY_SECRET')}'."
    )
    code = transformation.get("code") or ""
    for needle in ("process.env.MY_SECRET", "x-hd-signature", "x-hd-signed-at"):
        assert needle in code, (
            f"Transformation code is missing required reference to '{needle}'. Code:\n{code}"
        )


def test_connection_wiring(env_state, connection, transformation):
    names = env_state["names"]
    assert connection.get("name") == names["connection_name"], (
        f"Expected connection name '{names['connection_name']}', got '{connection.get('name')}'."
    )
    source = connection.get("source") or {}
    destination = connection.get("destination") or {}
    assert source.get("name") == names["source_name"], (
        f"Connection source name mismatch: expected '{names['source_name']}', got '{source.get('name')}'."
    )
    assert source.get("type") == "WEBHOOK", (
        f"Connection source type must be 'WEBHOOK', got '{source.get('type')}'."
    )
    assert destination.get("name") == names["destination_name"], (
        f"Connection destination name mismatch: expected '{names['destination_name']}', got '{destination.get('name')}'."
    )
    dtype = destination.get("type")
    dcfg = destination.get("config") or {}
    durl = dcfg.get("url") or ""
    assert dtype == "MOCK_API" or (
        dtype == "HTTP" and isinstance(durl, str) and durl.startswith("https://mock.hookdeck.com/")
    ), (
        f"Destination must be MOCK_API or HTTP pointing at https://mock.hookdeck.com/...; "
        f"got type='{dtype}' url='{durl}'."
    )
    rules = connection.get("rules") or []
    trf_rule_ids = [
        r.get("transformation_id") for r in rules if r.get("type") == "transformation"
    ]
    assert transformation.get("id") in trf_rule_ids, (
        f"Connection rules do not reference transformation_id='{transformation.get('id')}'. "
        f"Found transformation rules: {trf_rule_ids}"
    )


def test_secret_not_leaked_in_non_transformation_resources(env_state, connection):
    secret = env_state["names"]["expected_secret"]
    raw = json.dumps(connection)
    assert secret not in raw, (
        "Secret value appears in the Connection (including source/destination); "
        "it must live only in the transformation env."
    )


def test_signature_header_matches_recomputed_hmac(env_state, delivered_event):
    secret = env_state["names"]["expected_secret"].encode()
    event = delivered_event["event"]
    data = event.get("data") or {}
    headers = data.get("headers") or {}
    body_wrap = data.get("body")

    # Hookdeck's Inspect representation places the actual delivered body under
    # `data.body.body`; fall back to `data.body` itself if not wrapped.
    if isinstance(body_wrap, dict) and "body" in body_wrap and isinstance(body_wrap["body"], (dict, list)):
        delivered_body = body_wrap["body"]
    else:
        delivered_body = body_wrap

    assert delivered_body is not None, (
        f"Could not extract delivered JSON body from event.data.body: {body_wrap!r}"
    )

    serialized = json.dumps(delivered_body, separators=(",", ":"))
    expected_sig = hmac.new(secret, serialized.encode(), hashlib.sha256).hexdigest()

    actual_sig = _ci_get(headers, "x-hd-signature")
    assert actual_sig, (
        f"Delivered event headers missing 'x-hd-signature'. Headers: {list(headers.keys())}"
    )
    actual_sig = actual_sig.strip()
    assert re.fullmatch(r"[0-9a-f]{64}", actual_sig.lower()), (
        f"x-hd-signature is not a 64-char lowercase hex string: '{actual_sig}'"
    )
    assert actual_sig.lower() == expected_sig, (
        f"x-hd-signature mismatch.\n  expected (from {serialized!r}): {expected_sig}\n  actual:   {actual_sig.lower()}"
    )


def test_signed_at_header_is_fresh_iso(env_state, delivered_event):
    headers = (delivered_event["event"].get("data") or {}).get("headers") or {}
    raw = _ci_get(headers, "x-hd-signed-at")
    assert raw, (
        f"Delivered event headers missing 'x-hd-signed-at'. Headers: {list(headers.keys())}"
    )
    raw = raw.strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        pytest.fail(f"x-hd-signed-at '{raw}' is not ISO-8601 parseable: {exc}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = abs((datetime.now(timezone.utc) - parsed).total_seconds())
    assert delta <= 60, (
        f"x-hd-signed-at '{raw}' is not within 60s of current time (delta={delta:.1f}s)."
    )
