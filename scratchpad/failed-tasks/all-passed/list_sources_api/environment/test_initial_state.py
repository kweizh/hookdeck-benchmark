import os
import shutil

PROJECT_DIR = "/home/user/hookdeck-task"

def test_curl_binary_available():
    assert shutil.which("curl") is not None, "curl binary not found in PATH."

def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, "hookdeck binary not found in PATH."

def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hookdeck_api_key_available():
    assert "HOOKDECK_API_KEY" in os.environ, "HOOKDECK_API_KEY environment variable is not set."
