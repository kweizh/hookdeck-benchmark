import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/project"
LOG_FILE = os.path.join(PROJECT_DIR, "source.log")

def test_source_log_exists():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

def test_source_log_contains_source_id():
    with open(LOG_FILE, "r") as f:
        content = f.read()
    assert re.search(r"Source ID: src_[a-zA-Z0-9]+", content), "Log file does not contain a valid Source ID starting with 'src_'."

def test_hookdeck_source_configuration():
    # Extract source ID from log file
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Source ID:\s*(src_[a-zA-Z0-9]+)", content)
    assert match, "Could not extract Source ID from log file."
    source_id = match.group(1)

    # Get run-id
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    # Get API key
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    # Call Hookdeck API
    url = f"https://api.hookdeck.com/2025-07-01/sources/{source_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch source from Hookdeck API. Status: {response.status_code}, Response: {response.text}"

    data = response.json()
    
    expected_name = f"fireblocks-source-{run_id}"
    assert data.get("name") == expected_name, f"Expected source name '{expected_name}', got '{data.get('name')}'"
    assert data.get("type") == "FIREBLOCKS", f"Expected source type 'FIREBLOCKS', got '{data.get('type')}'"
    
    config = data.get("config", {})
    auth = config.get("auth", {})
    assert auth.get("environment") == "sandbox", f"Expected config.auth.environment to be 'sandbox', got '{auth.get('environment')}'"
