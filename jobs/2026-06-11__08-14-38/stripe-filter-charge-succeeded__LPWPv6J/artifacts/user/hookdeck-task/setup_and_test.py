import os
import sys
import json
import requests
import time

def main():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    run_id = os.environ.get("ZEALT_RUN_ID")

    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable is not set.")
        sys.exit(1)
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set.")
        sys.exit(1)

    print(f"Using Run ID: {run_id}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 1. Create or get connection
    connection_payload = {
        "name": f"stripe-charge-succeeded-{run_id}",
        "source": {
            "name": f"stripe-src-{run_id}",
            "type": "STRIPE"
        },
        "destination": {
            "name": f"mock-dest-{run_id}",
            "type": "MOCK_API"
        },
        "rules": [
            {
                "type": "filter",
                "body": {
                    "type": "charge.succeeded"
                }
            }
        ]
    }

    url = "https://api.hookdeck.com/2025-07-01/connections"
    print(f"Sending request to {url}...")
    response = requests.post(url, headers=headers, json=connection_payload)
    
    conn_data = None
    if response.status_code in (200, 201):
        conn_data = response.json()
        print("Connection created successfully.")
    elif response.status_code == 409:
        err_json = response.json()
        if "data" in err_json and "webhook" in err_json["data"]:
            conn_data = err_json["data"]["webhook"]
            print("Connection already exists. Retrieved from 409 response.")
        else:
            print("Resource already exists, but unable to parse webhook from response data.")
            print(json.dumps(err_json, indent=2))
            sys.exit(1)
    else:
        print(f"Failed to create connection. Status: {response.status_code}")
        print(response.text)
        sys.exit(1)

    connection_id = conn_data["id"]
    source_id = conn_data["source"]["id"]
    destination_id = conn_data["destination"]["id"]

    print(f"Connection ID: {connection_id}")
    print(f"Source ID: {source_id}")
    print(f"Destination ID: {destination_id}")

    # 2. Publish 4 distinct events
    publish_url = "https://hkdk.events/v1/publish"
    events_to_send = [
        "charge.succeeded",
        "charge.failed",
        "charge.refunded",
        "charge.captured"
    ]

    target_request_id = None

    for event_type in events_to_send:
        pub_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Hookdeck-Source-Id": source_id
        }
        # Using a dual-compatible payload structure to cover all bases
        payload = {
            "type": event_type,
            "body": {
                "type": event_type
            }
        }
        print(f"Publishing {event_type} to {publish_url}...")
        pub_resp = requests.post(publish_url, headers=pub_headers, json=payload)
        if pub_resp.status_code not in (200, 201, 202):
            print(f"Failed to publish {event_type}. Status: {pub_resp.status_code}")
            print(pub_resp.text)
            sys.exit(1)
        
        pub_data = pub_resp.json()
        print(f"Published {event_type} successfully. Response: {pub_data}")
        if event_type == "charge.succeeded":
            target_request_id = pub_data.get("request_id")
            print(f"Captured target request ID for charge.succeeded: {target_request_id}")

    if not target_request_id:
        print("Error: Did not capture a request ID for charge.succeeded event.")
        sys.exit(1)

    # 3. Poll Hookdeck Inspect API to wait for event processing
    print(f"Waiting for Hookdeck to finish processing event with request ID: {target_request_id}...")
    events_url = f"https://api.hookdeck.com/2025-07-01/events?webhook_id={connection_id}"
    
    delivered_event_id = None
    max_attempts = 20
    for attempt in range(1, max_attempts + 1):
        print(f"Polling attempt {attempt}/{max_attempts}...")
        ev_resp = requests.get(events_url, headers=headers)
        if ev_resp.status_code == 200:
            ev_data = ev_resp.json()
            models = ev_data.get("models", [])
            print(f"Found {len(models)} events total on this connection.")
            
            # Find the event matching our target request_id
            matching_events = [m for m in models if m.get("request_id") == target_request_id]
            if matching_events:
                matching_event = matching_events[0]
                status = matching_event.get("status")
                print(f"Found matching event {matching_event['id']} with status: {status}")
                if status == "SUCCESSFUL":
                    delivered_event_id = matching_event["id"]
                    print(f"Event {delivered_event_id} processed successfully!")
                    break
                elif status in ("FAILED", "ERROR"):
                    print(f"Warning: Event found but has status {status}.")
        else:
            print(f"Failed to query events: {ev_resp.status_code}")
            print(ev_resp.text)
        time.sleep(3)

    if not delivered_event_id:
        print("Error: Could not find SUCCESSFUL delivered event for the published charge.succeeded request.")
        sys.exit(1)

    # 4. Verify the delivered event details
    event_detail_url = f"https://api.hookdeck.com/2025-07-01/events/{delivered_event_id}"
    detail_resp = requests.get(event_detail_url, headers=headers)
    if detail_resp.status_code != 200:
        print(f"Failed to retrieve event details for {delivered_event_id}")
        sys.exit(1)

    detail_data = detail_resp.json()
    print("Delivered event details:")
    print(json.dumps(detail_data, indent=2))

    # Double check body type
    body_data = detail_data.get("data", {}).get("body", {})
    print(f"Event body data: {body_data}")

    # 5. Write the log file
    log_path = "/home/user/hookdeck-task/output.log"
    log_content = (
        f"Connection ID: {connection_id}\n"
        f"Source ID: {source_id}\n"
        f"Destination ID: {destination_id}\n"
        f"Delivered Event ID: {delivered_event_id}\n"
    )
    with open(log_path, "w") as f:
        f.write(log_content)
    
    print(f"Log written to {log_path} successfully.")
    print("Log content:")
    print(log_content)

if __name__ == "__main__":
    main()
