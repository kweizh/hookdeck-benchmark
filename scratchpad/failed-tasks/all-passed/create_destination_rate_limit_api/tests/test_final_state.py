import os
import re
import requests
import pytest

LOG_FILE = "/home/user/hookdeck-task/output.log"

def test_output_log_exists_and_contains_dest_id():
    """Verify that the output log exists and contains a valid destination ID."""
    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Destination ID:\s*(des_[a-zA-Z0-9]+)", content)
    assert match is not None, f"Could not find 'Destination ID: des_...' in {LOG_FILE}"
    
    dest_id = match.group(1)
    assert dest_id.startswith("des_"), f"Extracted ID {dest_id} does not start with 'des_'"

def test_destination_created_with_rate_limit():
    """Verify the destination is created in Hookdeck with the correct rate limit settings."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set"
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set"
    
    # Read the dest_id from the log file
    with open(LOG_FILE, "r") as f:
        content = f.read()
    match = re.search(r"Destination ID:\s*(des_[a-zA-Z0-9]+)", content)
    assert match is not None, "Failed to extract Destination ID for API verification"
    dest_id = match.group(1)
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Try fetching the destination list to find the destination
    response = requests.get("https://api.hookdeck.com/2025-07-01/destinations", headers=headers)
    assert response.status_code == 200, f"Failed to fetch destinations: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    
    dest = next((d for d in models if d.get("id") == dest_id), None)
    assert dest is not None, f"Destination with ID {dest_id} not found in Hookdeck"
    
    expected_name = f"rate-limited-dest-{run_id}"
    assert dest.get("name") == expected_name, f"Expected destination name '{expected_name}', got '{dest.get('name')}'"
    
    config = dest.get("config", {})
    assert config.get("url") == "https://mock.hookdeck.com/rate-limited", f"Expected url 'https://mock.hookdeck.com/rate-limited', got '{config.get('url')}'"
    assert str(config.get("rate_limit")) == "10", f"Expected rate_limit to be 10, got '{config.get('rate_limit')}'"
    assert config.get("rate_limit_period") == "second", f"Expected rate_limit_period to be 'second', got '{config.get('rate_limit_period')}'"
