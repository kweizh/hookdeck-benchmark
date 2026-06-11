import os
import shutil

import pytest
import requests

PROJECT_DIR = "/home/user/project"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "Hookdeck CLI binary `hookdeck` not found in PATH."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hookdeck_api_key_env_var_present():
    assert os.environ.get("HOOKDECK_API_KEY"), (
        "HOOKDECK_API_KEY must be set in the environment for the agent to authenticate."
    )


def test_zealt_run_id_env_var_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID must be set in the environment for parallel-safe naming."


def test_hookdeck_api_reachable():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    if not api_key:
        pytest.skip("HOOKDECK_API_KEY not set")
    resp = requests.get(
        "https://api.hookdeck.com/2025-07-01/sources",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"limit": 1},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Hookdeck REST API not reachable or API key invalid. "
        f"Status: {resp.status_code}, body: {resp.text[:500]}"
    )
