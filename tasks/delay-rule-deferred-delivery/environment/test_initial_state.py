import os
import shutil

PROJECT_DIR = "/home/user/hookdeck-task"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck CLI not found in PATH; the Hookdeck CLI must be pre-installed."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hookdeck_api_key_present():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, (
        "HOOKDECK_API_KEY environment variable must be set in the task environment."
    )


def test_zealt_run_id_present():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, (
        "ZEALT_RUN_ID environment variable must be set so resources can be isolated per trial."
    )


def test_log_file_does_not_exist_yet():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Log file {log_path} must not exist before the task starts; the executor must create it."
    )
