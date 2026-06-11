import os
import shutil


PROJECT_DIR = "/home/user/hookdeck-dedup"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "The hookdeck CLI must be installed and available in PATH "
        "for the executor to authenticate and manage Hookdeck resources."
    )


def test_curl_available():
    assert shutil.which("curl") is not None, (
        "curl must be available so the executor can call the Hookdeck REST API "
        "and the Hookdeck Publish API."
    )


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Expected the working project directory {PROJECT_DIR} to exist before the task starts."
    )


def test_hookdeck_api_key_env_var_present():
    assert os.environ.get("HOOKDECK_API_KEY"), (
        "HOOKDECK_API_KEY must be present in the environment so the executor can "
        "authenticate to Hookdeck."
    )


def test_zealt_run_id_env_var_present():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, (
        "ZEALT_RUN_ID must be set so the executor can build unique, "
        "concurrency-safe Hookdeck resource names."
    )
