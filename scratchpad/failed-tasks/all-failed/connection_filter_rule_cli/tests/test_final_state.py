import os
import requests
import pytest
import json

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

def test_connection_created_and_configured():
    run_id = os.environ.get("ZEALT_RUN_ID", "default-run-id")
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing."

    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    connection_id = None
    for line in content.splitlines():
        if line.startswith("Connection ID:"):
            connection_id = line.split("Connection ID:")[1].strip()
            break
            
    assert connection_id, "Connection ID not found in the log file. Expected format: 'Connection ID: <connection_id>'"

    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 200, f"Failed to fetch connection details: {response.text}"
    
    data = response.json()
    
    expected_name = f"filtered-conn-{run_id}"
    assert data.get("name") == expected_name, f"Expected connection name '{expected_name}', got '{data.get('name')}'"
    
    source = data.get("source", {})
    assert source.get("type") == "WEBHOOK", f"Expected source type 'WEBHOOK', got '{source.get('type')}'"
    
    destination = data.get("destination", {})
    assert destination.get("type") == "MOCK_API", f"Expected destination type 'MOCK_API', got '{destination.get('type')}'"
    
    rules = data.get("rules", [])
    has_filter = False
    for rule in rules:
        rule_str = json.dumps(rule)
        if "body.amount" in rule_str and "100" in rule_str:
            has_filter = True
            break
            
    assert has_filter, f"Could not find a rule that filters by body.amount > 100 in connection rules: {rules}"
