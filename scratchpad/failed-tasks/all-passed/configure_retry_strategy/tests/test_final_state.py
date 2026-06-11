import os
import re
import requests
import pytest

def test_run_id_exists():
    assert "ZEALT_RUN_ID" in os.environ, "ZEALT_RUN_ID environment variable is not set."

def test_output_log_and_connection_id():
    log_path = "/home/user/hookdeck-task/output.log"
    assert os.path.isfile(log_path), f"Log file {log_path} does not exist."
    
    with open(log_path, "r") as f:
        content = f.read()
    
    match = re.search(r"Connection ID:\s*(web_[a-zA-Z0-9_]+)", content)
    assert match is not None, "Could not find 'Connection ID: web_...' in output.log."
    
def test_connection_configuration_via_api():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID is required for this test."
    
    log_path = "/home/user/hookdeck-task/output.log"
    with open(log_path, "r") as f:
        content = f.read()
    match = re.search(r"Connection ID:\s*(web_[a-zA-Z0-9_]+)", content)
    assert match is not None, "Connection ID missing."
    connection_id = match.group(1)
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch connection {connection_id}. Status: {response.status_code}, Body: {response.text}"
    
    data = response.json()
    
    assert data.get("name") == f"retry-test-{run_id}", f"Expected connection name 'retry-test-{run_id}', got '{data.get('name')}'"
    
    source = data.get("source", {})
    assert source.get("name") == f"src-{run_id}", f"Expected source name 'src-{run_id}', got '{source.get('name')}'"
    assert source.get("type") == "WEBHOOK", f"Expected source type 'WEBHOOK', got '{source.get('type')}'"
    
    destination = data.get("destination", {})
    assert destination.get("name") == f"dest-{run_id}", f"Expected destination name 'dest-{run_id}', got '{destination.get('name')}'"
    assert destination.get("type") == "MOCK_API", f"Expected destination type 'MOCK_API', got '{destination.get('type')}'"
    
    rules = data.get("rules", [])
    retry_rules = [r for r in rules if r.get("type") == "retry"]
    assert len(retry_rules) == 1, f"Expected exactly one retry rule, found {len(retry_rules)}"
    
    retry_rule = retry_rules[0]
    status_codes = retry_rule.get("response_status_codes", [])
    
    # Check that it covers 5xx
    has_5xx = False
    has_4xx = False
    for code in status_codes:
        code_str = str(code)
        if "500" in code_str or ">=5" in code_str or "5xx" in code_str:
            has_5xx = True
        if "400" in code_str or ">=4" in code_str or "4xx" in code_str:
            has_4xx = True
            
    assert has_5xx, f"Retry rule does not seem to cover 5xx errors. Configured status codes: {status_codes}"
    assert not has_4xx, f"Retry rule should NOT cover 4xx errors. Configured status codes: {status_codes}"
