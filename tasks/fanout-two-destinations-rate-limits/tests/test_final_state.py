import os
import re
from datetime import datetime

import pytest
import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
LOG_PATH = "/home/user/hookdeck-fanout/output.log"


# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------


def _api_key() -> str:
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable must be set."
    return api_key


def _run_id() -> str:
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable must be set."
    return run_id


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_api_key()}"}


def _get(path: str, params: dict | None = None) -> dict:
    resp = requests.get(
        f"{API_BASE}{path}", headers=_auth_headers(), params=params, timeout=30
    )
    assert resp.status_code == 200, (
        f"GET {path} failed: HTTP {resp.status_code} body={resp.text!r}"
    )
    return resp.json()


def _list_all(path: str, params: dict | None = None) -> list:
    """List all models across paginated responses (200 per page is enough here)."""
    params = dict(params or {})
    params.setdefault("limit", 250)
    out: list = []
    next_cursor = None
    for _ in range(10):  # safety bound; we never expect > a few pages
        page_params = dict(params)
        if next_cursor:
            page_params["next"] = next_cursor
        data = _get(path, page_params)
        out.extend(data.get("models", []))
        next_cursor = data.get("pagination", {}).get("next")
        if not next_cursor:
            break
    return out


def _parse_ts(ts: str) -> datetime:
    # Hookdeck timestamps look like "2026-01-14T13:36:06.675Z" (possibly with
    # microseconds). datetime.fromisoformat accepts ISO 8601 if we replace 'Z'.
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Step 2: parse the executor's log file
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def logged_ids() -> dict:
    assert os.path.isfile(LOG_PATH), f"Log file {LOG_PATH} does not exist."
    with open(LOG_PATH, "r", encoding="utf-8") as fh:
        content = fh.read()

    patterns = {
        "source_id": r"Source ID:\s*(\S+)",
        "fast_destination_id": r"Fast Destination ID:\s*(\S+)",
        "slow_destination_id": r"Slow Destination ID:\s*(\S+)",
        "fast_connection_id": r"Fast Connection ID:\s*(\S+)",
        "slow_connection_id": r"Slow Connection ID:\s*(\S+)",
        "published_events": r"Published Events:\s*(\d+)",
    }

    extracted: dict = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        assert match, (
            f"Log file is missing required line for {key!r}; "
            f"expected pattern {pattern!r} in {LOG_PATH}."
        )
        extracted[key] = match.group(1)

    assert extracted["published_events"] == "12", (
        f"Log reports {extracted['published_events']} published events, expected 12."
    )
    return extracted


# ---------------------------------------------------------------------------
# Step 3: Source verification
# ---------------------------------------------------------------------------


def test_source_exists_with_expected_name_and_type(logged_ids: dict):
    run_id = _run_id()
    expected_name = f"fanout-src-{run_id}"
    sources = _list_all("/sources", {"name": expected_name})
    assert len(sources) == 1, (
        f"Expected exactly 1 source named {expected_name!r}, got {len(sources)}: "
        f"{[s.get('name') for s in sources]}"
    )
    src = sources[0]
    assert src["id"] == logged_ids["source_id"], (
        f"Source ID mismatch: API returned {src['id']!r}, "
        f"log reports {logged_ids['source_id']!r}."
    )
    assert src.get("type") == "WEBHOOK", (
        f"Source type must be WEBHOOK, got {src.get('type')!r}."
    )


# ---------------------------------------------------------------------------
# Step 4: Destination verification (rate-limit configuration contract)
# ---------------------------------------------------------------------------


def test_fast_destination_is_mock_api_with_no_rate_limit(logged_ids: dict):
    run_id = _run_id()
    expected_name = f"fanout-fast-{run_id}"
    dests = _list_all("/destinations", {"name": expected_name})
    assert len(dests) == 1, (
        f"Expected exactly 1 destination named {expected_name!r}, got {len(dests)}."
    )
    dest = dests[0]
    assert dest["id"] == logged_ids["fast_destination_id"], (
        f"Fast destination ID mismatch: API {dest['id']!r}, "
        f"log {logged_ids['fast_destination_id']!r}."
    )
    assert dest.get("type") == "MOCK_API", (
        f"Fast destination type must be MOCK_API, got {dest.get('type')!r}."
    )
    rate_limit = dest.get("config", {}).get("rate_limit")
    assert rate_limit in (None, 0), (
        f"Fast destination must have no rate_limit (null/unset), got {rate_limit!r}."
    )


def test_slow_destination_is_mock_api_with_2_per_second(logged_ids: dict):
    run_id = _run_id()
    expected_name = f"fanout-slow-{run_id}"
    dests = _list_all("/destinations", {"name": expected_name})
    assert len(dests) == 1, (
        f"Expected exactly 1 destination named {expected_name!r}, got {len(dests)}."
    )
    dest = dests[0]
    assert dest["id"] == logged_ids["slow_destination_id"], (
        f"Slow destination ID mismatch: API {dest['id']!r}, "
        f"log {logged_ids['slow_destination_id']!r}."
    )
    assert dest.get("type") == "MOCK_API", (
        f"Slow destination type must be MOCK_API, got {dest.get('type')!r}."
    )
    config = dest.get("config", {})
    assert config.get("rate_limit") == 2, (
        f"Slow destination must have rate_limit=2, got {config.get('rate_limit')!r}."
    )
    assert config.get("rate_limit_period") == "second", (
        "Slow destination must have rate_limit_period='second', "
        f"got {config.get('rate_limit_period')!r}."
    )


# ---------------------------------------------------------------------------
# Step 5: Connection topology verification
# ---------------------------------------------------------------------------


def _get_connection_by_name(name: str) -> dict:
    conns = _list_all("/connections", {"name": name})
    assert len(conns) == 1, (
        f"Expected exactly 1 connection named {name!r}, got {len(conns)}."
    )
    return conns[0]


def test_fast_connection_links_source_to_fast_destination(logged_ids: dict):
    run_id = _run_id()
    conn = _get_connection_by_name(f"fanout-fast-conn-{run_id}")
    assert conn["id"] == logged_ids["fast_connection_id"], (
        f"Fast connection ID mismatch: API {conn['id']!r}, "
        f"log {logged_ids['fast_connection_id']!r}."
    )
    assert conn.get("source", {}).get("id") == logged_ids["source_id"], (
        "Fast connection is not attached to the expected source."
    )
    assert (
        conn.get("destination", {}).get("id") == logged_ids["fast_destination_id"]
    ), "Fast connection is not attached to the fast destination."
    assert conn.get("disabled_at") is None, "Fast connection must not be disabled."
    assert conn.get("paused_at") is None, "Fast connection must not be paused."


def test_slow_connection_links_source_to_slow_destination(logged_ids: dict):
    run_id = _run_id()
    conn = _get_connection_by_name(f"fanout-slow-conn-{run_id}")
    assert conn["id"] == logged_ids["slow_connection_id"], (
        f"Slow connection ID mismatch: API {conn['id']!r}, "
        f"log {logged_ids['slow_connection_id']!r}."
    )
    assert conn.get("source", {}).get("id") == logged_ids["source_id"], (
        "Slow connection is not attached to the expected source."
    )
    assert (
        conn.get("destination", {}).get("id") == logged_ids["slow_destination_id"]
    ), "Slow connection is not attached to the slow destination."
    # The slow connection's destination must itself enforce the rate limit.
    slow_cfg = conn.get("destination", {}).get("config", {})
    assert slow_cfg.get("rate_limit") == 2, (
        "Slow connection's destination must expose rate_limit=2, "
        f"got {slow_cfg.get('rate_limit')!r}."
    )
    assert slow_cfg.get("rate_limit_period") == "second", (
        "Slow connection's destination must expose rate_limit_period='second', "
        f"got {slow_cfg.get('rate_limit_period')!r}."
    )


# ---------------------------------------------------------------------------
# Step 6 & 7: Event delivery + rate-limit timing contract
# ---------------------------------------------------------------------------


def _successful_events_for_destination(destination_id: str) -> list[dict]:
    events = _list_all(
        "/events",
        {"destination_id": destination_id, "status": "SUCCESSFUL", "limit": 250},
    )
    return events


def test_fast_destination_received_all_12_events_without_pacing(logged_ids: dict):
    events = _successful_events_for_destination(logged_ids["fast_destination_id"])
    assert len(events) == 12, (
        f"Expected 12 SUCCESSFUL events on the fast destination, "
        f"got {len(events)}."
    )

    timestamps = [_parse_ts(e["successful_at"]) for e in events]
    spread = (max(timestamps) - min(timestamps)).total_seconds()
    assert spread < 2.0, (
        "Fast (uncapped) destination should deliver in a tight burst "
        f"(< 2s spread). Observed spread = {spread:.3f}s."
    )


def test_slow_destination_received_all_12_events_with_rate_limit_pacing(
    logged_ids: dict,
):
    events = _successful_events_for_destination(logged_ids["slow_destination_id"])
    assert len(events) == 12, (
        f"Expected 12 SUCCESSFUL events on the slow destination, "
        f"got {len(events)}."
    )

    timestamps = [_parse_ts(e["successful_at"]) for e in events]
    spread = (max(timestamps) - min(timestamps)).total_seconds()
    assert spread >= 5.0, (
        "Slow destination (rate_limit=2/second) must show pacing across "
        f"12 events: expected spread >= 5.0s, observed {spread:.3f}s."
    )


def test_events_are_owned_by_the_two_expected_connections(logged_ids: dict):
    fast_events = _successful_events_for_destination(
        logged_ids["fast_destination_id"]
    )
    slow_events = _successful_events_for_destination(
        logged_ids["slow_destination_id"]
    )

    fast_webhook_ids = {e["webhook_id"] for e in fast_events}
    slow_webhook_ids = {e["webhook_id"] for e in slow_events}

    assert fast_webhook_ids == {logged_ids["fast_connection_id"]}, (
        f"Fast destination events must all come from the fast connection "
        f"{logged_ids['fast_connection_id']!r}; got {fast_webhook_ids}."
    )
    assert slow_webhook_ids == {logged_ids["slow_connection_id"]}, (
        f"Slow destination events must all come from the slow connection "
        f"{logged_ids['slow_connection_id']!r}; got {slow_webhook_ids}."
    )
