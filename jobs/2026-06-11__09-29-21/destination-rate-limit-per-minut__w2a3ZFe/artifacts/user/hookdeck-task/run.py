#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
from datetime import datetime, timezone

API_KEY = os.environ["HOOKDECK_API_KEY"]
RUN_ID = os.environ["ZEALT_RUN_ID"]
API_BASE = "https://api.hookdeck.com/2025-07-01"
PUBLISH_URL = "https://hkdk.events/v1/publish"
LOG_FILE = "/home/user/hookdeck-task/output.log"

SRC_NAME = f"rl-src-{RUN_ID}"
DEST_NAME = f"rl-dest-{RUN_ID}"
CONN_NAME = f"rl-conn-{RUN_ID}"

def api_call(method, url, data=None):
    """Make an API call to Hookdeck."""
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {API_KEY}",
           "-H", "Content-Type: application/json"]
    if data:
        cmd.extend(["-d", json.dumps(data)])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def find_resource(endpoint, name):
    """Find a resource by name using list endpoint."""
    resp = api_call("GET", f"{API_BASE}/{endpoint}")
    models = resp.get("models", resp.get("data", []))
    for m in models:
        if m.get("name") == name:
            return m
    return None

def parse_iso_timestamp(ts):
    """Parse ISO 8601 timestamp to epoch seconds."""
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    dt = datetime.fromisoformat(ts)
    return int(dt.timestamp())

print("=== Hookdeck Rate Limit Task ===")
print(f"RUN_ID: {RUN_ID}")

# ---- 1. Create or find Source ----
print("Creating/finding source...")
existing_src = find_resource("sources", SRC_NAME)
if existing_src:
    src_id = existing_src["id"]
    src_url = existing_src.get("url", "")
    print(f"  Found existing source: {src_id}")
else:
    src_resp = api_call("POST", f"{API_BASE}/sources", {"name": SRC_NAME})
    if "id" not in src_resp:
        print(f"  ERROR creating source: {src_resp}")
        sys.exit(1)
    src_id = src_resp["id"]
    src_url = src_resp.get("url", "")
    print(f"  Created source: {src_id}")

# ---- 2. Create or find Destination ----
print("Creating/finding destination...")
existing_dest = find_resource("destinations", DEST_NAME)
if existing_dest:
    dest_id = existing_dest["id"]
    print(f"  Found existing destination: {dest_id}")
else:
    dest_resp = api_call("POST", f"{API_BASE}/destinations", {
        "name": DEST_NAME,
        "type": "MOCK_API",
        "config": {
            "rate_limit": 2,
            "rate_limit_period": "minute"
        }
    })
    if "id" not in dest_resp:
        print(f"  ERROR creating destination: {dest_resp}")
        sys.exit(1)
    dest_id = dest_resp["id"]
    print(f"  Created destination: {dest_id}")

# ---- 3. Create or find Connection ----
print("Creating/finding connection...")
existing_conn = find_resource("connections", CONN_NAME)
if existing_conn:
    conn_id = existing_conn["id"]
    print(f"  Found existing connection: {conn_id}")
else:
    conn_resp = api_call("POST", f"{API_BASE}/connections", {
        "name": CONN_NAME,
        "source_id": src_id,
        "destination_id": dest_id
    })
    if "id" not in conn_resp:
        print(f"  ERROR creating connection: {conn_resp}")
        sys.exit(1)
    conn_id = conn_resp["id"]
    print(f"  Created connection: {conn_id}")

# ---- 4. Publish 5 events ----
print("Publishing 5 events...")
for i in range(1, 6):
    pub_resp = api_call("POST", PUBLISH_URL, {
        "source_id": src_id,
        "data": {"event_number": i, "test": "rate-limit"}
    })
    evt_id = pub_resp.get("id", pub_resp.get("event_id", ""))
    print(f"  Published event {i}: {evt_id}")

# ---- 5. Poll for SUCCESSFUL events ----
print("Waiting for all 5 events to reach SUCCESSFUL status...")
max_wait = 300  # 5 minutes max
elapsed = 0
interval = 15
successful_events = []

while elapsed < max_wait:
    events_resp = api_call("GET", f"{API_BASE}/events?destination_id={dest_id}&status=SUCCESSFUL")
    events_data = events_resp.get("data", [])
    print(f"  [{elapsed}s] Successful events: {len(events_data)} / 5")
    
    if len(events_data) >= 5:
        successful_events = events_data[:5]
        break
    
    time.sleep(interval)
    elapsed += interval

if not successful_events or len(successful_events) < 5:
    print("ERROR: Timed out waiting for events to become SUCCESSFUL")
    # Print whatever events we have for debugging
    events_resp = api_call("GET", f"{API_BASE}/events?destination_id={dest_id}")
    all_events = events_resp.get("data", [])
    for e in all_events[:10]:
        print(f"  Event {e.get('id')}: status={e.get('status')}")
    sys.exit(1)

# ---- 6. Sort events by successful_at and extract info ----
successful_events.sort(key=lambda e: e.get("successful_at", ""))
event_ids = [e["id"] for e in successful_events]
timestamps = [e["successful_at"] for e in successful_events]

print("\nEvent IDs and timestamps:")
for i, (eid, ts) in enumerate(zip(event_ids, timestamps)):
    print(f"  {i+1}. {eid} @ {ts}")

# Calculate spread
first_epoch = parse_iso_timestamp(timestamps[0])
last_epoch = parse_iso_timestamp(timestamps[-1])
spread = last_epoch - first_epoch
print(f"\nSpread between first and last: {spread} seconds")

# Check consecutive gaps
gaps = []
for i in range(1, len(timestamps)):
    gap = parse_iso_timestamp(timestamps[i]) - parse_iso_timestamp(timestamps[i-1])
    gaps.append(gap)
    print(f"  Gap {i}: {gap} seconds")

max_gap = max(gaps) if gaps else 0
has_gap_gt_25 = any(g > 25 for g in gaps)

print(f"Max consecutive gap: {max_gap} seconds")
print(f"Any gap > 25s: {has_gap_gt_25}")

# ---- 7. Write log file ----
event_ids_str = ",".join(event_ids)
with open(LOG_FILE, "w") as f:
    f.write(f"Destination ID: {dest_id}\n")
    f.write(f"Source ID: {src_id}\n")
    f.write(f"Connection ID: {conn_id}\n")
    f.write(f"Event IDs: {event_ids_str}\n")

print(f"\n=== Log file written to {LOG_FILE} ===")
with open(LOG_FILE) as f:
    print(f.read())

print("\n=== Verification ===")
print(f"Spread >= 60s: {'PASS' if spread >= 60 else 'FAIL'} ({spread} seconds)")
print(f"Consecutive gap > 25s: {'PASS' if has_gap_gt_25 else 'FAIL'}")