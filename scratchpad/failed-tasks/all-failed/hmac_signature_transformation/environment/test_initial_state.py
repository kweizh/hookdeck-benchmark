import os
import shutil
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"

def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_env_vars_injected():
    assert "HOOKDECK_API_KEY" in os.environ, "HOOKDECK_API_KEY environment variable is missing."
    assert "ZEALT_RUN_ID" in os.environ, "ZEALT_RUN_ID environment variable is missing."
    assert "HMAC_SECRET" in os.environ, "HMAC_SECRET environment variable is missing."
