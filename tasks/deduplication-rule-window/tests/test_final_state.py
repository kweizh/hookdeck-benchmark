import os
import re

import pytest
import requests


PROJECT_DIR = "/home/user/hookdeck-dedup"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"


def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY", "")
    assert key, "HOOKDECK_API_KEY is required to verify Hookdeck state via REST API."
    return key


def _run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID", "")
    assert rid, "ZEALT_RUN_ID is required to compute the expected Hookdeck resource names."
    return rid


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}"}


@pytest.fixture(scope="module")
def parsed_log() -> dict:
    assert os.path.isfile(LOG_FILE), (
        f"Expected the executor to write a summary log to {LOG_FILE}."
    )
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    def grab(label: str, prefix: str) -> str:
        match = re.search(rf"^{re.escape(label)}:\s*({prefix}[A-Za-z0-9_]+)\s*$", content, re.MULTILINE)
        assert match, (
            f"Expected a line of the form '{label}: {prefix}...' in {LOG_FILE}. "
            f"Log contents:\n{content}"
        )
        return match.group(1)

    return {
        "connection_id": grab("Connection ID", "web_"),
        "source_id": grab("Source ID", "src_"),
        "destination_id": grab("Destination ID", "des_"),
    }


def test_log_file_records_resource_ids(parsed_log: dict):
    assert parsed_log["connection_id"].startswith("web_"), (
        "Connection ID in the log should be a Hookdeck connection (webhook) ID prefixed with 'web_'."
    )
    assert parsed_log["source_id"].startswith("src_"), (
        "Source ID in the log should be a Hookdeck source ID prefixed with 'src_'."
    )
    assert parsed_log["destination_id"].startswith("des_"), (
        "Destination ID in the log should be a Hookdeck destination ID prefixed with 'des_'."
    )


def test_connection_uses_run_id_named_resources_and_mock_destination(parsed_log: dict):
    run_id = _run_id()
    expected_source_name = f"dedup-src-{run_id}"
    expected_destination_name = f"dedup-dst-{run_id}"

    resp = requests.get(
        f"{API_BASE}/connections/{parsed_log['connection_id']}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Expected to fetch connection {parsed_log['connection_id']} (HTTP 200) "
        f"but got {resp.status_code}: {resp.text}"
    )
    conn = resp.json()

    assert conn.get("source", {}).get("id") == parsed_log["source_id"], (
        "Connection's source id does not match the Source ID recorded in the log file."
    )
    assert conn.get("source", {}).get("name") == expected_source_name, (
        f"Expected the connection's source name to be '{expected_source_name}', "
        f"but got {conn.get('source', {}).get('name')!r}."
    )

    assert conn.get("destination", {}).get("id") == parsed_log["destination_id"], (
        "Connection's destination id does not match the Destination ID recorded in the log file."
    )
    assert conn.get("destination", {}).get("name") == expected_destination_name, (
        f"Expected the connection's destination name to be '{expected_destination_name}', "
        f"but got {conn.get('destination', {}).get('name')!r}."
    )
    assert conn.get("destination", {}).get("type") == "MOCK_API", (
        "The destination on the dedup connection must be a Mock API destination "
        "(type == 'MOCK_API') so events are accepted by Hookdeck's mock endpoint."
    )


def test_connection_has_single_deduplicate_rule_with_300s_window_on_id_and_type(parsed_log: dict):
    resp = requests.get(
        f"{API_BASE}/connections/{parsed_log['connection_id']}",
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Expected to fetch connection {parsed_log['connection_id']} (HTTP 200) "
        f"but got {resp.status_code}: {resp.text}"
    )
    conn = resp.json()

    rules = conn.get("rules")
    assert isinstance(rules, list) and len(rules) == 1, (
        f"Expected exactly one rule on the connection, got: {rules!r}"
    )
    rule = rules[0]

    assert rule.get("type") == "deduplicate", (
        f"Expected the single rule to be of type 'deduplicate', got: {rule!r}"
    )

    # Hookdeck deduplicate rule windows are expressed in milliseconds.
    # A 5 minute window = 300 seconds = 300000 ms.
    assert rule.get("window") == 300000, (
        "Expected the deduplicate rule's window to be 300000 ms (5 minutes), "
        f"got: {rule.get('window')!r}. See https://hookdeck.com/docs/deduplication for units."
    )

    include_fields = rule.get("include_fields")
    assert isinstance(include_fields, list), (
        f"Expected include_fields to be a list, got: {include_fields!r}"
    )
    assert set(include_fields) == {"body.id", "body.type"}, (
        "Expected the deduplicate rule's include_fields to dedupe on the JSON body's "
        "'id' and 'type' fields. Hookdeck requires field paths to start with one of "
        "'body', 'headers', 'query', 'path' (see https://hookdeck.com/docs/deduplication#field-path-resolution); "
        f"got include_fields={include_fields!r}."
    )

    assert not rule.get("exclude_fields"), (
        "The deduplicate rule must not set exclude_fields when include_fields is used; "
        f"got exclude_fields={rule.get('exclude_fields')!r}."
    )


def test_exactly_three_successful_events_delivered_through_connection(parsed_log: dict):
    resp = requests.get(
        f"{API_BASE}/events",
        params={
            "webhook_id": parsed_log["connection_id"],
            "status": "SUCCESSFUL",
            "limit": 100,
        },
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list events for connection {parsed_log['connection_id']}: "
        f"HTTP {resp.status_code}: {resp.text}"
    )
    body = resp.json()

    count = body.get("count")
    models = body.get("models", []) or []
    assert count == 3, (
        "Expected exactly 3 SUCCESSFUL events on the dedup connection (5 duplicates "
        "collapse into 1 delivery plus 2 distinct events = 3 total), "
        f"but Hookdeck reports count={count}."
    )
    assert len(models) == 3, (
        f"Expected exactly 3 event records in the response, got {len(models)}."
    )

    for event in models:
        assert event.get("status") == "SUCCESSFUL", (
            f"Every returned event must have status SUCCESSFUL, got: {event}"
        )
        assert event.get("webhook_id") == parsed_log["connection_id"], (
            f"Event {event.get('id')} is associated with a different connection: "
            f"{event.get('webhook_id')} vs expected {parsed_log['connection_id']}."
        )
        assert event.get("destination_id") == parsed_log["destination_id"], (
            f"Event {event.get('id')} was not delivered to the dedup destination: "
            f"{event.get('destination_id')} vs expected {parsed_log['destination_id']}."
        )


def test_duplicate_requests_were_ignored_by_deduplication(parsed_log: dict):
    resp = requests.get(
        f"{API_BASE}/requests",
        params={
            "source_id": parsed_log["source_id"],
            "limit": 100,
        },
        headers=_auth_headers(),
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Failed to list requests for source {parsed_log['source_id']}: "
        f"HTTP {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    requests_list = body.get("models", []) or []

    assert requests_list, (
        f"Expected at least one ingested request for source {parsed_log['source_id']}, "
        "but Hookdeck returned an empty list. Did the executor publish any events?"
    )

    total_ignored = sum(int(r.get("ignored_count") or 0) for r in requests_list)
    total_events = sum(int(r.get("events_count") or 0) for r in requests_list)

    assert total_ignored >= 4, (
        "Expected at least 4 duplicate requests to be marked ignored "
        "(5 identical {id, type} publishes minus the first one that became the delivered event), "
        f"but the sum of ignored_count across requests for source {parsed_log['source_id']} is {total_ignored}."
    )
    assert total_events == 3, (
        "Expected the sum of events_count across requests for the dedup source to be exactly 3 "
        "(matching the 3 events the executor expects to flow through), "
        f"but got {total_events}."
    )
