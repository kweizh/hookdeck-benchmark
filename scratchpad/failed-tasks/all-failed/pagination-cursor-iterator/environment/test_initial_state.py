import importlib.util
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

import pytest

PROJECT_DIR = "/workspace"
HOOKDECK_API = "https://api.hookdeck.com/2025-07-01"
SEED_TARGET = 260  # must remain > 250
PUBLISH_TIMEOUT = 30
INGESTION_TIMEOUT_SEC = 240


def _hookdeck_request(method: str, path: str, api_key: str, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        f"{HOOKDECK_API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _count_events_for_connection(api_key: str, connection_id: str) -> int:
    """Paginate via the documented cursor API and count events."""
    seen = 0
    cursor = None
    while True:
        params = {"webhook_id": connection_id, "limit": "250"}
        if cursor:
            params["next"] = cursor
        qs = urllib.parse.urlencode(params)
        page = _hookdeck_request("GET", f"/events?{qs}", api_key)
        seen += page.get("count", 0)
        cursor = (page.get("pagination") or {}).get("next")
        if not cursor:
            break
    return seen


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI binary not found in PATH."


def test_python_requests_available():
    assert (
        importlib.util.find_spec("requests") is not None
    ), "Python 'requests' library is not installed."


def test_required_env_vars_set():
    assert os.environ.get(
        "HOOKDECK_API_KEY"
    ), "HOOKDECK_API_KEY environment variable is not set."
    assert os.environ.get(
        "ZEALT_RUN_ID"
    ), "ZEALT_RUN_ID environment variable is not set."


def test_hookdeck_cli_logged_in():
    """Authenticate the Hookdeck CLI in this headless environment."""
    api_key = os.environ["HOOKDECK_API_KEY"]
    result = subprocess.run(
        ["hookdeck", "ci", "--api-key", api_key],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"`hookdeck ci --api-key ...` failed (rc={result.returncode}). "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_seed_target_connection_and_events():
    """Create an isolated connection scoped to this run-id and seed > 250 events."""
    api_key = os.environ["HOOKDECK_API_KEY"]
    run_id = os.environ["ZEALT_RUN_ID"]

    source_name = f"paginate-src-{run_id}"
    dest_name = f"paginate-dst-{run_id}"
    conn_name = f"paginate-conn-{run_id}"

    # Reuse an existing connection with this name if present (parallel-run safety).
    existing = _hookdeck_request(
        "GET",
        f"/connections?name={urllib.parse.quote(conn_name)}&limit=1",
        api_key,
    )
    if existing.get("count", 0) > 0:
        conn = existing["models"][0]
    else:
        payload = {
            "name": conn_name,
            "source": {"name": source_name, "type": "WEBHOOK"},
            "destination": {"name": dest_name, "type": "MOCK_API"},
        }
        conn = _hookdeck_request("POST", "/connections", api_key, payload)

    connection_id = conn["id"]
    source_url = conn["source"]["url"]
    assert connection_id, "Failed to obtain target connection id."
    assert source_url, "Failed to obtain seeded source URL for publishing."

    # How many events already exist for this connection? Only top up the deficit.
    existing_count = _count_events_for_connection(api_key, connection_id)
    deficit = max(0, SEED_TARGET - existing_count)

    for i in range(deficit):
        body = json.dumps(
            {"seq": existing_count + i, "run_id": run_id, "ts": time.time()}
        ).encode("utf-8")
        req = urllib.request.Request(
            source_url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        last_err = None
        for _ in range(3):
            try:
                urllib.request.urlopen(req, timeout=PUBLISH_TIMEOUT).read()
                last_err = None
                break
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
                last_err = e
                time.sleep(0.5)
        assert last_err is None, f"Failed to publish seed event #{i}: {last_err}"

    # Wait for ingestion to settle.
    deadline = time.time() + INGESTION_TIMEOUT_SEC
    final_count = 0
    while time.time() < deadline:
        final_count = _count_events_for_connection(api_key, connection_id)
        if final_count >= SEED_TARGET:
            break
        time.sleep(5)

    assert final_count >= SEED_TARGET, (
        f"Only {final_count} events ingested for connection {connection_id}; "
        f"expected >= {SEED_TARGET}."
    )

    # Persist TARGET_CONNECTION_ID so the executor can pick it up.
    bashrc = "/home/user/.bashrc"
    os.makedirs(os.path.dirname(bashrc), exist_ok=True)
    with open(bashrc, "a") as f:
        f.write(f'\nexport TARGET_CONNECTION_ID="{connection_id}"\n')

    try:
        with open("/etc/environment", "a") as f:
            f.write(f'TARGET_CONNECTION_ID="{connection_id}"\n')
    except PermissionError:
        pass

    with open(os.path.join(PROJECT_DIR, ".target_connection_id"), "w") as f:
        f.write(connection_id)

    os.environ["TARGET_CONNECTION_ID"] = connection_id
