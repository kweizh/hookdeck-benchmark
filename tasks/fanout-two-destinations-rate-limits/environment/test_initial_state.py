import os
import shutil

import pytest

PROJECT_DIR = "/home/user/hookdeck-fanout"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck CLI binary not found in PATH; the Hookdeck CLI is required "
        "for this task."
    )


def test_curl_available():
    assert shutil.which("curl") is not None, (
        "curl is required for calling the Hookdeck REST and Publish APIs."
    )


def test_python3_available():
    assert shutil.which("python3") is not None, (
        "python3 is required for orchestrating publish calls."
    )


def test_hookdeck_api_key_env_var_set():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, (
        "HOOKDECK_API_KEY environment variable must be set so the task can "
        "call the Hookdeck REST and Publish APIs."
    )


def test_zealt_run_id_env_var_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set so resources can be "
        "named uniquely per run."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Log file {log_path} should not yet exist; the executor must create it."
    )


def test_requests_library_importable():
    pytest.importorskip(
        "requests",
        reason="The verifier and helper scripts rely on the `requests` library.",
    )
