import os
import shutil

def test_curl_available():
    assert shutil.which("curl") is not None, "curl is not available in PATH"

def test_project_dir_exists():
    assert os.path.isdir("/home/user/hookdeck-task"), "Project directory /home/user/hookdeck-task does not exist"
