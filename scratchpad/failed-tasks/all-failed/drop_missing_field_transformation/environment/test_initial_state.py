import os
import shutil
import subprocess
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"

def test_hookdeck_cli_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI not found in PATH."

def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hookdeck_login():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is not set."
    
    # Login to Hookdeck CLI
    result = subprocess.run(
        ["hookdeck", "ci", "--api-key", api_key],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Failed to login to Hookdeck CLI: {result.stderr}"
