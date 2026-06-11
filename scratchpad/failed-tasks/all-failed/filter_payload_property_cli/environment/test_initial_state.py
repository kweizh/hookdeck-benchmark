import os
import shutil

def test_hookdeck_binary_available():
    assert shutil.which("hookdeck") is not None, "hookdeck CLI is not found in PATH."

def test_project_dir_exists():
    project_dir = "/home/user/hookdeck-task"
    assert os.path.isdir(project_dir), f"Project directory {project_dir} does not exist."
