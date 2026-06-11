import os
import shutil

import pytest

PROJECT_DIR = "/home/user/hookdeck-task"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck CLI binary not found in PATH; cannot interact with Hookdeck."
    )


def test_curl_available():
    assert shutil.which("curl") is not None, (
        "curl binary not found in PATH; needed to call the Hookdeck REST API."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist; the task environment was not"
        " prepared correctly."
    )


def test_hookdeck_api_key_set():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, (
        "HOOKDECK_API_KEY environment variable is not set; the task cannot authenticate"
        " against the Hookdeck API."
    )


def test_zealt_run_id_set():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable is not set; resource names must be suffixed"
        " with run-id to avoid cross-trial collisions."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"{log_path} already exists before the task starts; it must be produced by the"
        " executor."
    )
