import os
import shutil


def test_curl_available():
    assert shutil.which("curl") is not None, "curl binary not found in PATH."


def test_python_available():
    assert shutil.which("python3") is not None, "python3 binary not found in PATH."


def test_requests_module_importable():
    import importlib

    spec = importlib.util.find_spec("requests")
    assert spec is not None, "Python 'requests' package is not installed."


def test_project_dir_exists():
    assert os.path.isdir("/home/user/hookdeck-task"), (
        "Project directory /home/user/hookdeck-task does not exist."
    )
