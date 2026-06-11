import os
import shutil

PROJECT_DIR = "/home/user/hookdeck-task"

def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, "hookdeck binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."
