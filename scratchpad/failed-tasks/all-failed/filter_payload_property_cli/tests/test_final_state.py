import os
import subprocess
import json
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"

def test_connection_created_and_configured():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    connection_id = None
    for line in content.splitlines():
        if line.startswith("Connection ID: "):
            connection_id = line.split("Connection ID: ")[1].strip()
            break
            
    assert connection_id, "Could not extract Connection ID from output.log"
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    
    # Authenticate
    auth_result = subprocess.run(
        ["hookdeck", "ci", "--api-key", api_key],
        capture_output=True, text=True
    )
    assert auth_result.returncode == 0, f"'hookdeck ci' failed: {auth_result.stderr}"
    
    # Get connection details
    result = subprocess.run(
        ["hookdeck", "gateway", "connection", "get", connection_id, "--output", "json"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"'hookdeck gateway connection get' failed: {result.stderr}"
    
    try:
        connection_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output: {result.stdout}")
        
    expected_conn_name = f"order-filter-{run_id}"
    expected_src_name = f"stripe-source-{run_id}"
    expected_dest_name = f"mock-dest-{run_id}"
    
    assert connection_data.get("name") == expected_conn_name, \
        f"Expected connection name {expected_conn_name}, got {connection_data.get('name')}"
        
    source = connection_data.get("source", {})
    assert source.get("name") == expected_src_name, \
        f"Expected source name {expected_src_name}, got {source.get('name')}"
    assert source.get("type") == "WEBHOOK", \
        f"Expected source type WEBHOOK, got {source.get('type')}"
        
    destination = connection_data.get("destination", {})
    assert destination.get("name") == expected_dest_name, \
        f"Expected destination name {expected_dest_name}, got {destination.get('name')}"
    assert destination.get("type") == "MOCK", \
        f"Expected destination type MOCK, got {destination.get('type')}"
        
    rules = connection_data.get("rules", [])
    filter_rule_found = False
    for rule in rules:
        if rule.get("type") == "filter":
            body_filter = rule.get("body", {})
            if body_filter.get("type") == "order.created":
                filter_rule_found = True
                break
                
    assert filter_rule_found, "Could not find a filter rule where body.type is 'order.created'"
