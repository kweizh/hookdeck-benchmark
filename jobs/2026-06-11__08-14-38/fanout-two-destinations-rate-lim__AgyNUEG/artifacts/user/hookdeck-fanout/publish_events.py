import os
import requests
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

api_key = os.environ.get("HOOKDECK_API_KEY")
if not api_key:
    print("Error: HOOKDECK_API_KEY not set")
    sys.exit(1)

# Load state
state_path = "/home/user/hookdeck-fanout/state.json"
if not os.path.exists(state_path):
    print("Error: state.json not found. Run provision.py first.")
    sys.exit(1)

with open(state_path) as f:
    state = json.load(f)

source_id = state["source_id"]
print(f"Publishing exactly 12 events to Source ID: {source_id}...")

publish_url = "https://hkdk.events/v1/publish"

# We create a session and mount an adapter with a pool size of 20
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount('https://', adapter)

# Pre-warm connections without X-Hookdeck-Source-Id so they are rejected but warm up the pool
print("Pre-warming 12 keep-alive connections in the pool...")
def warm(i):
    try:
        requests_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        session.post(publish_url, headers=requests_headers, json={})
    except Exception:
        pass

with ThreadPoolExecutor(max_workers=12) as executor:
    list(executor.map(warm, range(12)))

# Align the start of the publishing burst to the end of the current second window
print("Waiting for the clock second boundary alignment...")
while True:
    now = time.time()
    frac = now - int(now)
    # We want to start publishing at 0.93 seconds into the current second
    if 0.93 <= frac <= 0.96:
        break
    time.sleep(0.001)

print(f"Starting tight concurrent publish at fraction {time.time() - int(time.time()):.4f}...")
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
        return i, r.status_code, r.text
    except Exception as e:
        return i, 0, str(e)

with ThreadPoolExecutor(max_workers=12) as executor:
    results = list(executor.map(send_request, range(12)))

end_time = time.time()

success_count = 0
for i, status_code, text in sorted(results):
    if status_code in [200, 201, 202]:
        success_count += 1
        print(f"Event {i+1} published. Status: {status_code}")
    else:
        print(f"Failed event {i+1}. Status: {status_code}, Response: {text}")

print(f"\nPublished {success_count}/12 events in {end_time - start_time:.4f} seconds.")
if success_count != 12:
    print("Error: Not all 12 events were successfully published.")
    sys.exit(1)
