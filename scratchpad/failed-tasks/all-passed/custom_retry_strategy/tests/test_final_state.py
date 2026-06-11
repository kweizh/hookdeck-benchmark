import os
import re
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def test_log_file_and_connection():
    run_id = os.environ.get("ZEALT_RUN_ID", "")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

    with open(LOG_FILE, "r") as f:
        content = f.read()

    match = re.search(r"Connection ID:\s*([a-zA-Z0-9_]+)", content)
    assert match is not None, f"Could not find 'Connection ID: <connection_id>' in {LOG_FILE}. Content: {content}"

    connection_id = match.group(1)

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch connection {connection_id}. Status: {response.status_code}, Body: {response.text}"

    data = response.json()
    expected_name = f"custom-retry-conn-{run_id}"
    assert data.get("name") == expected_name, f"Expected connection name '{expected_name}', got '{data.get('name')}'"

    rules = data.get("rules", [])
    retry_rule = next((r for r in rules if r.get("type") == "retry"), None)
    assert retry_rule is not None, f"No retry rule found in connection rules: {rules}"

    assert retry_rule.get("count") == 5, f"Expected retry count 5, got {retry_rule.get('count')}"
    assert retry_rule.get("strategy") == "linear", f"Expected retry strategy 'linear', got '{retry_rule.get('strategy')}'"
    assert retry_rule.get("interval") == 60000, f"Expected retry interval 60000, got {retry_rule.get('interval')}"

    status_codes = retry_rule.get("response_status_codes", [])
    
    # Check if 500-599 is present in the status codes
    # Depending on how it's sent, it might be exactly "500-599" or ">=500-599"
    found_5xx = any("500" in str(code) for code in status_codes)
    assert found_5xx, f"Expected response_status_codes to include 5xx errors, got {status_codes}"
