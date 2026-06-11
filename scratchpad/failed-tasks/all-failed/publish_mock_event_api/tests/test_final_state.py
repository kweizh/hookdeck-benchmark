import os
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
API_BASE_URL = "https://api.hookdeck.com/2025-07-01"

@pytest.fixture(scope="session")
def run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id

@pytest.fixture(scope="session")
def api_headers():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return {"Authorization": f"Bearer {api_key}"}

def test_output_log_exists_and_content(run_id):
    log_file = os.path.join(PROJECT_DIR, "output.log")
    assert os.path.isfile(log_file), f"Log file {log_file} does not exist."
    
    with open(log_file, "r") as f:
        content = f.read()
    
    expected_line = f"Source Name: mock-source-{run_id}"
    assert expected_line in content, f"Expected '{expected_line}' in {log_file}, but it was not found."

def test_source_exists(run_id, api_headers):
    source_name = f"mock-source-{run_id}"
    
    response = requests.get(f"{API_BASE_URL}/sources", headers=api_headers)
    assert response.status_code == 200, f"Failed to get sources: {response.text}"
    
    sources = response.json().get("models", [])
    source_names = [s.get("name") for s in sources]
    
    assert source_name in source_names, f"Source '{source_name}' not found. Available sources: {source_names}"

def test_destination_exists(run_id, api_headers):
    dest_name = f"mock-dest-{run_id}"
    
    response = requests.get(f"{API_BASE_URL}/destinations", headers=api_headers)
    assert response.status_code == 200, f"Failed to get destinations: {response.text}"
    
    dests = response.json().get("models", [])
    found_dest = next((d for d in dests if d.get("name") == dest_name), None)
    
    assert found_dest is not None, f"Destination '{dest_name}' not found."
    assert found_dest.get("type") == "MOCK_API", f"Expected destination type to be 'MOCK_API', got '{found_dest.get('type')}'"

def test_event_published(run_id, api_headers):
    source_name = f"mock-source-{run_id}"
    
    # First, get the source ID since events are associated with source IDs
    sources_response = requests.get(f"{API_BASE_URL}/sources", headers=api_headers)
    assert sources_response.status_code == 200, f"Failed to get sources: {sources_response.text}"
    
    source = next((s for s in sources_response.json().get("models", []) if s.get("name") == source_name), None)
    assert source is not None, f"Source '{source_name}' not found."
    source_id = source.get("id")
    
    # Then query events for this source
    events_response = requests.get(f"{API_BASE_URL}/events?source_id={source_id}", headers=api_headers)
    assert events_response.status_code == 200, f"Failed to get events: {events_response.text}"
    
    events = events_response.json().get("models", [])
    
    # Check if any event has the expected payload
    event_found = False
    for event in events:
        event_data = event.get("data", {}).get("body", {})
        if isinstance(event_data, dict):
            body = event_data.get("body", {})
            if isinstance(body, dict):
                if body.get("data", {}).get("run_id") == run_id:
                    event_found = True
                    break
            elif isinstance(event_data, dict) and event_data.get("data", {}).get("run_id") == run_id:
                # Sometimes the structure might be flat depending on transformation
                event_found = True
                break

    assert event_found, f"No event found with 'run_id': '{run_id}' for source '{source_name}'."
