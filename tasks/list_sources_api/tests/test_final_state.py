import os
import requests
import pytest

PROJECT_DIR = "/home/user/myproject"
SOURCES_FILE = os.path.join(PROJECT_DIR, "sources.txt")

def test_sources_file_exists():
    """Verify that the script was executed and generated the required artifact."""
    assert os.path.isfile(SOURCES_FILE), f"Artifact file {SOURCES_FILE} does not exist."

def test_sources_file_content():
    """Verify that the file contains exactly the expected source names."""
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing"

    url = "https://api.hookdeck.com/2025-07-01/sources"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch sources from Hookdeck API: {response.text}"

    data = response.json()
    expected_names = {model["name"] for model in data.get("models", [])}

    with open(SOURCES_FILE, "r") as f:
        content = f.read()

    actual_names = {line.strip() for line in content.splitlines() if line.strip()}

    assert actual_names == expected_names, (
        f"Sources in file do not match expected sources. "
        f"Expected: {expected_names}, Actual: {actual_names}"
    )
