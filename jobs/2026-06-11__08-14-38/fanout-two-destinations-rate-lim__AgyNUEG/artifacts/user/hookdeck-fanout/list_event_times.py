import os
import requests
import json
from datetime import datetime

api_key = os.environ.get("HOOKDECK_API_KEY")
state_path = "/home/user/hookdeck-fanout/state.json"
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
    return datetime.fromisoformat(ts_str)

print("=== Fast Destination Events ===")
r = requests.get(f"{base_url}/events?destination_id={fast_dest_id}", headers=headers)
fast_events = [e for e in r.json().get("models", []) if e.get("status") == "SUCCESSFUL"]
fast_events.sort(key=lambda x: parse_iso(x.get("successful_at")))
for idx, e in enumerate(fast_events):
    print(f"  {idx+1}: ID: {e.get('id')}, successful_at: {e.get('successful_at')}")

print("\n=== Slow Destination Events ===")
r = requests.get(f"{base_url}/events?destination_id={slow_dest_id}", headers=headers)
slow_events = [e for e in r.json().get("models", []) if e.get("status") == "SUCCESSFUL"]
slow_events.sort(key=lambda x: parse_iso(x.get("successful_at")))
for idx, e in enumerate(slow_events):
    print(f"  {idx+1}: ID: {e.get('id')}, successful_at: {e.get('successful_at')}")
