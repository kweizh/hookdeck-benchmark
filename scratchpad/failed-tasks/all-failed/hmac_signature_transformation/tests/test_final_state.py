import os
import re
import time
import hmac
import hashlib
import json
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def get_env_vars():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")
    hmac_secret = os.environ.get("HMAC_SECRET")
    assert run_id, "ZEALT_RUN_ID is missing"
    assert api_key, "HOOKDECK_API_KEY is missing"
    assert hmac_secret, "HMAC_SECRET is missing"
    return run_id, api_key, hmac_secret

def test_log_file_exists():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist."

def test_extract_ids_and_verify_connection():
    run_id, api_key, _ = get_env_vars()
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
        
    conn_match = re.search(r"Connection ID:\s*([a-zA-Z0-9_]+)", content)
    assert conn_match, "Could not find 'Connection ID: <id>' in output.log"
    connection_id = conn_match.group(1)
    
    source_match = re.search(r"Source ID:\s*([a-zA-Z0-9_]+)", content)
    assert source_match, "Could not find 'Source ID: <id>' in output.log"
    source_id = source_match.group(1)
    
    # Verify connection via API
    url = f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to fetch connection {connection_id}: {response.text}"
    
    conn_data = response.json()
    expected_name = f"hmac-connection-{run_id}"
    assert conn_data.get("name") == expected_name, f"Expected connection name {expected_name}, got {conn_data.get('name')}"

def test_publish_and_verify_hmac():
    run_id, api_key, hmac_secret = get_env_vars()
    
    with open(LOG_FILE, "r") as f:
        content = f.read()
    source_match = re.search(r"Source ID:\s*([a-zA-Z0-9_]+)", content)
    assert source_match, "Could not find 'Source ID: <id>' in output.log"
    source_id = source_match.group(1)
    
    # Publish event
    publish_url = "https://hkdk.events/v1/publish"
    publish_headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": f"hmac-source-{run_id}",
        "Content-Type": "application/json"
    }
    payload = {"message": "hello world"}
    
    pub_res = requests.post(publish_url, headers=publish_headers, json=payload)
    assert pub_res.status_code == 200, f"Failed to publish event: {pub_res.text}"
    
    # Wait for processing
    time.sleep(5)
    
    # Query events
    events_url = f"https://api.hookdeck.com/2025-07-01/events?source_id={source_id}&limit=5"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Retry logic for fetching the processed event
    found_hmac = None
    expected_hmac = hmac.new(
        hmac_secret.encode('utf-8'),
        json.dumps(payload).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    for _ in range(3):
        ev_res = requests.get(events_url, headers=headers)
        assert ev_res.status_code == 200, f"Failed to fetch events: {ev_res.text}"
        
        events_data = ev_res.json()
        models = events_data.get("models", [])
        
        for event in models:
            # Look at event attempts or headers
            # Hookdeck events/attempts usually store headers in `headers` or `request_headers`
            event_str = json.dumps(event).lower()
            if "x-hmac-signature" in event_str:
                # Try to extract the value
                match = re.search(r'"x-hmac-signature":\s*"([^"]+)"', json.dumps(event, ignore_nan=True) if hasattr(json, 'ignore_nan') else json.dumps(event))
                if not match:
                    match = re.search(r'"x-hmac-signature":\s*\["([^"]+)"\]', json.dumps(event))
                if match:
                    found_hmac = match.group(1)
                    break
        
        if found_hmac:
            break
        time.sleep(3)
        
    assert found_hmac is not None, "Could not find 'x-hmac-signature' in the delivered event headers."
    assert found_hmac == expected_hmac, f"Expected HMAC {expected_hmac}, but got {found_hmac}."
