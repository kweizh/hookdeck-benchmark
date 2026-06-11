import os
import re
import subprocess
import json
import pytest

LOG_FILE = "/home/user/hookdeck-task/output.log"

def test_log_file_exists_and_contains_source_id():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Source ID:\s*(src_[a-zA-Z0-9]+)", content)
    assert match is not None, f"Source ID not found in {LOG_FILE}. Content: {content}"

def test_source_verification_config():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    match = re.search(r"Source ID:\s*(src_[a-zA-Z0-9]+)", content)
    assert match is not None, "Source ID not found in log file."
    source_id = match.group(1)
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    
    result = subprocess.run(
        [
            "curl", "-s", 
            "-H", f"Authorization: Bearer {api_key}", 
            f"https://api.hookdeck.com/2025-07-01/sources/{source_id}"
        ],
        capture_output=True, text=True
    )
    
    assert result.returncode == 0, f"curl request failed: {result.stderr}"
    
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"Failed to parse JSON response: {result.stdout}")
    
    expected_name = f"secure-source-{run_id}"
    assert data.get("name") == expected_name, f"Expected source name '{expected_name}', got '{data.get('name')}'"
    
    verification = data.get("verification")
    assert verification is not None, "Verification configuration not found in response."
    assert verification.get("type") == "HMAC", f"Expected verification type 'HMAC', got '{verification.get('type')}'"
    
    configs = verification.get("configs")
    assert configs is not None, "Verification configs not found in response."
    
    assert configs.get("algorithm") == "SHA256", f"Expected algorithm 'SHA256', got '{configs.get('algorithm')}'"
    assert configs.get("encoding") == "base64", f"Expected encoding 'base64', got '{configs.get('encoding')}'"
    assert configs.get("header_key") == "x-custom-signature", f"Expected header_key 'x-custom-signature', got '{configs.get('header_key')}'"
