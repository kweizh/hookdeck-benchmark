import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-project"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id

def get_api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return api_key

def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

def test_connection_created_correctly():
    assert os.path.isfile(LOG_FILE), "Cannot verify connection without log file."
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        
    conn_match = re.search(r"Connection ID:\s*([a-zA-Z0-9_-]+)", content)
    assert conn_match, "Connection ID not found in the log file in the expected format."
    connection_id = conn_match.group(1)
    
    run_id = get_run_id()
    api_key = get_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}", headers=headers)
    assert response.status_code == 200, f"Failed to fetch connection details: {response.text}"
    
    data = response.json()
    assert data.get("name") == f"conn-{run_id}", f"Expected connection name 'conn-{run_id}', got {data.get('name')}"
    
    source = data.get("source", {})
    assert source.get("name") == f"source-{run_id}", f"Expected source name 'source-{run_id}', got {source.get('name')}"
    
    destination = data.get("destination", {})
    assert destination.get("name") == f"mock-dest-{run_id}", f"Expected destination name 'mock-dest-{run_id}', got {destination.get('name')}"

def test_event_processed_successfully():
    assert os.path.isfile(LOG_FILE), "Cannot verify event without log file."
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        
    event_match = re.search(r"Event ID:\s*([a-zA-Z0-9_-]+)", content)
    assert event_match, "Event ID not found in the log file in the expected format."
    event_id = event_match.group(1)
    
    run_id = get_run_id()
    api_key = get_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(f"https://api.hookdeck.com/2025-07-01/events/{event_id}", headers=headers)
    assert response.status_code == 200, f"Failed to fetch event details: {response.text}"
    
    data = response.json()
    assert data.get("status") == "SUCCESSFUL", f"Expected event status 'SUCCESSFUL', got {data.get('status')}"
    
    body = data.get("body", {})
    assert body.get("test_id") == run_id, f"Expected event body.test_id '{run_id}', got {body.get('test_id')}"
