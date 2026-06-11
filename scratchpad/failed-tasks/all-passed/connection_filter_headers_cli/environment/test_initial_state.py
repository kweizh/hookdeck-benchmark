import os
import shutil
import pytest

def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, "hookdeck binary not found in PATH."

def test_project_dir_exists():
    assert os.path.isdir("/home/user/hookdeck-task"), "Project directory /home/user/hookdeck-task does not exist."
