import os
import shutil

PROJECT_DIR = "/home/user/myproject"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck CLI binary not found in PATH; the Hookdeck CLI must be pre-installed."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected project directory {PROJECT_DIR} to exist before evaluation."
    )


def test_hookdeck_api_key_env_present():
    assert os.environ.get("HOOKDECK_API_KEY"), (
        "HOOKDECK_API_KEY must be set in the environment so the executor can call the Hookdeck API."
    )


def test_zealt_run_id_env_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID must be set so resources can be namespaced for parallel-run safety."
