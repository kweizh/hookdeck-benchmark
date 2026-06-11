import os
import shutil
import subprocess
import sys

import pytest
import requests

PROJECT_DIR = "/workspace"
SEEDED_ENV_FILE = "/workspace/.seeded_events.env"
SCRIPT_PATH = "/workspace/await_delivery.py"
SEED_SCRIPT = "/opt/seed_hookdeck_events.py"
HOOKDECK_API_BASE = "https://api.hookdeck.com/2025-07-01"


def _parse_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export ") :]
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            values[key] = val
    return values


@pytest.fixture(scope="session", autouse=True)
def _seed_hookdeck_events():
    """
    Seed the Hookdeck environment with a successful and a failed event.

    The seeding requires HOOKDECK_API_KEY which is only available at container
    runtime, so we run the seeding script here (the initial-state test always
    runs before evaluation, so the resulting state is treated as the starting
    environment for the executor).
    """
    if os.path.isfile(SEEDED_ENV_FILE):
        return
    assert os.path.isfile(SEED_SCRIPT), (
        f"Seeding helper {SEED_SCRIPT} is missing from the image."
    )
    result = subprocess.run(
        [sys.executable, SEED_SCRIPT],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"Hookdeck seeding script failed (exit {result.returncode}). "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


@pytest.fixture(scope="module")
def seeded_env() -> dict[str, str]:
    assert os.path.isfile(SEEDED_ENV_FILE), (
        f"Seeded event ids file {SEEDED_ENV_FILE} does not exist after seeding."
    )
    return _parse_env_file(SEEDED_ENV_FILE)


def test_python3_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_requests_library_importable():
    import importlib

    importlib.import_module("requests")


def test_workspace_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hookdeck_api_key_present():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI not found in PATH."


def test_seeded_env_file_exists():
    assert os.path.isfile(SEEDED_ENV_FILE), (
        f"Seeded event ids file {SEEDED_ENV_FILE} does not exist."
    )


def test_seeded_env_file_defines_successful_event_id(seeded_env: dict[str, str]):
    assert seeded_env.get("SUCCESSFUL_EVENT_ID"), (
        "SUCCESSFUL_EVENT_ID is not defined in /workspace/.seeded_events.env."
    )
    assert seeded_env["SUCCESSFUL_EVENT_ID"].startswith("evt_"), (
        "SUCCESSFUL_EVENT_ID does not look like a Hookdeck event id (expected 'evt_' prefix)."
    )


def test_seeded_env_file_defines_failed_event_id(seeded_env: dict[str, str]):
    assert seeded_env.get("FAILED_EVENT_ID"), (
        "FAILED_EVENT_ID is not defined in /workspace/.seeded_events.env."
    )
    assert seeded_env["FAILED_EVENT_ID"].startswith("evt_"), (
        "FAILED_EVENT_ID does not look like a Hookdeck event id (expected 'evt_' prefix)."
    )


def test_seeded_successful_event_reachable_via_inspect_api(seeded_env: dict[str, str]):
    api_key = os.environ.get("HOOKDECK_API_KEY", "")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    event_id = seeded_env["SUCCESSFUL_EVENT_ID"]
    response = requests.get(
        f"{HOOKDECK_API_BASE}/events/{event_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    assert response.status_code == 200, (
        f"Inspect API did not return the seeded successful event "
        f"{event_id}: HTTP {response.status_code} - {response.text[:200]}"
    )
    payload = response.json()
    assert payload.get("id") == event_id, (
        f"Inspect API returned an event with a different id than seeded: "
        f"{payload.get('id')} != {event_id}"
    )


def test_seeded_failed_event_reachable_via_inspect_api(seeded_env: dict[str, str]):
    api_key = os.environ.get("HOOKDECK_API_KEY", "")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    event_id = seeded_env["FAILED_EVENT_ID"]
    response = requests.get(
        f"{HOOKDECK_API_BASE}/events/{event_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    assert response.status_code == 200, (
        f"Inspect API did not return the seeded failed event "
        f"{event_id}: HTTP {response.status_code} - {response.text[:200]}"
    )
    payload = response.json()
    assert payload.get("id") == event_id, (
        f"Inspect API returned an event with a different id than seeded: "
        f"{payload.get('id')} != {event_id}"
    )


def test_await_delivery_script_not_yet_created():
    assert not os.path.exists(SCRIPT_PATH), (
        f"{SCRIPT_PATH} already exists before the task starts; "
        f"the executor is expected to create it."
    )
