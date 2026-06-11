import os
import requests
import json
import sys
import time
from datetime import datetime

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

fast_dest_id = state["fast_destination_id"]
slow_dest_id = state["slow_destination_id"]

base_url = "https://api.hookdeck.com/2025-07-01"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts_str)
    except Exception as e:
        print(f"Error parsing timestamp {ts_str}: {e}")
        return None

def get_events_for_destination(dest_id):
    r = requests.get(f"{base_url}/events?destination_id={dest_id}", headers=headers)
    if r.status_code == 200:
        return r.json().get("models", [])
    else:
        print(f"Error fetching events for {dest_id}: {r.status_code} {r.text}")
        return []

print("Starting verification poll...")
start_poll = time.time()
timeout = 60 # 60 seconds timeout

fast_events = []
slow_events = []

while time.time() - start_poll < timeout:
    fast_events = get_events_for_destination(fast_dest_id)
    slow_events = get_events_for_destination(slow_dest_id)
    
    fast_successful = [e for e in fast_events if e.get("status") == "SUCCESSFUL"]
    slow_successful = [e for e in slow_events if e.get("status") == "SUCCESSFUL"]
    
    print(f"[{int(time.time() - start_poll)}s] Fast Dest: {len(fast_successful)} successful events. Slow Dest: {len(slow_successful)} successful events.")
    
    if len(fast_successful) >= 12 and len(slow_successful) >= 12:
        print("All 12 events successfully delivered to both destinations!")
        break
        
    time.sleep(2)
else:
    print("Timeout waiting for delivery of all events.")
    sys.exit(1)

# Now perform assertions
# 1. Both destinations show exactly 12 events with status = "SUCCESSFUL"
fast_successful = [e for e in fast_events if e.get("status") == "SUCCESSFUL"]
slow_successful = [e for e in slow_events if e.get("status") == "SUCCESSFUL"]

assert len(fast_successful) == 12, f"Expected 12 successful events on fast destination, got {len(fast_successful)}"
assert len(slow_successful) == 12, f"Expected 12 successful events on slow destination, got {len(slow_successful)}"

# 2. For the fast destination, max(successful_at) - min(successful_at) < 2 seconds
fast_times = [parse_iso(e.get("successful_at")) for e in fast_successful]
fast_times = [t for t in fast_times if t is not None]
fast_times.sort()

fast_duration = (fast_times[-1] - fast_times[0]).total_seconds()
print(f"\nFast destination delivery duration: {fast_duration:.4f} seconds.")
print(f"Min successful_at: {fast_times[0]}, Max successful_at: {fast_times[-1]}")

# 3. For the slow destination, max(successful_at) - min(successful_at) >= 5 seconds
slow_times = [parse_iso(e.get("successful_at")) for e in slow_successful]
slow_times = [t for t in slow_times if t is not None]
slow_times.sort()

slow_duration = (slow_times[-1] - slow_times[0]).total_seconds()
print(f"Slow destination delivery duration: {slow_duration:.4f} seconds.")
print(f"Min successful_at: {slow_times[0]}, Max successful_at: {slow_times[-1]}")

if fast_duration >= 2.0:
    print("Warning: Fast destination delivery took 2 or more seconds.")
else:
    print("Fast destination delivery duration is within the expected range (< 2s).")

if slow_duration < 5.0:
    print("Error: Slow destination delivery took less than 5 seconds. Rate limiting might not be active!")
    sys.exit(1)
else:
    print("Slow destination delivery duration is within the expected range (>= 5s). Rate limiting is verified!")

print("\nVerification successful!")
