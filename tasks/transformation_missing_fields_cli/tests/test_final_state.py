import os
import time
import requests
import pytest

OUTPUT_LOG = "/home/user/hookdeck-task/output.log"

@pytest.fixture(scope="session")
def context():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert run_id, "ZEALT_RUN_ID environment variable not set."
    assert api_key, "HOOKDECK_API_KEY environment variable not set."
    
    return {
        "run_id": run_id,
        "api_key": api_key,
        "source_name": f"safe-transform-src-{run_id}",
        "dest_name": f"safe-transform-dest-{run_id}",
        "connection_id": None,
        "source_id": None
    }

def test_log_file_and_connection_id(context):
    assert os.path.isfile(OUTPUT_LOG), f"Log file {OUTPUT_LOG} does not exist."
    
    connection_id = None
    with open(OUTPUT_LOG, "r") as f:
        content = f.read()
        for line in content.splitlines():
            if line.startswith("Connection ID:"):
                connection_id = line.split(":", 1)[1].strip()
                break
                
    assert connection_id, "Log file does not contain a valid 'Connection ID: <connection_id>' line."
    context["connection_id"] = connection_id

def test_connection_details(context):
    connection_id = context["connection_id"]
    api_key = context["api_key"]
    run_id = context["run_id"]
    
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/connections/{connection_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 200, f"Failed to fetch connection details: {response.text}"
    
    data = response.json()
    assert data.get("source", {}).get("name") == context["source_name"], \
        f"Expected source name {context['source_name']}, got {data.get('source', {}).get('name')}"
    
    assert data.get("destination", {}).get("name") == context["dest_name"], \
        f"Expected destination name {context['dest_name']}, got {data.get('destination', {}).get('name')}"
        
    context["source_id"] = data.get("source", {}).get("id")
    assert context["source_id"], "Source ID not found in connection details."

def test_publish_events(context):
    api_key = context["api_key"]
    source_name = context["source_name"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": source_name,
        "Content-Type": "application/json"
    }
    
    # Event 1: Valid payload
    payload_valid = {"data": {"user": {"id": "user_123"}}}
    resp1 = requests.post(
        "https://hkdk.events/v1/publish",
        headers=headers,
        json=payload_valid
    )
    assert resp1.status_code == 200, f"Failed to publish valid event: {resp1.text}"
    
    # Event 2: Missing fields payload
    payload_missing = {"data": {}}
    resp2 = requests.post(
        "https://hkdk.events/v1/publish",
        headers=headers,
        json=payload_missing
    )
    assert resp2.status_code == 200, f"Failed to publish missing fields event: {resp2.text}"
    
    # Wait for Hookdeck to process events
    time.sleep(3)

def test_event_transformations(context):
    api_key = context["api_key"]
    source_id = context["source_id"]
    
    response = requests.get(
        f"https://api.hookdeck.com/2025-07-01/events?source_id={source_id}&limit=2",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    assert response.status_code == 200, f"Failed to fetch events: {response.text}"
    
    data = response.json()
    events = data.get("models", [])
    assert len(events) >= 2, f"Expected at least 2 events, found {len(events)}"
    
    # Both events should be successful
    for event in events[:2]:
        assert event.get("status") == "SUCCESSFUL", f"Event {event.get('id')} is not SUCCESSFUL. Status: {event.get('status')}"
    
    # Check attempts for transformed payload. Hookdeck Inspect API includes `data` or we need to check attempts.
    # The requirement is that the transformation doesn't fail (status SUCCESSFUL).
    # Since we can't easily assert the exact transformed payload structure without knowing Hookdeck's exact response format for delivered body,
    # and the prompt said "verify that the events were successfully transformed without throwing TypeErrors", the SUCCESSFUL status is our primary check.
    # If the transformation threw a TypeError, the status would be FAILED.
