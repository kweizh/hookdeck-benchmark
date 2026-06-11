"""Initial-state verification for the `metrics_api_report` task.

This module both validates the prerequisites for the task and provisions the
Hookdeck resources that the agent will later query. All shared, externally
visible resources are scoped by ``ZEALT_RUN_ID`` so concurrent trials do not
collide.
"""

import json
import os
import time
from datetime import datetime, timezone

import pytest
import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
PROJECT_DIR = "/home/user/myproject"
WORKSPACE = "/workspace"
RESOURCE_IDS_PATH = os.path.join(WORKSPACE, "resource_ids.json")
SEED_COUNT_PATH = os.path.join(WORKSPACE, "seed_event_count.txt")
SEED_EVENTS = 5
METRICS_SETTLE_SECONDS = 25


def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key, "HOOKDECK_API_KEY env var must be set for the initial-state setup."
    return key


def _run_id() -> str:
    rid = os.environ.get("ZEALT_RUN_ID", "").strip()
    assert rid, "ZEALT_RUN_ID env var must be set so resources can be scoped per trial."
    return rid


def _auth_headers() -> dict:
    return {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def test_requests_library_available():
    # The agent and the verifier both rely on the `requests` library.
    import requests as _requests  # noqa: F401

    assert True


def test_hookdeck_api_key_env_var_set():
    assert os.environ.get("HOOKDECK_API_KEY"), (
        "HOOKDECK_API_KEY must be exported in the task environment."
    )


def test_zealt_run_id_env_var_set():
    assert os.environ.get("ZEALT_RUN_ID", "").strip(), (
        "ZEALT_RUN_ID must be exported so per-trial Hookdeck resources are isolated."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} must exist before the task starts."
    )


def test_workspace_directory_exists():
    os.makedirs(WORKSPACE, exist_ok=True)
    assert os.path.isdir(WORKSPACE), (
        f"Workspace directory {WORKSPACE} must exist so the agent can write report.json."
    )


def test_hookdeck_api_reachable():
    resp = requests.get(
        f"{API_BASE}/sources",
        headers=_auth_headers(),
        params={"limit": 1},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Hookdeck API must be reachable from the environment "
        f"(GET /sources returned {resp.status_code}: {resp.text[:200]})."
    )


def _put_json(url: str, payload: dict) -> dict:
    resp = requests.put(url, headers=_auth_headers(), json=payload, timeout=60)
    assert resp.status_code in (200, 201), (
        f"PUT {url} failed with {resp.status_code}: {resp.text[:500]}"
    )
    return resp.json()


def test_provision_hookdeck_resources_and_seed_metrics():
    """Provision per-run Hookdeck resources and pre-seed traffic.

    The function is idempotent: PUT-based upserts mean retrying the initial
    state will reuse existing resources for the same run-id rather than
    duplicating them.
    """
    run_id = _run_id()
    src_name = f"metrics-src-{run_id}"
    dst_name = f"metrics-dst-{run_id}"
    conn_name = f"metrics-conn-{run_id}"
    trf_name = f"metrics-trf-{run_id}"

    # 1. Upsert source.
    source = _put_json(
        f"{API_BASE}/sources",
        {"name": src_name, "type": "WEBHOOK"},
    )
    source_id = source["id"]
    source_url = source.get("url")
    assert source_url, f"Source response missing url field: {source}"

    # 2. Upsert mock destination.
    destination = _put_json(
        f"{API_BASE}/destinations",
        {
            "name": dst_name,
            "type": "HTTP",
            "config": {"url": "https://mock.hookdeck.com/metrics-test"},
        },
    )
    destination_id = destination["id"]

    # 3. Upsert a JS transformation so the transformations metric reports data.
    transformation_code = (
        "addHandler('transform', (request, context) => {\n"
        "  request.headers['x-zealt-metrics-test'] = 'true';\n"
        "  return request;\n"
        "});\n"
    )
    transformation = _put_json(
        f"{API_BASE}/transformations",
        {"name": trf_name, "code": transformation_code},
    )
    transformation_id = transformation["id"]

    # 4. Upsert the connection wiring source -> transform -> destination.
    connection = _put_json(
        f"{API_BASE}/connections",
        {
            "name": conn_name,
            "source": {"id": source_id},
            "destination": {"id": destination_id},
            "rules": [
                {
                    "type": "transform",
                    "transformation": {"id": transformation_id},
                }
            ],
        },
    )
    connection_id = connection["id"]

    # 5. Seed inbound traffic by POSTing JSON to the source URL. Each POST
    #    produces one request, one event, and one transformation execution.
    seeded = 0
    last_error = None
    for i in range(SEED_EVENTS):
        try:
            r = requests.post(
                source_url,
                headers={"Content-Type": "application/json"},
                json={
                    "type": "metrics.test",
                    "i": i,
                    "ts": datetime.now(timezone.utc).isoformat(),
                },
                timeout=30,
            )
            if r.status_code in (200, 201, 202):
                seeded += 1
            else:
                last_error = f"Seed POST {i} returned {r.status_code}: {r.text[:200]}"
        except requests.RequestException as exc:  # pragma: no cover - network noise
            last_error = f"Seed POST {i} raised: {exc!r}"
    assert seeded > 0, f"Failed to seed any traffic to the source. Last error: {last_error}"

    # 6. Allow Hookdeck enough time to aggregate near-real-time metrics.
    time.sleep(METRICS_SETTLE_SECONDS)

    # 7. Persist resource IDs and the seed count so the agent and verifier can
    #    scope their metrics queries to this run.
    os.makedirs(WORKSPACE, exist_ok=True)
    with open(RESOURCE_IDS_PATH, "w") as f:
        json.dump(
            {
                "source_id": source_id,
                "destination_id": destination_id,
                "connection_id": connection_id,
                "transformation_id": transformation_id,
            },
            f,
            indent=2,
            sort_keys=True,
        )
    with open(SEED_COUNT_PATH, "w") as f:
        f.write(str(seeded))


def test_resource_ids_file_was_written():
    assert os.path.isfile(RESOURCE_IDS_PATH), (
        f"{RESOURCE_IDS_PATH} must exist after provisioning Hookdeck resources."
    )
    with open(RESOURCE_IDS_PATH) as f:
        data = json.load(f)
    for key in ("source_id", "destination_id", "connection_id"):
        assert isinstance(data.get(key), str) and data[key], (
            f"resource_ids.json is missing a string value for '{key}'."
        )


def test_seed_event_count_file_was_written():
    assert os.path.isfile(SEED_COUNT_PATH), (
        f"{SEED_COUNT_PATH} must record how many events were seeded."
    )
    with open(SEED_COUNT_PATH) as f:
        text = f.read().strip()
    assert text.isdigit() and int(text) > 0, (
        f"seed_event_count.txt must contain a positive integer; got {text!r}."
    )
