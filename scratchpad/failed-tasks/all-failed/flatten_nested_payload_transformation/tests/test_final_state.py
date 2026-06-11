import os
import time
import requests
import pytest

def test_flatten_transformation():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is missing"

    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing"

    source_name = f"flatten-source-{run_id}"
    dest_name = f"flatten-dest-{run_id}"

    # Send test event via Publish API
    publish_url = "https://hkdk.events/v1/publish"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": source_name,
        "Content-Type": "application/json"
    }
    payload = {
        "event_type": "user.created",
        "data": {
            "user": {
                "id": "u_999",
                "email": "hello@example.com"
            }
        }
    }
    publish_resp = requests.post(publish_url, headers=headers, json=payload)
    assert publish_resp.status_code == 200, f"Failed to publish event: {publish_resp.text}"

    # Wait for processing
    time.sleep(5)

    # Fetch events via Inspect API
    inspect_url = "https://api.hookdeck.com/2025-07-01/events"
    inspect_headers = {
        "Authorization": f"Bearer {api_key}"
    }
    inspect_params = {
        "destination_name": dest_name
    }
    inspect_resp = requests.get(inspect_url, headers=inspect_headers, params=inspect_params)
    assert inspect_resp.status_code == 200, f"Failed to fetch events: {inspect_resp.text}"

    events_data = inspect_resp.json()
    models = events_data.get("models", [])
    assert len(models) > 0, f"No events found for destination {dest_name}"

    # Verify transformation on the latest event
    latest_event = models[0]
    transformed_body = latest_event.get("data", {}).get("body", {}).get("body", {})

    expected_body = {
        "event_type": "user.created",
        "user_id": "u_999",
        "user_email": "hello@example.com"
    }

    assert transformed_body == expected_body, f"Transformed body {transformed_body} does not match expected {expected_body}"
