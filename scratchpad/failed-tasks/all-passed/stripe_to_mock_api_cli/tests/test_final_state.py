import os
import re
import requests
import pytest

LOG_FILE = "/home/user/hookdeck-task/output.log"

def test_output_log_exists():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

def test_connection_created_via_api():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    with open(LOG_FILE, "r") as f:
        content = f.read()

    # The ID prefix for connections is usually 'web_' or similar, but we can match any typical ID
    match = re.search(r"Connection ID:\s*([a-zA-Z0-9_]+)", content)
    assert match is not None, f"Could not find 'Connection ID: <id>' in {LOG_FILE}. Content: {content}"
    
    connection_id = match.group(1)

    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Failed to retrieve connection {connection_id} via API. Status: {response.status_code}, Body: {response.text}"
    
    conn_data = response.json()
    
    expected_name = f"stripe-to-mock-{run_id}"
    assert conn_data.get("name") == expected_name, f"Expected connection name '{expected_name}', got '{conn_data.get('name')}'"
    
    source = conn_data.get("source", {})
    expected_source_name = f"stripe-{run_id}"
    assert source.get("name") == expected_source_name, f"Expected source name '{expected_source_name}', got '{source.get('name')}'"
    assert source.get("type") == "STRIPE", f"Expected source type 'STRIPE', got '{source.get('type')}'"
    
    destination = conn_data.get("destination", {})
    expected_dest_name = f"mock-api-{run_id}"
    assert destination.get("name") == expected_dest_name, f"Expected destination name '{expected_dest_name}', got '{destination.get('name')}'"
    assert destination.get("type") == "MOCK_API", f"Expected destination type 'MOCK_API', got '{destination.get('type')}'"
