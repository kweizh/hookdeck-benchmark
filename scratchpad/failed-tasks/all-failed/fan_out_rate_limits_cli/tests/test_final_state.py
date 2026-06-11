import os
import subprocess
import json
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    return run_id

def test_log_file_exists_and_contains_url():
    """Verify that the script output the Source URL to the log file."""
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    assert "Source URL: https://events.hookdeck.com/e/" in content, \
        f"Expected 'Source URL: https://events.hookdeck.com/e/' in {LOG_FILE}, but got:\n{content}"

def test_hookdeck_connections_and_rate_limits():
    """Use Hookdeck CLI to verify the fan-out architecture and rate limits."""
    run_id = get_run_id()
    dest_1_name = f"mock-dest-1-{run_id}"
    dest_2_name = f"mock-dest-2-{run_id}"
    expected_source_name = f"fan-out-source-{run_id}"

    result = subprocess.run(
        ["hookdeck", "gateway", "connection", "list", "--output", "json"],
        capture_output=True, text=True, cwd=PROJECT_DIR
    )
    assert result.returncode == 0, f"'hookdeck gateway connection list' failed: {result.stderr}"
    
    try:
        connections = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON output from hookdeck CLI: {result.stdout}")

    # Find connection for dest 1
    conn_1 = next((c for c in connections if c.get("destination", {}).get("name") == dest_1_name), None)
    assert conn_1 is not None, f"Connection to destination '{dest_1_name}' not found."
    
    # Check rate limit for dest 1
    assert conn_1["destination"].get("rate_limit") == 10, \
        f"Expected rate limit 10 for {dest_1_name}, got {conn_1['destination'].get('rate_limit')}"
    assert conn_1["destination"].get("rate_limit_period") == "second", \
        f"Expected rate limit period 'second' for {dest_1_name}, got {conn_1['destination'].get('rate_limit_period')}"

    # Find connection for dest 2
    conn_2 = next((c for c in connections if c.get("destination", {}).get("name") == dest_2_name), None)
    assert conn_2 is not None, f"Connection to destination '{dest_2_name}' not found."
    
    # Check rate limit for dest 2
    assert conn_2["destination"].get("rate_limit") == 50, \
        f"Expected rate limit 50 for {dest_2_name}, got {conn_2['destination'].get('rate_limit')}"
    assert conn_2["destination"].get("rate_limit_period") == "second", \
        f"Expected rate limit period 'second' for {dest_2_name}, got {conn_2['destination'].get('rate_limit_period')}"

    # Verify both share the same source name
    assert conn_1["source"].get("name") == expected_source_name, \
        f"Expected source name '{expected_source_name}' for connection 1, got {conn_1['source'].get('name')}"
    assert conn_2["source"].get("name") == expected_source_name, \
        f"Expected source name '{expected_source_name}' for connection 2, got {conn_2['source'].get('name')}"

    # Verify both share the exact same source ID
    assert conn_1["source"].get("id") == conn_2["source"].get("id"), \
        f"Expected both connections to share the same source ID. Conn 1 source: {conn_1['source'].get('id')}, Conn 2 source: {conn_2['source'].get('id')}"
