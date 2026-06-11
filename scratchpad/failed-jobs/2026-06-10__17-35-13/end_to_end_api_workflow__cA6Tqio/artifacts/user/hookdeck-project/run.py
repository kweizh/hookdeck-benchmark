#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import time
import urllib.request
import urllib.error

def run_cmd(args):
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    return result.stdout

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")

    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Using ZEALT_RUN_ID: {run_id}")

    # 1. Authenticate with Hookdeck CLI
    print("Authenticating with Hookdeck CLI...")
    subprocess.run(["hookdeck", "ci", "--api-key", api_key], check=True)

    # 2. Check/Create Source
    source_name = f"source-{run_id}"
    print(f"Checking for source: {source_name}")
    sources_json = run_cmd(["hookdeck", "gateway", "source", "list", "--output", "json"])
    sources_data = json.loads(sources_json)
    
    source_id = None
    source_url = None
    for item in sources_data.get("models", []):
        if item.get("name") == source_name:
            source_id = item.get("id")
            source_url = item.get("url")
            print(f"Found existing source: {source_id} at {source_url}")
            break

    if not source_id:
        print(f"Creating source: {source_name}")
        create_res = run_cmd(["hookdeck", "gateway", "source", "create", "--name", source_name, "--type", "WEBHOOK", "--output", "json"])
        create_data = json.loads(create_res)
        source_id = create_data.get("id")
        source_url = create_data.get("url")
        print(f"Created source: {source_id} at {source_url}")

    # 3. Check/Create Destination
    dest_name = f"mock-dest-{run_id}"
    print(f"Checking for destination: {dest_name}")
    dest_json = run_cmd(["hookdeck", "gateway", "destination", "list", "--output", "json"])
    dest_data = json.loads(dest_json)

    dest_id = None
    for item in dest_data.get("models", []):
        if item.get("name") == dest_name:
            dest_id = item.get("id")
            print(f"Found existing destination: {dest_id}")
            break

    if not dest_id:
        print(f"Creating destination: {dest_name}")
        create_res = run_cmd(["hookdeck", "gateway", "destination", "create", "--name", dest_name, "--type", "MOCK_API", "--output", "json"])
        create_data = json.loads(create_res)
        dest_id = create_data.get("id")
        print(f"Created destination: {dest_id}")

    # 4. Check/Create Connection
    conn_name = f"conn-{run_id}"
    print(f"Checking for connection: {conn_name}")
    conn_json = run_cmd(["hookdeck", "gateway", "connection", "list", "--output", "json"])
    conn_data = json.loads(conn_json)

    conn_id = None
    for item in conn_data.get("models", []):
        if item.get("name") == conn_name:
            conn_id = item.get("id")
            print(f"Found existing connection: {conn_id}")
            break

    if not conn_id:
        print(f"Creating connection: {conn_name}")
        create_res = run_cmd([
            "hookdeck", "gateway", "connection", "create",
            "--name", conn_name,
            "--source-id", source_id,
            "--destination-id", dest_id,
            "--output", "json"
        ])
        create_data = json.loads(create_res)
        conn_id = create_data.get("id")
        print(f"Created connection: {conn_id}")

    # 5. Publish test event to the Source
    payload = {"test_id": run_id}
    payload_bytes = json.dumps(payload).encode("utf-8")
    print(f"Publishing test event to {source_url} with payload {payload}")

    req = urllib.request.Request(
        source_url,
        data=payload_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            print(f"Publish response: {resp_body}")
            resp_data = json.loads(resp_body)
            request_id = resp_data.get("request_id")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error publishing event: {e}", file=sys.stderr)
        sys.exit(1)

    if not request_id:
        print("Error: Could not retrieve request_id from publish response.", file=sys.stderr)
        sys.exit(1)

    print(f"Event published successfully. Request ID: {request_id}")

    # 6. Poll Hookdeck API to verify successful event processing and get Event ID
    print("Polling Hookdeck API for the processed event...")
    event_id = None
    max_retries = 15
    for attempt in range(max_retries):
        print(f"Polling attempt {attempt + 1}/{max_retries}...")
        try:
            events_json = run_cmd(["hookdeck", "gateway", "request", "events", request_id, "--output", "json"])
            events_data = json.loads(events_json)
            if events_data and len(events_data) > 0:
                event = events_data[0]
                status = event.get("status")
                print(f"Event status: {status}")
                if status == "SUCCESSFUL":
                    event_id = event.get("id")
                    print(f"Found successful event ID: {event_id}")
                    break
        except Exception as e:
            print(f"Error during polling: {e}", file=sys.stderr)
        time.sleep(2)

    if not event_id:
        print("Error: Event was not processed successfully within the timeout.", file=sys.stderr)
        sys.exit(1)

    # 7. Write to log file
    log_dir = "/home/user/hookdeck-project"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "output.log")
    
    print(f"Writing Connection ID and Event ID to {log_path}...")
    with open(log_path, "w") as f:
        f.write(f"Connection ID: {conn_id}\n")
        f.write(f"Event ID: {event_id}\n")

    print("Workflow completed successfully.")

if __name__ == "__main__":
    main()
