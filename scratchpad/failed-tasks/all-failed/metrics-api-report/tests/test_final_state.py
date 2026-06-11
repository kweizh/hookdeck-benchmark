"""Final-state verification for the `metrics_api_report` task.

The verifier re-queries the Hookdeck Metrics API for the same one-hour window
and compares the agent-produced report against the live data within a small
numeric tolerance.
"""

import json
import math
import os
from datetime import datetime, timedelta, timezone

import pytest
import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
WORKSPACE = "/workspace"
REPORT_PATH = os.path.join(WORKSPACE, "report.json")
RESOURCE_IDS_PATH = os.path.join(WORKSPACE, "resource_ids.json")
SEED_COUNT_PATH = os.path.join(WORKSPACE, "seed_event_count.txt")

COUNT_TOLERANCE = 2  # ±2 events for stable counters
RATE_TOLERANCE = 5.0  # ±5 percentage points for error_rate
QUEUE_TOLERANCE = 2  # ±2 for queue depth gauge


def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key, "HOOKDECK_API_KEY env var must be set for verification."
    return key


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Accept": "application/json",
    }


def _load_report() -> dict:
    assert os.path.isfile(REPORT_PATH), (
        f"Expected agent to produce {REPORT_PATH}; file does not exist."
    )
    with open(REPORT_PATH) as f:
        return json.load(f)


def _load_resource_ids() -> dict:
    assert os.path.isfile(RESOURCE_IDS_PATH), (
        f"Initial-state file {RESOURCE_IDS_PATH} missing — seeding did not run."
    )
    with open(RESOURCE_IDS_PATH) as f:
        return json.load(f)


def _load_seed_count() -> int:
    assert os.path.isfile(SEED_COUNT_PATH), (
        f"Initial-state file {SEED_COUNT_PATH} missing — seeding did not run."
    )
    with open(SEED_COUNT_PATH) as f:
        return int(f.read().strip())


def _date_range_params() -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=1)
    # Widen the end-of-window slightly to absorb clock drift between agent and verifier.
    end = end + timedelta(minutes=2)
    return {
        "date_range[start]": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "date_range[end]": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _metrics_get(path: str, extra_params: dict) -> list:
    params = {**_date_range_params(), **extra_params}
    resp = requests.get(
        f"{API_BASE}{path}",
        headers=_auth_headers(),
        params=params,
        timeout=60,
    )
    assert resp.status_code == 200, (
        f"GET {path} failed with {resp.status_code}: {resp.text[:500]}"
    )
    payload = resp.json()
    assert "data" in payload and isinstance(payload["data"], list), (
        f"Unexpected response shape for {path}: {payload!r}"
    )
    return payload["data"]


def test_report_file_exists_and_is_json():
    report = _load_report()
    expected_keys = {
        "requests_last_hour",
        "events_by_issue",
        "transformation_error_rate",
        "queue_depth",
    }
    actual_keys = set(report.keys())
    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    assert not missing, f"report.json is missing required keys: {sorted(missing)}"
    assert not extra, (
        f"report.json contains unexpected top-level keys: {sorted(extra)}. "
        f"Only {sorted(expected_keys)} are allowed."
    )


def test_report_value_types():
    report = _load_report()

    requests_last_hour = report["requests_last_hour"]
    assert isinstance(requests_last_hour, int) and not isinstance(
        requests_last_hour, bool
    ), (
        f"requests_last_hour must be int, got {type(requests_last_hour).__name__}: "
        f"{requests_last_hour!r}"
    )
    assert requests_last_hour >= 0, "requests_last_hour must be non-negative."

    events_by_issue = report["events_by_issue"]
    assert isinstance(events_by_issue, dict), (
        f"events_by_issue must be a JSON object, got "
        f"{type(events_by_issue).__name__}: {events_by_issue!r}"
    )
    for k, v in events_by_issue.items():
        assert isinstance(k, str) and k, (
            f"events_by_issue keys must be non-empty strings; got {k!r}"
        )
        assert isinstance(v, int) and not isinstance(v, bool) and v >= 0, (
            f"events_by_issue['{k}'] must be a non-negative int, got {v!r}"
        )

    transformation_error_rate = report["transformation_error_rate"]
    assert (
        isinstance(transformation_error_rate, (int, float))
        and not isinstance(transformation_error_rate, bool)
        and math.isfinite(float(transformation_error_rate))
    ), (
        f"transformation_error_rate must be a finite number, got "
        f"{type(transformation_error_rate).__name__}: {transformation_error_rate!r}"
    )
    assert 0.0 <= float(transformation_error_rate) <= 100.0, (
        f"transformation_error_rate must lie in [0, 100], got "
        f"{transformation_error_rate!r}"
    )

    queue_depth = report["queue_depth"]
    assert isinstance(queue_depth, int) and not isinstance(queue_depth, bool), (
        f"queue_depth must be int, got {type(queue_depth).__name__}: {queue_depth!r}"
    )
    assert queue_depth >= 0, "queue_depth must be non-negative."


def test_requests_last_hour_matches_metrics_api():
    report = _load_report()
    ids = _load_resource_ids()
    seed_count = _load_seed_count()

    rows = _metrics_get(
        "/metrics/requests",
        {
            "measures[]": "count",
            "filters[source_id]": ids["source_id"],
        },
    )
    verifier_count = 0
    for row in rows:
        metrics = row.get("metrics") or {}
        verifier_count += int(metrics.get("count") or 0)

    reported = report["requests_last_hour"]
    assert reported >= seed_count, (
        f"requests_last_hour ({reported}) should be at least the seeded count "
        f"({seed_count}); the agent likely failed to query /metrics/requests for the seeded source."
    )
    assert abs(reported - verifier_count) <= COUNT_TOLERANCE, (
        f"requests_last_hour mismatch: report={reported}, verifier={verifier_count}, "
        f"tolerance=±{COUNT_TOLERANCE}."
    )


def test_events_by_issue_matches_metrics_api():
    report = _load_report()
    ids = _load_resource_ids()

    rows = _metrics_get(
        "/metrics/events-by-issue",
        {
            "measures[]": "count",
            "dimensions[]": "issue_id",
            "filters[connection_id]": ids["connection_id"],
        },
    )
    verifier_map: dict = {}
    for row in rows:
        dims = row.get("dimensions") or {}
        issue_id = dims.get("issue_id")
        if not issue_id:
            continue
        metrics = row.get("metrics") or {}
        verifier_map[issue_id] = verifier_map.get(issue_id, 0) + int(
            metrics.get("count") or 0
        )

    reported_map = {k: int(v) for k, v in report["events_by_issue"].items()}

    assert set(reported_map.keys()) == set(verifier_map.keys()), (
        f"events_by_issue key set mismatch: report={sorted(reported_map)}, "
        f"verifier={sorted(verifier_map)}"
    )
    for issue_id, verifier_count in verifier_map.items():
        reported_count = reported_map[issue_id]
        assert abs(reported_count - verifier_count) <= COUNT_TOLERANCE, (
            f"events_by_issue['{issue_id}'] mismatch: report={reported_count}, "
            f"verifier={verifier_count}, tolerance=±{COUNT_TOLERANCE}."
        )


def test_transformation_error_rate_matches_metrics_api():
    report = _load_report()
    ids = _load_resource_ids()

    rows = _metrics_get(
        "/metrics/transformations",
        {
            "measures[]": "error_rate",
            "filters[connection_id]": ids["connection_id"],
        },
    )
    verifier_rate = 0.0
    for row in rows:
        metrics = row.get("metrics") or {}
        verifier_rate = max(verifier_rate, float(metrics.get("error_rate") or 0))

    reported_rate = float(report["transformation_error_rate"])
    assert abs(reported_rate - verifier_rate) <= RATE_TOLERANCE, (
        f"transformation_error_rate mismatch: report={reported_rate}, "
        f"verifier={verifier_rate}, tolerance=±{RATE_TOLERANCE}."
    )


def test_queue_depth_matches_metrics_api():
    report = _load_report()
    ids = _load_resource_ids()

    rows = _metrics_get(
        "/metrics/queue-depth",
        {
            "measures[]": "max_depth",
            "filters[destination_id]": ids["destination_id"],
        },
    )
    verifier_depth = 0
    for row in rows:
        metrics = row.get("metrics") or {}
        verifier_depth = max(verifier_depth, int(metrics.get("max_depth") or 0))

    reported_depth = int(report["queue_depth"])
    assert abs(reported_depth - verifier_depth) <= QUEUE_TOLERANCE, (
        f"queue_depth mismatch: report={reported_depth}, verifier={verifier_depth}, "
        f"tolerance=±{QUEUE_TOLERANCE}."
    )
