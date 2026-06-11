import os
import re
import requests
import pytest

LOG_FILE = "/home/user/hookdeck-task/output.log"

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id

def get_api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return api_key

def test_log_file_exists():
    """Verify that the output log file exists."""
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

def test_event_published():
    """Verify that the event was successfully published and retrieved via API."""
    run_id = get_run_id()
    api_key = get_api_key()
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        
    match = re.search(r"Event ID:\s*([a-zA-Z0-9_]+)", content)
    assert match, f"Could not find 'Event ID: <event_id>' in {LOG_FILE}. Content: {content}"
    
    event_id = match.group(1)
    
    # Check event
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/events/{event_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 200, f"Failed to retrieve event {event_id}. Status: {response.status_code}, Body: {response.text}"
    
    event_data = response.json()
    source_id = event_data.get("source_id")
    assert source_id, f"Event {event_id} does not have a source_id."
    
    # Check source name
    source_response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/sources/{source_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert source_response.status_code == 200, f"Failed to retrieve source {source_id}."
    source_data = source_response.json()
    
    expected_source_name = f"mock-source-{run_id}"
    actual_source_name = source_data.get("name")
    assert actual_source_name == expected_source_name, f"Expected source name {expected_source_name}, got {actual_source_name}"

def test_connection_exists():
    """Verify that the connection to the mock destination was created."""
    run_id = get_run_id()
    api_key = get_api_key()
    
    response = requests.get(
        "https://api.hookdeck.com/2025-07-01/connections",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 200, f"Failed to list connections. Status: {response.status_code}"
    
    # The Hookdeck API returns a paginated response with a "models" array
    data = response.json()
    connections = data.get("models", [])
    connection_names = [conn.get("name") for conn in connections]
    
    expected_name = f"mock-conn-{run_id}"
    assert expected_name in connection_names, f"Expected connection {expected_name} in connections, got {connection_names}"
