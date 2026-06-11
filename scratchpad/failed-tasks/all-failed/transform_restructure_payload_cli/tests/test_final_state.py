import os
import re
import time
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set"
    return run_id

def get_api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set"
    return api_key

def test_log_file_exists_and_contains_connection_id():
    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    match = re.search(r"Connection ID:\s+(\S+)", content)
    assert match, "Log file does not contain a valid Connection ID in the format 'Connection ID: <connection_id>'"

def test_transformation_restructures_payload_and_adds_headers():
    run_id = get_run_id()
    api_key = get_api_key()
    source_name = f"legacy-source-{run_id}"
    
    # Send a test event using the Publish API
    publish_url = "https://hkdk.events/v1/publish"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": source_name,
        "Content-Type": "application/json"
    }
    test_value = f"test_value_{run_id}"
    payload = {
        "data": {
            "object": {
                "test_key": test_value
            }
        }
    }
    
    response = requests.post(publish_url, headers=headers, json=payload)
    assert response.status_code == 200, f"Failed to publish event. Status: {response.status_code}, Response: {response.text}"
    
    # Wait for the event to be processed
    time.sleep(5)
    
    # Get the source ID
    sources_url = f"https://api.hookdeck.com/2025-07-01/sources?name={source_name}"
    headers_api = {
        "Authorization": f"Bearer {api_key}"
    }
    response = requests.get(sources_url, headers=headers_api)
    assert response.status_code == 200, f"Failed to list sources. Status: {response.status_code}, Response: {response.text}"
    
    sources_data = response.json()
    assert "models" in sources_data and len(sources_data["models"]) > 0, f"Source '{source_name}' not found."
    source_id = sources_data["models"][0]["id"]
    
    # Query events
    events_url = f"https://api.hookdeck.com/2025-07-01/events?source_id={source_id}&status=SUCCESSFUL"
    
    # Retry logic for event delivery
    max_retries = 3
    events_data = None
    for attempt in range(max_retries):
        response = requests.get(events_url, headers=headers_api)
        assert response.status_code == 200, f"Failed to query events. Status: {response.status_code}, Response: {response.text}"
        events_data = response.json()
        if "models" in events_data and len(events_data["models"]) > 0:
            break
        time.sleep(3)
        
    assert events_data and "models" in events_data and len(events_data["models"]) > 0, "No SUCCESSFUL events found for the source."
    
    event = events_data["models"][0]
    
    # Verify the delivered event in the Inspect API response
    # The event object in the Inspect API has a `request` or `body` field depending on Hookdeck's structure.
    # Usually, `event.body` or `event.request.body` contains the payload.
    # Hookdeck API for events: event.data.body or event.body?
    # Actually, the Inspect API returns an Event. Let's look at the plan.
    # Inspect API: curl "https://api.hookdeck.com/2025-07-01/events?source_id=src_123&status=SUCCESSFUL"
    # It returns events. Let's assume the event object has `body` and `headers` directly, or under `request` or `data` or `event_data.body`.
    # To be safe, we'll check if the expected payload and headers are in the stringified event.
    
    event_str = str(event)
    
    # Check body
    # The body should be exactly {"test_key": "test_value_${run-id}"}
    # It could be a dict in the response.
    # Let's search for the test_value in the event.
    assert test_value in event_str, f"Expected test_value '{test_value}' not found in the delivered event."
    
    # We should specifically check if the restructuring happened.
    # If it didn't happen, the event body would be {"data": {"object": {"test_key": ...}}}
    # If it did happen, the event body would be {"test_key": ...}
    # Let's check that 'data' and 'object' are NOT the top-level keys.
    # Or, we can find the body in the event object.
    
    # In Hookdeck API, the event object usually has a `body` field or `event_data.body`.
    body = event.get("body") or event.get("request", {}).get("body") or event.get("data", {}).get("body")
    if not body:
        # Fallback to checking the stringified event
        assert "'data': {'object':" not in event_str, "Payload was not restructured. Found 'data.object' in the event."
    else:
        assert "test_key" in body, f"Payload was not restructured correctly. Body: {body}"
        assert body["test_key"] == test_value, f"Expected test_key to be {test_value}, got {body.get('test_key')}"
    
    # Check headers
    # Headers are usually in `headers` or `request.headers` or `data.headers`.
    headers_dict = event.get("headers") or event.get("request", {}).get("headers") or event.get("data", {}).get("headers") or {}
    # headers keys might be lowercase
    headers_dict = {k.lower(): v for k, v in headers_dict.items()} if headers_dict else {}
    
    if headers_dict:
        assert headers_dict.get("x-hookdeck-transformed") == "true", "Header x-hookdeck-transformed: true not found."
        expected_secret = f"super_secret_value_{run_id}"
        assert headers_dict.get("x-secret-token") == expected_secret, f"Header x-secret-token: {expected_secret} not found."
    else:
        # Fallback to string search if we couldn't find the headers dict
        assert "x-hookdeck-transformed" in event_str.lower(), "Header x-hookdeck-transformed not found in the event."
        expected_secret = f"super_secret_value_{run_id}"
        assert expected_secret in event_str, f"Header x-secret-token value not found in the event."
