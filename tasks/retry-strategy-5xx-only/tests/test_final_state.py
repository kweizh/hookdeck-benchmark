import os
import re

import pytest
import requests

LOG_PATH = "/home/user/hookdeck-task/output.log"
API_BASE = "https://api.hookdeck.com/2025-07-01"
EXPECTED_5XX_CODES = {"500", "502", "503", "504"}


def _read_log_text() -> str:
    assert os.path.isfile(LOG_PATH), f"Log file {LOG_PATH} does not exist."
    with open(LOG_PATH, "r") as f:
        return f.read()


def _extract_id(text: str, prefix: str, id_prefix: str) -> str:
    pattern = rf"{re.escape(prefix)}\s*({re.escape(id_prefix)}[A-Za-z0-9_]+)"
    match = re.search(pattern, text)
    assert match is not None, (
        f"Could not find a '{prefix} {id_prefix}...' line in {LOG_PATH}. "
        f"Log content was:\n{text}"
    )
    return match.group(1)


@pytest.fixture(scope="module")
def run_id() -> str:
    value = os.environ.get("ZEALT_RUN_ID")
    assert value, "ZEALT_RUN_ID environment variable is not set."
    return value


@pytest.fixture(scope="module")
def api_headers() -> dict:
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="module")
def log_ids() -> dict:
    text = _read_log_text()
    return {
        "connection_a_id": _extract_id(text, "Connection A ID:", "web_"),
        "connection_b_id": _extract_id(text, "Connection B ID:", "web_"),
        "event_a_id": _extract_id(text, "Event A ID:", "evt_"),
        "event_b_id": _extract_id(text, "Event B ID:", "evt_"),
    }


def _get_json(url: str, headers: dict, params: dict | None = None) -> dict:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    assert response.status_code == 200, (
        f"GET {url} (params={params}) returned status {response.status_code}: {response.text}"
    )
    return response.json()


def _retry_rules(rules: list) -> list:
    return [r for r in rules if isinstance(r, dict) and r.get("type") == "retry"]


def test_log_file_has_all_ids(log_ids):
    assert log_ids["connection_a_id"].startswith("web_"), \
        f"Invalid Connection A ID format: {log_ids['connection_a_id']}"
    assert log_ids["connection_b_id"].startswith("web_"), \
        f"Invalid Connection B ID format: {log_ids['connection_b_id']}"
    assert log_ids["event_a_id"].startswith("evt_"), \
        f"Invalid Event A ID format: {log_ids['event_a_id']}"
    assert log_ids["event_b_id"].startswith("evt_"), \
        f"Invalid Event B ID format: {log_ids['event_b_id']}"


def test_connection_a_configuration(run_id, api_headers, log_ids):
    connection_id = log_ids["connection_a_id"]
    data = _get_json(f"{API_BASE}/connections/{connection_id}", api_headers)

    expected_name = f"conn-a-{run_id}"
    assert data.get("name") == expected_name, \
        f"Connection A name mismatch: expected '{expected_name}', got '{data.get('name')}'"

    source = data.get("source", {}) or {}
    assert source.get("name") == f"src-a-{run_id}", \
        f"Connection A source name mismatch: got '{source.get('name')}'"
    assert source.get("type") == "WEBHOOK", \
        f"Connection A source type must be WEBHOOK, got '{source.get('type')}'"

    destination = data.get("destination", {}) or {}
    assert destination.get("name") == f"dest-a-{run_id}", \
        f"Connection A destination name mismatch: got '{destination.get('name')}'"
    assert destination.get("type") == "HTTP", \
        f"Connection A destination type must be HTTP, got '{destination.get('type')}'"

    rules = data.get("rules") or []
    retry_rules = _retry_rules(rules)
    assert len(retry_rules) == 1, \
        f"Connection A must have exactly one retry rule, found {len(retry_rules)}: {rules}"
    retry_rule = retry_rules[0]

    assert retry_rule.get("strategy") == "linear", \
        f"Connection A retry strategy must be 'linear', got '{retry_rule.get('strategy')}'"
    assert retry_rule.get("interval") == 30000, \
        f"Connection A retry interval must be 30000 ms, got {retry_rule.get('interval')}"
    assert retry_rule.get("count") == 5, \
        f"Connection A retry count must be 5, got {retry_rule.get('count')}"

    codes = retry_rule.get("response_status_codes") or []
    codes_as_str = {str(c) for c in codes}
    assert codes_as_str == EXPECTED_5XX_CODES, (
        "Connection A retry rule response_status_codes must equal "
        f"{sorted(EXPECTED_5XX_CODES)} (as set); got {sorted(codes_as_str)}"
    )


def test_connection_b_configuration(run_id, api_headers, log_ids):
    connection_id = log_ids["connection_b_id"]
    data = _get_json(f"{API_BASE}/connections/{connection_id}", api_headers)

    expected_name = f"conn-b-{run_id}"
    assert data.get("name") == expected_name, \
        f"Connection B name mismatch: expected '{expected_name}', got '{data.get('name')}'"

    source = data.get("source", {}) or {}
    assert source.get("name") == f"src-b-{run_id}", \
        f"Connection B source name mismatch: got '{source.get('name')}'"
    assert source.get("type") == "WEBHOOK", \
        f"Connection B source type must be WEBHOOK, got '{source.get('type')}'"

    destination = data.get("destination", {}) or {}
    assert destination.get("name") == f"dest-b-{run_id}", \
        f"Connection B destination name mismatch: got '{destination.get('name')}'"
    assert destination.get("type") == "HTTP", \
        f"Connection B destination type must be HTTP, got '{destination.get('type')}'"

    rules = data.get("rules") or []
    retry_rules = _retry_rules(rules)
    assert len(retry_rules) == 1, \
        f"Connection B must have exactly one retry rule, found {len(retry_rules)}: {rules}"
    retry_rule = retry_rules[0]

    codes = retry_rule.get("response_status_codes") or []
    codes_as_str = {str(c) for c in codes}
    assert codes_as_str & EXPECTED_5XX_CODES, (
        "Connection B retry rule must include at least one 5xx code "
        f"({sorted(EXPECTED_5XX_CODES)}); got {sorted(codes_as_str)}"
    )
    assert "422" not in codes_as_str, (
        "Connection B retry rule must NOT include 422; "
        f"got response_status_codes={sorted(codes_as_str)}"
    )


def test_event_a_state(api_headers, log_ids):
    event_id = log_ids["event_a_id"]
    data = _get_json(f"{API_BASE}/events/{event_id}", api_headers)

    assert data.get("webhook_id") == log_ids["connection_a_id"], (
        f"Event A is associated with webhook {data.get('webhook_id')}, "
        f"expected {log_ids['connection_a_id']}"
    )
    attempts = data.get("attempts")
    assert isinstance(attempts, int) and attempts >= 3, \
        f"Event A must have attempts >= 3, got {attempts}"
    assert data.get("status") == "SUCCESSFUL", \
        f"Event A final status must be SUCCESSFUL, got '{data.get('status')}'"


def test_event_a_attempts_history(api_headers, log_ids):
    event_id = log_ids["event_a_id"]
    params = {
        "event_id": event_id,
        "limit": 100,
        "order_by": "created_at",
        "dir": "asc",
    }
    data = _get_json(f"{API_BASE}/attempts", api_headers, params=params)
    models = data.get("models") or []
    assert len(models) >= 3, \
        f"Expected at least 3 attempts for Event A, got {len(models)}: {models}"

    for attempt in models:
        status = attempt.get("status")
        assert status in {"SUCCESSFUL", "FAILED"}, (
            f"GET /attempts must only return SUCCESSFUL or FAILED attempts; "
            f"got status '{status}' in attempt {attempt}"
        )

    latest = max(models, key=lambda a: a.get("attempt_number") or 0)
    assert latest.get("status") == "SUCCESSFUL", (
        f"The most recent attempt for Event A must be SUCCESSFUL; "
        f"got {latest.get('status')} on attempt #{latest.get('attempt_number')}"
    )

    five_xx_failed = [
        a for a in models
        if a.get("status") == "FAILED"
        and isinstance(a.get("response_status"), int)
        and 500 <= a["response_status"] <= 599
    ]
    assert len(five_xx_failed) >= 1, (
        "Event A must have at least one earlier FAILED attempt with a 5xx response_status; "
        f"attempts were: {[(a.get('attempt_number'), a.get('status'), a.get('response_status')) for a in models]}"
    )


def test_event_b_state(api_headers, log_ids):
    event_id = log_ids["event_b_id"]
    data = _get_json(f"{API_BASE}/events/{event_id}", api_headers)

    assert data.get("webhook_id") == log_ids["connection_b_id"], (
        f"Event B is associated with webhook {data.get('webhook_id')}, "
        f"expected {log_ids['connection_b_id']}"
    )
    attempts = data.get("attempts")
    assert attempts == 1, f"Event B must have exactly 1 attempt, got {attempts}"
    assert data.get("status") == "FAILED", \
        f"Event B final status must be FAILED, got '{data.get('status')}'"


def test_event_b_attempts_history(api_headers, log_ids):
    event_id = log_ids["event_b_id"]
    data = _get_json(
        f"{API_BASE}/attempts",
        api_headers,
        params={"event_id": event_id, "limit": 100},
    )
    models = data.get("models") or []
    assert len(models) == 1, \
        f"Event B must have exactly 1 attempt in /attempts, got {len(models)}: {models}"

    attempt = models[0]
    assert attempt.get("status") == "FAILED", \
        f"Event B attempt must be FAILED, got '{attempt.get('status')}'"
    assert attempt.get("response_status") == 422, \
        f"Event B attempt response_status must be 422, got {attempt.get('response_status')}"
