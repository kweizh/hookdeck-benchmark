import os
import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
SOURCE_ID_FILE = os.path.join(PROJECT_DIR, "source_id.txt")
CONNECTION_ID_FILE = os.path.join(PROJECT_DIR, "connection_id.txt")

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is not set."
    return run_id

def get_api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is not set."
    return api_key

def get_source_id():
    assert os.path.isfile(SOURCE_ID_FILE), f"Source ID file {SOURCE_ID_FILE} does not exist."
    with open(SOURCE_ID_FILE, "r") as f:
        source_id = f.read().strip()
    assert source_id, f"Source ID file {SOURCE_ID_FILE} is empty."
    return source_id

def get_connection_id():
    assert os.path.isfile(CONNECTION_ID_FILE), f"Connection ID file {CONNECTION_ID_FILE} does not exist."
    with open(CONNECTION_ID_FILE, "r") as f:
        connection_id = f.read().strip()
    assert connection_id, f"Connection ID file {CONNECTION_ID_FILE} is empty."
    return connection_id

def test_source_configuration():
    run_id = get_run_id()
    api_key = get_api_key()
    source_id = get_source_id()
    
    url = f"https://api.hookdeck.com/2025-07-01/sources/{source_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch source: {response.text}"
    
    data = response.json()
    expected_name = f"custom-methods-source-{run_id}"
    assert data.get("name") == expected_name, f"Expected source name '{expected_name}', got '{data.get('name')}'"
    
    config = data.get("config", {})
    allowed_methods = config.get("allowed_http_methods", [])
    assert sorted(allowed_methods) == ["PATCH", "PUT"], f"Expected allowed_http_methods to be ['PATCH', 'PUT'], got {allowed_methods}"

def test_connection_configuration():
    run_id = get_run_id()
    api_key = get_api_key()
    source_id = get_source_id()
    connection_id = get_connection_id()
    
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch connection: {response.text}"
    
    data = response.json()
    
    actual_source_id = data.get("source", {}).get("id")
    assert actual_source_id == source_id, f"Expected connection source id '{source_id}', got '{actual_source_id}'"
    
    expected_dest_name = f"mock-dest-{run_id}"
    actual_dest_name = data.get("destination", {}).get("name")
    assert actual_dest_name == expected_dest_name, f"Expected destination name '{expected_dest_name}', got '{actual_dest_name}'"
