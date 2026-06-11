import os
import shutil
import subprocess


PROJECT_DIR = "/home/user/hookdeck-task"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI not found in PATH."


def test_curl_available():
    assert shutil.which("curl") is not None, "curl not found in PATH."


def test_hookdeck_api_key_env():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."


def test_zealt_run_id_env():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_hookdeck_cli_version_runs():
    result = subprocess.run(
        ["hookdeck", "version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"`hookdeck version` failed (exit {result.returncode}): "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
