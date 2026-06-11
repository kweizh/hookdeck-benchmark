import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def test_connection_created_and_logged():
    """Verify the connection ID is logged and the connection has the correct configuration via API."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"

    with open(LOG_FILE, "r") as f:
        content = f.read()

    match = re.search(r"Connection ID:\s*([a-zA-Z0-9_]+)", content)
    assert match, f"Could not find 'Connection ID: <id>' in log file. File content: {content}"
    connection_id = match.group(1).strip()

    # Use Hookdeck API to verify
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to retrieve connection {connection_id}. Status: {response.status_code}, Body: {response.text}"
    
    conn_data = response.json()
    
    expected_conn_name = f"shopify-to-http-{run_id}"
    assert conn_data.get("name") == expected_conn_name, f"Expected connection name '{expected_conn_name}', got '{conn_data.get('name')}'"
    
    source = conn_data.get("source", {})
    expected_source_name = f"shopify-source-{run_id}"
    assert source.get("name") == expected_source_name, f"Expected source name '{expected_source_name}', got '{source.get('name')}'"
    assert source.get("type") == "SHOPIFY", f"Expected source type 'SHOPIFY', got '{source.get('type')}'"
    
    destination = conn_data.get("destination", {})
    expected_dest_name = f"http-destination-{run_id}"
    assert destination.get("name") == expected_dest_name, f"Expected destination name '{expected_dest_name}', got '{destination.get('name')}'"
    assert destination.get("type") == "HTTP", f"Expected destination type 'HTTP', got '{destination.get('type')}'"
    
    dest_config = destination.get("config", {})
    expected_url = f"https://mock.hookdeck.com/{run_id}"
    assert dest_config.get("url") == expected_url, f"Expected destination URL '{expected_url}', got '{dest_config.get('url')}'"
