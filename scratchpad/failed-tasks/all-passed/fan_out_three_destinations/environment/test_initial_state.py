import os
import shutil
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"

def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI binary not found in PATH."

def test_project_directory_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."
