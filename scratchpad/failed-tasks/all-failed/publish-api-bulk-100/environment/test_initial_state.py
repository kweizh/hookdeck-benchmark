import os
import shutil

PROJECT_DIR = "/home/user/hookdeck-task"


def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, "hookdeck binary not found in PATH."


def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."


def test_environment_variables_set():
    assert "ZEALT_RUN_ID" in os.environ, "ZEALT_RUN_ID environment variable is not set."
    assert "HOOKDECK_API_KEY" in os.environ, "HOOKDECK_API_KEY environment variable is not set."
