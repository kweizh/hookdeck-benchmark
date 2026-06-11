import os
import shutil


PROJECT_DIR = "/home/user/hookdeck-task"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck CLI binary not found in PATH; the Hookdeck CLI must be "
        "preinstalled in the task environment."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist; it must be "
        "preprovisioned for the task."
    )


def test_hookdeck_api_key_env_var_set():
    assert os.environ.get("HOOKDECK_API_KEY"), (
        "HOOKDECK_API_KEY environment variable is not set; the executor needs "
        "it to authenticate against the Hookdeck API."
    )


def test_zealt_run_id_env_var_set():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, (
        "ZEALT_RUN_ID environment variable is not set; resource names must be "
        "suffixed with this value to keep parallel runs isolated."
    )


def test_output_log_not_yet_created():
    log_path = os.path.join(PROJECT_DIR, "output.log")
    assert not os.path.exists(log_path), (
        f"Log file {log_path} already exists before the task starts; "
        "the executor is expected to create it."
    )
