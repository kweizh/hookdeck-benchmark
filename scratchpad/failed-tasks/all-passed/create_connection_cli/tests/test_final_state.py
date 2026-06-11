import os
import requests
import pytest

LOG_FILE = "/home/user/hookdeck-task/output.log"

def test_log_file_exists_and_contains_connection_name():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    
    expected_name = f"stripe-connection-{run_id}"
    
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        
    expected_line = f"Connection Name: {expected_name}"
    assert expected_line in content, f"Expected log file to contain '{expected_line}', got: {content}"

def test_connection_created_in_hookdeck():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    
    api_key = os.environ.get("HOOKDECK_API_KEY", "")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    
    expected_name = f"stripe-connection-{run_id}"
    
    url = "https://api.hookdeck.com/2025-07-01/connections"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to list connections. Status code: {response.status_code}, Response: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    
    # Find the connection by name
    target_connection = next((conn for conn in models if conn.get("name") == expected_name), None)
    
    assert target_connection is not None, f"Connection '{expected_name}' not found in Hookdeck workspace."
    
    # Verify source type
    source_type = target_connection.get("source", {}).get("type")
    assert source_type == "STRIPE", f"Expected source type to be 'STRIPE', got: {source_type}"
    
    # Verify destination type
    destination_type = target_connection.get("destination", {}).get("type")
    assert destination_type == "MOCK_API", f"Expected destination type to be 'MOCK_API', got: {destination_type}"
