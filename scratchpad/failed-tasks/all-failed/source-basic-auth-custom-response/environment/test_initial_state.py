import os
import shutil

PROJECT_DIR = "/home/user/hookdeck-project"


def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, (
        "hookdeck CLI not found in PATH; the task environment must ship the Hookdeck CLI."
    )


def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), (
        f"Project directory {PROJECT_DIR} does not exist in the initial environment."
    )


def test_requests_importable():
    import requests  # noqa: F401

    assert requests is not None, "Python `requests` library is required for live HTTP probes."
