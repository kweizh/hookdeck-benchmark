import os
import re
import requests
import pytest

def test_connection_created_and_configured():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    log_file = "/home/user/hookdeck-task/output.log"
    assert os.path.isfile(log_file), f"Log file {log_file} does not exist."

    with open(log_file, "r") as f:
        content = f.read()

    match = re.search(r"Connection ID:\s*([^\s]+)", content)
    assert match, "Could not find 'Connection ID: <connection_id>' in the log file."
    connection_id = match.group(1).strip()

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # Fetch the connection details
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to retrieve connection {connection_id}: {response.text}"

    conn_data = response.json()

    # Verify connection name
    expected_conn_name = f"header-filter-conn-{run_id}"
    assert conn_data.get("name") == expected_conn_name, f"Expected connection name '{expected_conn_name}', got '{conn_data.get('name')}'"

    # Verify source name
    source = conn_data.get("source", {})
    expected_source_name = f"header-source-{run_id}"
    assert source.get("name") == expected_source_name, f"Expected source name '{expected_source_name}', got '{source.get('name')}'"

    # Verify destination name
    destination = conn_data.get("destination", {})
    expected_dest_name = f"mock-dest-{run_id}"
    assert destination.get("name") == expected_dest_name, f"Expected destination name '{expected_dest_name}', got '{destination.get('name')}'"

    # Verify filter rule
    rules = conn_data.get("rules", [])
    has_correct_filter = False
    for rule in rules:
        rule_str = str(rule).lower()
        if "filter" in rule_str and "x-target-event" in rule_str and "process" in rule_str:
            has_correct_filter = True
            break
            
    assert has_correct_filter, f"Could not find a filter rule matching header 'x-target-event' to 'process' in rules: {rules}"
