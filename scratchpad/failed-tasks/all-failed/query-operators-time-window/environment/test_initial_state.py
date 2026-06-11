import json
import os
import shutil
import subprocess

import pytest

WORKSPACE = "/workspace"
SEED_PATH = os.path.join(WORKSPACE, "seed.json")
SEED_SCRIPT = "/opt/hookdeck-seed/seed.py"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "Hookdeck CLI binary not found in PATH; expected `hookdeck` to be installed."
    )


def test_python_requests_available():
    try:
        import requests  # noqa: F401
    except ImportError as exc:  # pragma: no cover
        pytest.fail(f"The `requests` package is required but is not importable: {exc}")


def test_workspace_dir_exists():
    assert os.path.isdir(WORKSPACE), f"Workspace directory {WORKSPACE} does not exist."


def test_hookdeck_api_key_env_present():
    value = os.environ.get("HOOKDECK_API_KEY", "")
    assert value, "HOOKDECK_API_KEY environment variable must be set for the task."


def test_run_id_env_present():
    value = os.environ.get("ZEALT_RUN_ID", "").strip()
    assert value, "ZEALT_RUN_ID environment variable must be set for parallel-safe seeding."


def test_seed_script_exists():
    assert os.path.isfile(SEED_SCRIPT), (
        f"Seed script {SEED_SCRIPT} not found; it is required to populate Hookdeck with events."
    )


def test_seed_was_executed():
    """Run the seed script (idempotent) and verify the seed artifact was produced."""
    if not os.path.exists(SEED_PATH):
        result = subprocess.run(
            ["python3", SEED_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert result.returncode == 0, (
            f"Seed script failed (exit {result.returncode}).\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    assert os.path.isfile(SEED_PATH), (
        f"Seed file {SEED_PATH} was not produced by the seed step."
    )


def test_seed_file_schema():
    assert os.path.isfile(SEED_PATH), f"Seed file {SEED_PATH} missing."
    with open(SEED_PATH) as fh:
        seed = json.load(fh)
    for key in ("source_id", "source_name", "window_start", "window_end", "expected_ids"):
        assert key in seed, f"Seed file missing required key '{key}'."
    assert isinstance(seed["source_id"], str) and seed["source_id"].startswith("src_"), (
        "seed.source_id must be a Hookdeck source ID string starting with 'src_'."
    )
    assert isinstance(seed["window_start"], str) and seed["window_start"].endswith("Z"), (
        "seed.window_start must be an ISO-8601 UTC timestamp ending with 'Z'."
    )
    assert isinstance(seed["window_end"], str) and seed["window_end"].endswith("Z"), (
        "seed.window_end must be an ISO-8601 UTC timestamp ending with 'Z'."
    )
    assert isinstance(seed["expected_ids"], list) and len(seed["expected_ids"]) >= 1, (
        "seed.expected_ids must be a non-empty list of event IDs."
    )
    for eid in seed["expected_ids"]:
        assert isinstance(eid, str) and eid.startswith("evt_"), (
            f"seed.expected_ids contains an entry that is not a valid event id: {eid!r}"
        )
