import os
import requests
import json

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

r = requests.get(f"{base_url}/destinations/{fast_dest_id}", headers=headers)
print("Fast Destination Config:")
print(json.dumps(r.json(), indent=2))

r = requests.get(f"{base_url}/destinations/{slow_dest_id}", headers=headers)
print("\nSlow Destination Config:")
print(json.dumps(r.json(), indent=2))
