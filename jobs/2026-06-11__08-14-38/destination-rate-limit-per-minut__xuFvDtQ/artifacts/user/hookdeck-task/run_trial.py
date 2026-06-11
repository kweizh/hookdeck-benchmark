import urllib.request
import urllib.parse
import json
import os
import sys
import time
from datetime import datetime

api_key = os.environ.get('HOOKDECK_API_KEY')
run_id = os.environ.get('ZEALT_RUN_ID')

if not api_key:
    print("Error: HOOKDECK_API_KEY not set")
    sys.exit(1)
if not run_id:
    print("Error: ZEALT_RUN_ID not set")
    sys.exit(1)

base_url = "https://api.hookdeck.com/2025-07-01"

def api_request(method, path, body=None):
    url = f"{base_url}{path}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "curl/8.7.1"
    }
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            if res_body:
                return json.loads(res_body)
            return None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"HTTP Error {method} {path}: {e.code}")
        print(err_body)
        raise e
    except Exception as e:
        print(f"Error {method} {path}: {e}")
        raise e

def clean_up():
    print("Cleaning up existing resources...")
    # List connections
    try:
        conns = api_request("GET", "/connections")
        if conns and "models" in conns:
            for conn in conns["models"]:
                if run_id in conn.get("name", ""):
                    print(f"Deleting connection {conn['id']} ({conn['name']})...")
                    api_request("DELETE", f"/connections/{conn['id']}")
    except Exception as e:
        print(f"Error deleting connections: {e}")

    # List sources
    try:
        sources = api_request("GET", "/sources")
        if sources and "models" in sources:
            for src in sources["models"]:
                if run_id in src.get("name", ""):
                    print(f"Deleting source {src['id']} ({src['name']})...")
                    api_request("DELETE", f"/sources/{src['id']}")
    except Exception as e:
        print(f"Error deleting sources: {e}")

    # List destinations
    try:
        destinations = api_request("GET", "/destinations")
        if destinations and "models" in destinations:
            for dest in destinations["models"]:
                if run_id in dest.get("name", ""):
                    print(f"Deleting destination {dest['id']} ({dest['name']})...")
                    api_request("DELETE", f"/destinations/{dest['id']}")
    except Exception as e:
        print(f"Error deleting destinations: {e}")

def run():
    clean_up()

    # 1. Create WEBHOOK source
    source_name = f"rl-src-{run_id}"
    print(f"Creating source {source_name}...")
    source = api_request("POST", "/sources", {
        "name": source_name,
        "type": "WEBHOOK"
    })
    source_id = source["id"]
    source_url = source["url"]
    print(f"Created source {source_id} at {source_url}")

    # 2. Create MOCK_API destination
    dest_name = f"rl-dest-{run_id}"
    print(f"Creating destination {dest_name}...")
    destination = api_request("POST", "/destinations", {
        "name": dest_name,
        "type": "MOCK_API",
        "config": {
            "rate_limit": 2,
            "rate_limit_period": "minute"
        }
    })
    destination_id = destination["id"]
    print(f"Created destination {destination_id}")

    # 3. Create connection
    conn_name = f"rl-conn-{run_id}"
    print(f"Creating connection {conn_name}...")
    connection = api_request("POST", "/connections", {
        "name": conn_name,
        "source_id": source_id,
        "destination_id": destination_id
    })
    connection_id = connection["id"]
    print(f"Created connection {connection_id}")

    # 4. Publish exactly 5 events
    print("Publishing 5 events to the source URL in quick succession...")
    for i in range(1, 6):
        payload = json.dumps({"event_num": i, "timestamp": str(datetime.utcnow())}).encode('utf-8')
        req = urllib.request.Request(source_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "curl/8.7.1"}, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                res = response.read().decode('utf-8')
                print(f"Published event {i}: {res}")
        except Exception as e:
            print(f"Failed to publish event {i}: {e}")
            raise e
        time.sleep(0.1)

    # 5. Poll events until exactly 5 events are SUCCESSFUL
    print("Polling events until all 5 are SUCCESSFUL...")
    start_time = time.time()
    successful_events = []
    
    # Wait up to 5 minutes (300 seconds)
    while time.time() - start_time < 300:
        try:
            # Poll events filtered by destination_id
            events_res = api_request("GET", f"/events?destination_id={destination_id}")
            if events_res and "models" in events_res:
                models = events_res["models"]
                
                # Let's write a simpler status print
                statuses = []
                temp_successful = []
                for ev in models:
                    status = ev.get("status")
                    statuses.append(status)
                    if status == "SUCCESSFUL":
                        temp_successful.append(ev)
                
                print(f"Found {len(models)} events. Statuses: {statuses}")
                
                if len(temp_successful) == 5:
                    successful_events = temp_successful
                    print("All 5 events are SUCCESSFUL!")
                    break
            else:
                print("No events found yet...")
        except Exception as e:
            print(f"Error polling events: {e}")
        
        time.sleep(10)
    
    if len(successful_events) < 5:
        print(f"Error: Only {len(successful_events)} events reached SUCCESSFUL status within timeout.")
        sys.exit(1)

    # Sort successful events by successful_at
    # Hookdeck successful_at is ISO format string, e.g. "2026-06-11T08:26:25.232Z"
    # Let's parse them to datetime objects for accurate sorting and verification
    def parse_time(t_str):
        # Remove Z and replace with +00:00 or parse manually
        if t_str.endswith('Z'):
            t_str = t_str[:-1] + '+00:00'
        return datetime.fromisoformat(t_str)

    sorted_events = sorted(successful_events, key=lambda x: parse_time(x['successful_at']))
    
    timestamps = [parse_time(ev['successful_at']) for ev in sorted_events]
    event_ids = [ev['id'] for ev in sorted_events]
    
    print("\nSuccessful Events Timeline:")
    for ev in sorted_events:
        print(f"Event ID: {ev['id']}, Status: {ev['status']}, Successful At: {ev['successful_at']}")
        
    # Calculate metrics
    total_spread = (timestamps[-1] - timestamps[0]).total_seconds()
    print(f"Total spread: {total_spread} seconds")
    
    gaps = []
    for i in range(len(timestamps) - 1):
        gap = (timestamps[i+1] - timestamps[i]).total_seconds()
        gaps.append(gap)
        print(f"Gap {i+1}: {gap} seconds")
        
    max_gap = max(gaps) if gaps else 0
    print(f"Max consecutive gap: {max_gap} seconds")
    
    # Write to log file
    log_path = "/home/user/hookdeck-task/output.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "w") as f:
        f.write(f"Destination ID: {destination_id}\n")
        f.write(f"Source ID: {source_id}\n")
        f.write(f"Connection ID: {connection_id}\n")
        f.write(f"Event IDs: {','.join(event_ids)}\n")
        
    print(f"\nSaved results to {log_path}")

if __name__ == "__main__":
    run()
