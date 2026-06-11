import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

@pytest.fixture
def run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id

@pytest.fixture
def api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return api_key

@pytest.fixture
def event_id():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Event ID:\s*(\S+)", content)
    assert match is not None, f"Could not find 'Event ID: <event_id>' in {LOG_FILE}."
    return match.group(1)

def test_event_is_successful(event_id, api_key):
    url = f"https://api.hookdeck.com/2025-07-01/events/{event_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Failed to fetch event {event_id}. Status: {response.status_code}, Response: {response.text}"
    
    event_data = response.json()
    assert event_data.get("status") == "SUCCESSFUL", f"Expected event status to be SUCCESSFUL, got: {event_data.get('status')}"

def test_source_exists(run_id, api_key):
    url = "https://api.hookdeck.com/2025-07-01/sources"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Failed to fetch sources. Status: {response.status_code}, Response: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    source_names = [model.get("name") for model in models]
    expected_source_name = f"test-source-{run_id}"
    
    assert expected_source_name in source_names, f"Expected source '{expected_source_name}' not found in sources: {source_names}"

def test_destination_exists(run_id, api_key):
    url = "https://api.hookdeck.com/2025-07-01/destinations"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Failed to fetch destinations. Status: {response.status_code}, Response: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    destination_names = [model.get("name") for model in models]
    expected_destination_name = f"mock-dest-{run_id}"
    
    assert expected_destination_name in destination_names, f"Expected destination '{expected_destination_name}' not found in destinations: {destination_names}"
