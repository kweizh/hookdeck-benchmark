import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is not set."
    return run_id

def test_output_log_exists_and_contains_connection_id():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Connection ID:\s*(web_[a-zA-Z0-9_]+)", content)
    assert match is not None, "Could not find 'Connection ID: web_...' in output.log"

def test_connection_configuration_via_api():
    run_id = get_run_id()
    
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Connection ID:\s*(web_[a-zA-Z0-9_]+)", content)
    assert match is not None, "Could not find 'Connection ID: web_...' in output.log"
    connection_id = match.group(1)
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is not set."
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    response = requests.get(url, headers=headers)
    
    assert response.status_code == 200, f"Failed to get connection {connection_id}. Status: {response.status_code}, Response: {response.text}"
    
    data = response.json()
    
    assert data.get("name") == f"conn-{run_id}", f"Expected connection name 'conn-{run_id}', got '{data.get('name')}'"
    
    rules = data.get("rules", [])
    dedup_rule = next((r for r in rules if r.get("type") == "deduplicate"), None)
    assert dedup_rule is not None, "No deduplicate rule found in the connection."
    
    assert dedup_rule.get("window") == 600, f"Expected deduplicate window 600, got {dedup_rule.get('window')}"
    
    include_fields = dedup_rule.get("include_fields", [])
    assert "id" in include_fields, f"Expected 'id' in include_fields, got {include_fields}"
    
    source = data.get("source", {})
    assert source.get("name") == f"source-{run_id}", f"Expected source name 'source-{run_id}', got '{source.get('name')}'"
    assert source.get("type") == "WEBHOOK", f"Expected source type 'WEBHOOK', got '{source.get('type')}'"
    
    destination = data.get("destination", {})
    assert destination.get("name") == f"mock-api-{run_id}", f"Expected destination name 'mock-api-{run_id}', got '{destination.get('name')}'"
    assert destination.get("type") == "MOCK_API", f"Expected destination type 'MOCK_API', got '{destination.get('type')}'"
