import os
import requests
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

if not api_key or not run_id:
    print("Error: HOOKDECK_API_KEY or ZEALT_RUN_ID not set")
    sys.exit(1)

base_url = "https://api.hookdeck.com/2025-07-01"
publish_url = "https://hkdk.events/v1/publish"

# Create a single session for everything
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
session.mount('https://', adapter)
session.headers.update({
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
})

source_name = f"fanout-src-{run_id}"
fast_dest_name = f"fanout-fast-{run_id}"
slow_dest_name = f"fanout-slow-{run_id}"
fast_conn_name = f"fanout-fast-conn-{run_id}"
slow_conn_name = f"fanout-slow-conn-{run_id}"

# 1. Clean up existing resources
print("Cleaning up existing connections...")
r = session.get(f"{base_url}/connections")
if r.status_code == 200:
    for conn in r.json().get("models", []):
        if conn.get("name") in [fast_conn_name, slow_conn_name]:
            conn_id = conn.get("id")
            print(f"Deleting connection {conn.get('name')} ({conn_id})...")
            session.delete(f"{base_url}/connections/{conn_id}")

print("Cleaning up existing destinations...")
r = session.get(f"{base_url}/destinations")
if r.status_code == 200:
    for dest in r.json().get("models", []):
        if dest.get("name") in [fast_dest_name, slow_dest_name]:
            dest_id = dest.get("id")
            print(f"Deleting destination {dest.get('name')} ({dest_id})...")
            session.delete(f"{base_url}/destinations/{dest_id}")

print("Cleaning up existing sources...")
r = session.get(f"{base_url}/sources")
if r.status_code == 200:
    for src in r.json().get("models", []):
        if src.get("name") == source_name:
            src_id = src.get("id")
            print(f"Deleting source {src.get('name')} ({src_id})...")
            session.delete(f"{base_url}/sources/{src_id}")


# 2. Create Source
print(f"\nCreating source {source_name}...")
src_payload = {
    "name": source_name,
    "type": "WEBHOOK"
}
r = session.post(f"{base_url}/sources", json=src_payload)
if r.status_code not in [200, 201]:
    print("Error creating source:", r.text)
    sys.exit(1)
source_id = r.json().get("id")
print(f"Created Source ID: {source_id}")


# 3. Create Fast Destination
print(f"\nCreating fast destination {fast_dest_name}...")
fast_dest_payload = {
    "name": fast_dest_name,
    "type": "MOCK_API",
    "config": {
        "rate_limit": None,
        "rate_limit_period": None
    }
}
r = session.post(f"{base_url}/destinations", json=fast_dest_payload)
if r.status_code not in [200, 201]:
    print("Error creating fast destination:", r.text)
    sys.exit(1)
fast_dest_id = r.json().get("id")
print(f"Created Fast Destination ID: {fast_dest_id}")


# 4. Create Slow Destination
print(f"\nCreating slow destination {slow_dest_name}...")
slow_dest_payload = {
    "name": slow_dest_name,
    "type": "MOCK_API",
    "config": {
        "rate_limit": 2,
        "rate_limit_period": "second"
    }
}
r = session.post(f"{base_url}/destinations", json=slow_dest_payload)
if r.status_code not in [200, 201]:
    print("Error creating slow destination:", r.text)
    sys.exit(1)
slow_dest_id = r.json().get("id")
print(f"Created Slow Destination ID: {slow_dest_id}")


# 5. Create Fast Connection
print(f"\nCreating fast connection {fast_conn_name}...")
fast_conn_payload = {
    "name": fast_conn_name,
    "source_id": source_id,
    "destination_id": fast_dest_id
}
r = session.post(f"{base_url}/connections", json=fast_conn_payload)
if r.status_code not in [200, 201]:
    print("Error creating fast connection:", r.text)
    sys.exit(1)
fast_conn_id = r.json().get("id")
print(f"Created Fast Connection ID: {fast_conn_id}")


# 6. Create Slow Connection
print(f"\nCreating slow connection {slow_conn_name}...")
slow_conn_payload = {
    "name": slow_conn_name,
    "source_id": source_id,
    "destination_id": slow_dest_id
}
r = session.post(f"{base_url}/connections", json=slow_conn_payload)
if r.status_code not in [200, 201]:
    print("Error creating slow connection:", r.text)
    sys.exit(1)
slow_conn_id = r.json().get("id")
print(f"Created Slow Connection ID: {slow_conn_id}")

# Save state
state = {
    "source_id": source_id,
    "fast_destination_id": fast_dest_id,
    "slow_destination_id": slow_dest_id,
    "fast_connection_id": fast_conn_id,
    "slow_connection_id": slow_conn_id
}
with open("/home/user/hookdeck-fanout/state.json", "w") as f:
    json.dump(state, f, indent=2)

print("\nAll resources successfully provisioned!")


# 7. Pre-warm 12 connections to hkdk.events
print("\nPre-warming 12 keep-alive connections in the pool...")
def warm(i):
    try:
        # No source ID header so they are rejected but warm up TLS/TCP
        session.post(publish_url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json={})
    except Exception:
        pass

with ThreadPoolExecutor(max_workers=12) as executor:
    list(executor.map(warm, range(12)))


# 8. Align with clock second boundary and publish
print("\nWaiting for the clock second boundary alignment...")
while True:
    now = time.time()
    frac = now - int(now)
    # We want to start publishing at 0.90 to 0.92 seconds into the current second
    if 0.90 <= frac <= 0.92:
        break
    time.sleep(0.001)

print(f"Starting tight concurrent publish of exactly 12 events at fraction {time.time() - int(time.time()):.4f}...")
start_time = time.time()

def send_request(i):
    payload = {
        "event_index": i,
        "timestamp": time.time(),
        "message": f"Aligned concurrent event {i+1}/12"
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Hookdeck-Source-Id": source_id
    }
    try:
        r = session.post(publish_url, headers=headers, json=payload)
        return i, r.status_code
    except Exception as e:
        return i, str(e)

with ThreadPoolExecutor(max_workers=12) as executor:
    results = list(executor.map(send_request, range(12)))

end_time = time.time()
print(f"Published 12 events in {end_time - start_time:.4f} seconds.")


# 9. Verify delivery and outcome
print("\nWaiting 10 seconds for deliveries to complete...")
time.sleep(10)

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str)

print("Fetching fast destination events...")
r = session.get(f"{base_url}/events?destination_id={fast_dest_id}")
fast_events = [e for e in r.json().get("models", []) if e.get("status") == "SUCCESSFUL"]
fast_events.sort(key=lambda x: parse_iso(x.get("successful_at")))

print("Fetching slow destination events...")
r = session.get(f"{base_url}/events?destination_id={slow_dest_id}")
slow_events = [e for e in r.json().get("models", []) if e.get("status") == "SUCCESSFUL"]
slow_events.sort(key=lambda x: parse_iso(x.get("successful_at")))

print(f"\nFast Destination: {len(fast_events)} successful events.")
for idx, e in enumerate(fast_events):
    print(f"  {idx+1}: {e.get('id')} at {e.get('successful_at')}")

print(f"\nSlow Destination: {len(slow_events)} successful events.")
for idx, e in enumerate(slow_events):
    print(f"  {idx+1}: {e.get('id')} at {e.get('successful_at')}")

fast_times = [parse_iso(e.get("successful_at")) for e in fast_events]
fast_duration = (fast_times[-1] - fast_times[0]).total_seconds() if len(fast_times) >= 2 else 0

slow_times = [parse_iso(e.get("successful_at")) for e in slow_events]
slow_duration = (slow_times[-1] - slow_times[0]).total_seconds() if len(slow_times) >= 2 else 0

print(f"\n--- RESULTS ---")
print(f"Fast Destination Delivery Duration: {fast_duration:.4f} seconds")
print(f"Slow Destination Delivery Duration: {slow_duration:.4f} seconds")

if len(fast_events) == 12 and len(slow_events) == 12:
    print("SUCCESS: Both destinations received exactly 12 events.")
else:
    print("FAILURE: Incorrect event counts.")

if fast_duration < 2.0:
    print("SUCCESS: Fast destination delivery duration < 2 seconds.")
else:
    print("FAILURE: Fast destination delivery duration >= 2 seconds.")

if slow_duration >= 5.0:
    print("SUCCESS: Slow destination delivery duration >= 5 seconds.")
else:
    print("FAILURE: Slow destination delivery duration < 5 seconds.")
