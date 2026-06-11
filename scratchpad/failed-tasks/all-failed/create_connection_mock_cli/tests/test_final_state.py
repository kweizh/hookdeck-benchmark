import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def test_log_file_exists_and_contains_connection_id():
    """Verify that the log file exists and contains the connection ID."""
    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Connection ID:\s*([a-zA-Z0-9_]+)", content)
    assert match is not None, f"Could not find 'Connection ID: <id>' in log file. Content: {content}"

def test_connection_details_via_api():
    """Verify the connection details using the Hookdeck API."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is missing."
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is missing."
    
    # Extract connection ID from log file
    with open(LOG_FILE, "r") as f:
        content = f.read()
    match = re.search(r"Connection ID:\s*([a-zA-Z0-9_]+)", content)
    assert match is not None, "Could not extract connection ID from log file."
    connection_id = match.group(1)
    
    # Fetch connection from API
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch connection details. Status: {response.status_code}, Response: {response.text}"
    
    data = response.json()
    
    # Assert connection name
    expected_conn_name = f"mock-conn-{run_id}"
    assert data.get("name") == expected_conn_name, f"Expected connection name '{expected_conn_name}', got '{data.get('name')}'"
    
    # Assert source name
    source = data.get("source", {})
    expected_source_name = f"mock-source-{run_id}"
    assert source.get("name") == expected_source_name, f"Expected source name '{expected_source_name}', got '{source.get('name')}'"
    
    # Assert destination name and type
    destination = data.get("destination", {})
    expected_dest_name = f"mock-dest-{run_id}"
    assert destination.get("name") == expected_dest_name, f"Expected destination name '{expected_dest_name}', got '{destination.get('name')}'"
    
    dest_type = destination.get("type", "").upper()
    assert dest_type == "MOCK", f"Expected destination type 'MOCK', got '{dest_type}'"
