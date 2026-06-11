import base64
import json
import os
import time

import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-project"
SOURCE_JSON_PATH = os.path.join(PROJECT_DIR, "source.json")

HOOKDECK_API_BASE = "https://api.hookdeck.com/2025-07-01"
EXPECTED_USERNAME = "eval-user"
EXPECTED_PASSWORD = "eval-pass"
EXPECTED_CUSTOM_BODY = {"ok": True, "id": "abc"}


@pytest.fixture(scope="session")
def run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID")
    assert rid, "ZEALT_RUN_ID environment variable is missing in the verifier environment"
    return rid


@pytest.fixture(scope="session")
def api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key, "HOOKDECK_API_KEY environment variable is missing in the verifier environment"
    return key


@pytest.fixture(scope="session")
def auth_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="session")
def source_log() -> dict:
    assert os.path.exists(SOURCE_JSON_PATH), f"{SOURCE_JSON_PATH} does not exist"
    with open(SOURCE_JSON_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            pytest.fail(f"{SOURCE_JSON_PATH} does not contain valid JSON: {exc}")
    assert isinstance(data, dict), f"{SOURCE_JSON_PATH} must contain a JSON object"
    assert "source_id" in data and isinstance(data["source_id"], str) and data["source_id"].startswith("src_"), (
        f"source.json is missing a valid `source_id` (expected string starting with 'src_'); got: {data!r}"
    )
    assert "source_url" in data and isinstance(data["source_url"], str) and data["source_url"].startswith("http"), (
        f"source.json is missing a valid `source_url` (expected http(s) URL); got: {data!r}"
    )
    return data


@pytest.fixture(scope="session")
def source_obj(source_log: dict, auth_headers: dict) -> dict:
    source_id = source_log["source_id"]
    url = f"{HOOKDECK_API_BASE}/sources/{source_id}"
    resp = requests.get(url, headers=auth_headers, timeout=30)
    assert resp.status_code == 200, f"Failed to retrieve source {source_id}: HTTP {resp.status_code} {resp.text}"
    return resp.json()


def test_source_basic_auth_config(source_obj: dict, run_id: str):
    assert source_obj.get("type") == "WEBHOOK", (
        f"Source must be of type WEBHOOK, got {source_obj.get('type')!r}"
    )
    name = source_obj.get("name", "")
    assert isinstance(name, str) and name.endswith(f"-{run_id}"), (
        f"Source name must end with '-{run_id}', got {name!r}"
    )

    config = source_obj.get("config") or {}
    assert config.get("auth_type") == "BASIC_AUTH", (
        f"Expected source config.auth_type == 'BASIC_AUTH', got {config.get('auth_type')!r}"
    )
    auth = config.get("auth") or {}
    assert auth.get("username") == EXPECTED_USERNAME, (
        f"Expected source basic auth username {EXPECTED_USERNAME!r}, got {auth.get('username')!r}"
    )
    assert auth.get("password") == EXPECTED_PASSWORD, (
        f"Expected source basic auth password {EXPECTED_PASSWORD!r}, got {auth.get('password')!r}"
    )


def test_source_custom_response_config(source_obj: dict):
    config = source_obj.get("config") or {}
    custom_response = config.get("custom_response")
    assert isinstance(custom_response, dict), (
        f"Source config.custom_response must be an object, got {custom_response!r}"
    )
    assert custom_response.get("content_type") == "json", (
        f"Expected custom_response.content_type == 'json', got {custom_response.get('content_type')!r}"
    )
    body_raw = custom_response.get("body")
    assert isinstance(body_raw, str) and body_raw.strip(), (
        f"custom_response.body must be a non-empty string, got {body_raw!r}"
    )
    try:
        body_parsed = json.loads(body_raw)
    except json.JSONDecodeError as exc:
        pytest.fail(f"custom_response.body is not valid JSON: {body_raw!r} ({exc})")
    assert body_parsed == EXPECTED_CUSTOM_BODY, (
        f"custom_response.body JSON must equal {EXPECTED_CUSTOM_BODY!r}, got {body_parsed!r}"
    )


def test_source_url_matches_log(source_obj: dict, source_log: dict):
    api_url = source_obj.get("url")
    assert isinstance(api_url, str) and api_url.startswith("http"), (
        f"Source `url` from API must be an http(s) URL, got {api_url!r}"
    )
    assert source_log["source_url"].rstrip("/") == api_url.rstrip("/"), (
        f"source.json source_url {source_log['source_url']!r} does not match Hookdeck API source.url {api_url!r}"
    )


def test_connection_and_mock_destination(source_log: dict, auth_headers: dict, run_id: str):
    source_id = source_log["source_id"]
    url = f"{HOOKDECK_API_BASE}/connections"
    resp = requests.get(url, headers=auth_headers, params={"source_id": source_id}, timeout=30)
    assert resp.status_code == 200, f"Failed to list connections for source: HTTP {resp.status_code} {resp.text}"
    data = resp.json()
    models = data.get("models") or []
    assert models, f"No connections found for source {source_id}"

    run_suffix = f"-{run_id}"
    suffixed = [c for c in models if isinstance(c.get("name"), str) and c["name"].endswith(run_suffix)]
    assert suffixed, (
        f"No connection name ends with '-{run_id}'; connections found: {[c.get('name') for c in models]}"
    )

    connection = suffixed[0]
    destination = connection.get("destination") or {}
    dest_id = destination.get("id")
    assert isinstance(dest_id, str) and dest_id, f"Connection is missing a destination id: {connection!r}"

    dest_resp = requests.get(f"{HOOKDECK_API_BASE}/destinations/{dest_id}", headers=auth_headers, timeout=30)
    assert dest_resp.status_code == 200, f"Failed to fetch destination {dest_id}: HTTP {dest_resp.status_code} {dest_resp.text}"
    dest = dest_resp.json()

    dest_name = dest.get("name", "")
    assert isinstance(dest_name, str) and dest_name.endswith(run_suffix), (
        f"Destination name must end with '-{run_id}', got {dest_name!r}"
    )

    dest_type = dest.get("type")
    dest_config_url = (dest.get("config") or {}).get("url") or ""
    is_mock = dest_type == "MOCK_API" or (
        dest_type == "HTTP" and "mock.hookdeck.com" in dest_config_url
    )
    assert is_mock, (
        f"Destination must be MOCK_API (or HTTP pointing at mock.hookdeck.com); got type={dest_type!r}, url={dest_config_url!r}"
    )


def test_live_authorized_probe_returns_custom_response(source_log: dict, run_id: str):
    source_url = source_log["source_url"]
    creds = f"{EXPECTED_USERNAME}:{EXPECTED_PASSWORD}".encode("utf-8")
    headers = {
        "Authorization": "Basic " + base64.b64encode(creds).decode("ascii"),
        "Content-Type": "application/json",
    }
    payload = {"probe": "auth-ok", "run": run_id}
    resp = requests.post(source_url, headers=headers, json=payload, timeout=30)
    assert resp.status_code == 200, (
        f"Authorized POST to source URL must return 200, got {resp.status_code}; body={resp.text!r}"
    )
    content_type = resp.headers.get("Content-Type", "")
    assert "json" in content_type.lower(), (
        f"Authorized response Content-Type must indicate JSON, got {content_type!r}"
    )
    try:
        body = resp.json()
    except ValueError as exc:
        pytest.fail(f"Authorized response body is not valid JSON: {resp.text!r} ({exc})")
    assert body == EXPECTED_CUSTOM_BODY, (
        f"Authorized response body must equal {EXPECTED_CUSTOM_BODY!r}, got {body!r}"
    )


def test_live_unauthorized_probe_returns_401(source_log: dict, run_id: str):
    source_url = source_log["source_url"]
    # Wrong password
    wrong = f"{EXPECTED_USERNAME}:wrong-pass".encode("utf-8")
    headers = {
        "Authorization": "Basic " + base64.b64encode(wrong).decode("ascii"),
        "Content-Type": "application/json",
    }
    payload = {"probe": "auth-bad", "run": run_id}
    resp = requests.post(source_url, headers=headers, json=payload, timeout=30)
    assert resp.status_code == 401, (
        f"Unauthorized POST to source URL must return 401, got {resp.status_code}; body={resp.text!r}"
    )


def _list_requests(source_id: str, auth_headers: dict) -> list:
    # Pull a generous page of recent requests for the source to scan for our probes.
    resp = requests.get(
        f"{HOOKDECK_API_BASE}/requests",
        headers=auth_headers,
        params={"source_id": source_id, "limit": 100},
        timeout=30,
    )
    assert resp.status_code == 200, f"Failed to list requests for source: HTTP {resp.status_code} {resp.text}"
    return resp.json().get("models") or []


def _request_matches(request_obj: dict, probe_value: str, run_id: str) -> bool:
    data = request_obj.get("data") or {}
    body = data.get("body")
    # Hookdeck may nest the inbound body under data.body.body
    if isinstance(body, dict) and "body" in body and isinstance(body["body"], (dict, list)):
        inner = body["body"]
    else:
        inner = body
    if isinstance(inner, dict):
        return inner.get("probe") == probe_value and inner.get("run") == run_id
    if isinstance(inner, str):
        return f'"probe": "{probe_value}"' in inner and f'"run": "{run_id}"' in inner
    return False


def test_inspect_api_records_authorized_request_only(source_log: dict, auth_headers: dict, run_id: str):
    source_id = source_log["source_id"]

    # Hookdeck ingestion has a small async delay; poll briefly.
    deadline = time.time() + 30
    authorized_hits = []
    unauthorized_hits = []
    while time.time() < deadline:
        models = _list_requests(source_id, auth_headers)
        authorized_hits = [m for m in models if _request_matches(m, "auth-ok", run_id)]
        unauthorized_hits = [m for m in models if _request_matches(m, "auth-bad", run_id)]
        if authorized_hits:
            break
        time.sleep(3)

    assert len(authorized_hits) >= 1, (
        f"Expected at least one ingested request with probe=auth-ok and run={run_id}; found none."
    )
    assert not unauthorized_hits, (
        f"Unauthorized POSTs must not be ingested by Hookdeck, but {len(unauthorized_hits)} matching request(s) were found."
    )
