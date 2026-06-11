import os
import time
import requests
import pytest

def test_hookdeck_transformation():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is missing."

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Step 2: Verify connection and rules
    conn_name = f"transform-conn-{run_id}"
    conn_url = f"https://api.hookdeck.com/2025-07-01/connections?name={conn_name}"
    conn_resp = requests.get(conn_url, headers=headers)
    assert conn_resp.status_code == 200, f"Failed to get connection: {conn_resp.text}"
    conn_data = conn_resp.json()
    assert "models" in conn_data and len(conn_data["models"]) > 0, f"Connection {conn_name} not found."
    
    connection = conn_data["models"][0]
    rules = connection.get("rules", [])
    has_transform = any(rule.get("type") == "transform" for rule in rules)
    assert has_transform, "Connection does not have a transformation rule."

    # Step 3: Publish event
    source_name = f"transform-source-{run_id}"
    publish_url = "https://hkdk.events/v1/publish"
    publish_headers = headers.copy()
    publish_headers["X-Hookdeck-Source-Name"] = source_name
    
    payload = {
        "customer_id": "test_user_789",
        "status": "active"
    }
    
    pub_resp = requests.post(publish_url, headers=publish_headers, json=payload)
    assert pub_resp.status_code == 200, f"Failed to publish event: {pub_resp.text}"

    # Step 4: Wait for processing
    time.sleep(5)

    # Step 5: Retrieve and verify event
    dest_name = f"transform-dest-{run_id}"
    events_url = f"https://api.hookdeck.com/2025-07-01/events?destination_name={dest_name}&order_by=created_at&dir=desc&limit=1"
    
    events_resp = requests.get(events_url, headers=headers)
    assert events_resp.status_code == 200, f"Failed to get events: {events_resp.text}"
    events_data = events_resp.json()
    assert "models" in events_data and len(events_data["models"]) > 0, "No events found for the destination."
    
    latest_event = events_data["models"][0]
    assert latest_event.get("response_status") == 200, f"Event response status is not 200: {latest_event.get('response_status')}"
    
    event_data = latest_event.get("data", {})
    body_data = event_data.get("body", {})
    if "body" in body_data:
        body_data = body_data["body"]
        
    assert "userId" in body_data, f"userId not found in transformed body: {body_data}"
    assert body_data["userId"] == "test_user_789", f"userId is incorrect: {body_data['userId']}"
    assert "status" in body_data and body_data["status"] == "active", f"status is incorrect: {body_data.get('status')}"
    assert "customer_id" not in body_data, f"customer_id should be removed: {body_data}"
    
    event_headers = event_data.get("headers", {})
    assert "x-custom-transformed" in event_headers, f"x-custom-transformed header not found: {event_headers}"
    assert event_headers["x-custom-transformed"] == "true", f"x-custom-transformed header is not true: {event_headers['x-custom-transformed']}"
