import json
import os
import re
from datetime import datetime, timezone

import pytest
import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
WORKSPACE = "/workspace"
QUERY_SCRIPT = os.path.join(WORKSPACE, "query.py")
WINDOW_PATH = os.path.join(WORKSPACE, "window.json")
SEED_PATH = os.path.join(WORKSPACE, "seed.json")

API_KEY = os.environ.get("HOOKDECK_API_KEY", "")


def _auth_headers():
    assert API_KEY, "HOOKDECK_API_KEY environment variable is required for verification."
    return {"Authorization": f"Bearer {API_KEY}"}


def _parse_iso8601(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def _list_events(source_id: str, gte: str, lte: str) -> list[dict]:
    """Walk full pagination, applying the requested server-side filter."""
    collected: list[dict] = []
    next_cursor = None
    safety = 0
    while True:
        safety += 1
        if safety > 100:
            raise AssertionError("Pagination loop exceeded 100 pages; aborting to avoid infinite loop.")
        params = [
            ("source_id", source_id),
            ("created_at[gte]", gte),
            ("created_at[lte]", lte),
            ("limit", "250"),
            ("order_by", "created_at"),
            ("dir", "asc"),
        ]
        if next_cursor:
            params.append(("next", next_cursor))
        resp = requests.get(f"{API_BASE}/events", headers=_auth_headers(), params=params, timeout=30)
        assert resp.status_code == 200, (
            f"Hookdeck list-events call failed: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        collected.extend(body.get("models", []) or [])
        next_cursor = (body.get("pagination") or {}).get("next")
        if not next_cursor:
            break
    return collected


@pytest.fixture(scope="module")
def seed() -> dict:
    assert os.path.isfile(SEED_PATH), f"Seed file {SEED_PATH} missing; initial state did not run."
    with open(SEED_PATH) as fh:
        data = json.load(fh)
    for key in ("source_id", "window_start", "window_end", "expected_ids"):
        assert key in data, f"Seed file is missing key '{key}'."
    return data


@pytest.fixture(scope="module")
def window_output() -> dict:
    assert os.path.isfile(WINDOW_PATH), (
        f"Expected candidate-produced artifact {WINDOW_PATH} to exist."
    )
    with open(WINDOW_PATH) as fh:
        data = json.load(fh)
    return data


def test_query_script_exists():
    assert os.path.isfile(QUERY_SCRIPT), (
        f"Candidate script {QUERY_SCRIPT} not found; the task requires writing this file."
    )


def test_query_script_uses_server_side_operators():
    """The candidate must compose the server-side query operators, not filter client-side."""
    with open(QUERY_SCRIPT) as fh:
        source = fh.read()
    assert "created_at[gte]" in source, (
        "Candidate script must reference `created_at[gte]` to compose the server-side filter."
    )
    assert "created_at[lte]" in source, (
        "Candidate script must reference `created_at[lte]` to compose the server-side filter."
    )


def test_window_output_schema(window_output: dict):
    assert set(window_output.keys()) == {"count", "ids"}, (
        f"window.json must have exactly keys {{'count', 'ids'}}, got {sorted(window_output.keys())}"
    )
    assert isinstance(window_output["count"], int), "window.json `count` must be an integer."
    assert isinstance(window_output["ids"], list), "window.json `ids` must be a JSON array."
    for eid in window_output["ids"]:
        assert isinstance(eid, str) and re.match(r"^evt_[A-Za-z0-9]+$", eid), (
            f"window.json `ids` entry is not a valid Hookdeck event id: {eid!r}"
        )
    assert window_output["count"] == len(window_output["ids"]), (
        f"window.json `count` ({window_output['count']}) must equal len(ids) ({len(window_output['ids'])})."
    )
    assert len(set(window_output["ids"])) == len(window_output["ids"]), (
        "window.json `ids` contains duplicate entries."
    )


def test_seed_expectation_matches_live_server(seed: dict):
    """Independently issue the same server-side query and confirm the seed expectation is still authoritative."""
    server_events = _list_events(seed["source_id"], seed["window_start"], seed["window_end"])
    server_ids = sorted(e["id"] for e in server_events)
    expected_ids = sorted(seed["expected_ids"])
    assert server_ids == expected_ids, (
        "Server-side query returned a different set of event IDs than the seed recorded.\n"
        f"Server: {server_ids}\nSeed:   {expected_ids}"
    )


def test_window_output_matches_server_side_query(window_output: dict, seed: dict):
    server_events = _list_events(seed["source_id"], seed["window_start"], seed["window_end"])
    server_ids = {e["id"] for e in server_events}
    candidate_ids = set(window_output["ids"])
    extra = candidate_ids - server_ids
    missing = server_ids - candidate_ids
    assert not extra, (
        f"window.json contains {len(extra)} event id(s) not returned by the authoritative server-side query: {sorted(extra)}"
    )
    assert not missing, (
        f"window.json is missing {len(missing)} event id(s) that the server-side query returned: {sorted(missing)}"
    )
    assert window_output["count"] == len(server_ids), (
        f"window.json count ({window_output['count']}) must equal server-side count ({len(server_ids)})."
    )


def test_no_events_outside_window(window_output: dict, seed: dict):
    """For each id in the candidate output, fetch it individually and assert created_at lies inside the window."""
    start = _parse_iso8601(seed["window_start"])
    end = _parse_iso8601(seed["window_end"])
    for eid in window_output["ids"]:
        resp = requests.get(f"{API_BASE}/events/{eid}", headers=_auth_headers(), timeout=30)
        assert resp.status_code == 200, (
            f"Failed to fetch event {eid} for verification: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        created_at = body.get("created_at")
        assert isinstance(created_at, str), f"Event {eid} has no `created_at` field."
        ts = _parse_iso8601(created_at)
        assert start <= ts <= end, (
            f"Event {eid} created_at={created_at} falls outside the window "
            f"[{seed['window_start']}, {seed['window_end']}]."
        )
