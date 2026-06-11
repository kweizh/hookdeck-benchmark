import os
import re
import time
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

@pytest.fixture(scope="session")
def run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is not set."
    return run_id

@pytest.fixture(scope="session")
def api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is not set."
    return api_key

@pytest.fixture(scope="session")
def api_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}

@pytest.fixture(scope="session")
def source_url():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Source URL:\s*(https?://[^\s]+)", content)
    assert match is not None, f"Could not find 'Source URL: <url>' in {LOG_FILE}"
    return match.group(1)

def test_source_exists(run_id, api_headers):
    source_name = f"fan-out-source-{run_id}"
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/sources?name={source_name}",
        headers=api_headers
    )
    assert response.status_code == 200, f"Failed to get sources: {response.text}"
    data = response.json()
    assert data.get("count", 0) > 0, f"Source '{source_name}' not found."
    models = data.get("models", [])
    assert len(models) > 0, f"Source '{source_name}' not found in models."

def test_destinations_exist(run_id, api_headers):
    dest_names = [f"mock-dest-1-{run_id}", f"mock-dest-2-{run_id}"]
    for dest_name in dest_names:
        response = requests.get(
            f"https://api.hookdeck.com/2025-07-01/destinations?name={dest_name}",
            headers=api_headers
        )
        assert response.status_code == 200, f"Failed to get destinations: {response.text}"
        data = response.json()
        assert data.get("count", 0) > 0, f"Destination '{dest_name}' not found."
        
def test_connections_exist(run_id, api_headers):
    # Get source ID
    source_name = f"fan-out-source-{run_id}"
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/sources?name={source_name}",
        headers=api_headers
    )
    assert response.status_code == 200, f"Failed to get source: {response.text}"
    source_models = response.json().get("models", [])
    assert len(source_models) > 0, f"Source '{source_name}' not found."
    source_id = source_models[0]["id"]
    
    # Get destination IDs
    dest_ids = []
    dest_names = [f"mock-dest-1-{run_id}", f"mock-dest-2-{run_id}"]
    for dest_name in dest_names:
        response = requests.get(
            f"https://api.hookdeck.com/2025-07-01/destinations?name={dest_name}",
            headers=api_headers
        )
        assert response.status_code == 200, f"Failed to get destination: {response.text}"
        dest_models = response.json().get("models", [])
        assert len(dest_models) > 0, f"Destination '{dest_name}' not found."
        dest_ids.append(dest_models[0]["id"])
    
    # Check connections
    for dest_id in dest_ids:
        response = requests.get(
            f"https://api.hookdeck.com/2025-07-01/connections?source_id={source_id}&destination_id={dest_id}",
            headers=api_headers
        )
        assert response.status_code == 200, f"Failed to get connections: {response.text}"
        conn_data = response.json()
        assert conn_data.get("count", 0) > 0, f"Connection from source '{source_id}' to destination '{dest_id}' not found."

def test_event_delivery(run_id, api_headers, source_url):
    # Publish event
    publish_res = requests.post(
        source_url,
        json={"test": "fan-out"}
    )
    assert publish_res.status_code in (200, 201, 202), f"Failed to publish event: {publish_res.text}"
    
    # Give Hookdeck a moment to process the event
    time.sleep(5)
    
    # Get source ID
    source_name = f"fan-out-source-{run_id}"
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/sources?name={source_name}",
        headers=api_headers
    )
    assert response.status_code == 200, f"Failed to get source: {response.text}"
    source_id = response.json()["models"][0]["id"]
    
    # Get destination IDs
    dest_ids = []
    dest_names = [f"mock-dest-1-{run_id}", f"mock-dest-2-{run_id}"]
    for dest_name in dest_names:
        response = requests.get(
            f"https://api.hookdeck.com/2025-07-01/destinations?name={dest_name}",
            headers=api_headers
        )
        assert response.status_code == 200, f"Failed to get destination: {response.text}"
        dest_ids.append(response.json()["models"][0]["id"])
        
    # Check events
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/events?source_id={source_id}",
        headers=api_headers
    )
    assert response.status_code == 200, f"Failed to get events: {response.text}"
    events = response.json().get("models", [])
    
    for dest_id in dest_ids:
        found_successful_event = False
        for event in events:
            if event.get("destination_id") == dest_id and event.get("status") == "SUCCESSFUL":
                found_successful_event = True
                break
        assert found_successful_event, f"No successful event found for destination '{dest_id}'."
