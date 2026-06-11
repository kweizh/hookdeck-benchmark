import os
import time
import requests
import pytest
import json

def test_hookdeck_transformation():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    source_name = f"webhook-source-{run_id}"
    connection_name = f"transform-connection-{run_id}"
    secret_val = f"secret-val-{run_id}"

    # 1. Publish test event
    publish_url = "https://hkdk.events/v1/publish"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": source_name,
        "Content-Type": "application/json"
    }
    payload = {"old_key": "test_value"}
    publish_res = requests.post(publish_url, headers=headers, json=payload)
    assert publish_res.status_code in (200, 201, 202), f"Failed to publish event: {publish_res.text}"

    # 2. Wait for event processing
    time.sleep(5)

    # 3. Retrieve connection ID
    conn_url = "https://api.hookdeck.com/2025-07-01/connections"
    conn_res = requests.get(conn_url, headers={"Authorization": f"Bearer {api_key}"}, params={"name": connection_name})
    assert conn_res.status_code == 200, f"Failed to list connections: {conn_res.text}"
    conn_data = conn_res.json()
    assert "models" in conn_data and len(conn_data["models"]) > 0, f"Connection {connection_name} not found."
    conn_id = conn_data["models"][0]["id"]

    # 4. Retrieve latest event for connection
    events_url = "https://api.hookdeck.com/2025-07-01/events"
    
    latest_event = None
    for _ in range(3):
        events_res = requests.get(events_url, headers={"Authorization": f"Bearer {api_key}"}, params={"connection_id": conn_id, "limit": 1})
        assert events_res.status_code == 200, f"Failed to list events: {events_res.text}"
        events_data = events_res.json()
        if "models" in events_data and len(events_data["models"]) > 0:
            latest_event = events_data["models"][0]
            break
        time.sleep(3)

    assert latest_event is not None, f"No events found for connection {connection_name}."

    event_data = latest_event.get("data", {})

    # Check custom header
    event_headers = event_data.get("headers", {})
    assert "x-custom-secret" in event_headers, f"Custom header 'x-custom-secret' not found in event headers: {event_headers}"
    assert event_headers["x-custom-secret"] == secret_val, f"Custom header 'x-custom-secret' value is incorrect. Expected {secret_val}, got {event_headers['x-custom-secret']}"

    # Check body transformation
    event_body = event_data.get("body", {})
    body_str = json.dumps(event_body)
    assert "new_key" in body_str, f"Transformed payload does not contain 'new_key'. Body: {body_str}"
    assert "test_value" in body_str, f"Transformed payload does not contain 'test_value'. Body: {body_str}"
    assert "old_key" not in body_str, f"Transformed payload still contains 'old_key'. Body: {body_str}"
