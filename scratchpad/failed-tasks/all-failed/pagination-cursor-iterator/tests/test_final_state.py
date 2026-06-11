import json
import os
import urllib.parse

import pytest
import requests

PROJECT_DIR = "/workspace"
RESULT_FILE = os.path.join(PROJECT_DIR, "result.json")
CONN_ID_FILE = os.path.join(PROJECT_DIR, ".target_connection_id")
HOOKDECK_API = "https://api.hookdeck.com/2025-07-01"
MIN_EVENTS = 250


def _resolve_target_connection_id() -> str:
    cid = os.environ.get("TARGET_CONNECTION_ID")
    if cid:
        return cid
    if os.path.isfile(CONN_ID_FILE):
        with open(CONN_ID_FILE, "r") as f:
            cid = f.read().strip()
            if cid:
                return cid
    pytest.fail(
        "TARGET_CONNECTION_ID is not set and /workspace/.target_connection_id is missing."
    )


def _paginate_all_events(api_key: str, connection_id: str):
    """Independently paginate using the documented cursor (`next`) API."""
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key}"})
    all_ids = []
    seen = set()
    cursor = None
    pages = 0
    while True:
        params = {"webhook_id": connection_id, "limit": 250}
        if cursor:
            params["next"] = cursor
        url = f"{HOOKDECK_API}/events?{urllib.parse.urlencode(params)}"
        resp = session.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"Verifier pagination request failed: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        for model in body.get("models", []):
            ev_id = model.get("id")
            if ev_id and ev_id not in seen:
                seen.add(ev_id)
                all_ids.append(ev_id)
        cursor = (body.get("pagination") or {}).get("next")
        pages += 1
        if not cursor:
            break
        assert pages < 100, "Verifier traversed too many pages; likely a cursor loop."
    return all_ids


def test_result_file_exists():
    assert os.path.isfile(
        RESULT_FILE
    ), f"Expected the executor to write {RESULT_FILE}; file is missing."


def test_result_file_is_valid_json_with_required_keys():
    with open(RESULT_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"{RESULT_FILE} is not valid JSON: {e}")
    assert isinstance(data, dict), f"{RESULT_FILE} must contain a JSON object."
    for key, expected_type, type_label in (
        ("total", int, "integer"),
        ("first_id", str, "string"),
        ("last_id", str, "string"),
    ):
        assert key in data, f"Result JSON is missing required key '{key}'."
        # bool is a subclass of int in Python; reject it explicitly.
        if expected_type is int and isinstance(data[key], bool):
            pytest.fail(f"Result key '{key}' must be an integer, got a boolean.")
        assert isinstance(data[key], expected_type), (
            f"Result key '{key}' must be a {type_label}, got {type(data[key]).__name__}."
        )


def test_total_matches_independently_paginated_count():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing in the verifier."
    connection_id = _resolve_target_connection_id()

    with open(RESULT_FILE, "r") as f:
        data = json.load(f)

    verified_ids = _paginate_all_events(api_key, connection_id)
    verified_total = len(verified_ids)
    assert verified_total >= MIN_EVENTS, (
        f"Verifier collected only {verified_total} events for connection "
        f"{connection_id}; seeding pre-condition (>= {MIN_EVENTS}) was not met."
    )

    submitted_total = data["total"]
    assert submitted_total == verified_total, (
        f"Submitted total ({submitted_total}) does not match the verifier's "
        f"independently paginated count ({verified_total}) for connection {connection_id}."
    )


def test_first_and_last_ids_are_real_connection_events():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing in the verifier."
    connection_id = _resolve_target_connection_id()

    with open(RESULT_FILE, "r") as f:
        data = json.load(f)

    verified_set = set(_paginate_all_events(api_key, connection_id))

    first_id = data["first_id"]
    last_id = data["last_id"]

    assert first_id in verified_set, (
        f"first_id={first_id!r} is not a valid event id for connection "
        f"{connection_id}."
    )
    assert last_id in verified_set, (
        f"last_id={last_id!r} is not a valid event id for connection "
        f"{connection_id}."
    )
