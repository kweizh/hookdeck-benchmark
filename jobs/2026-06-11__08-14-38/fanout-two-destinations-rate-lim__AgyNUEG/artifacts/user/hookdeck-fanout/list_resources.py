import os
import requests
import json

api_key = os.environ.get("HOOKDECK_API_KEY")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
base_url = "https://api.hookdeck.com/2025-07-01"

print("Listing sources...")
r = requests.get(f"{base_url}/sources", headers=headers)
print("Sources Status:", r.status_code)
if r.status_code == 200:
    sources = r.json().get("models", [])
    for s in sources:
        print(f" - {s.get('name')}: {s.get('id')}")

print("\nListing destinations...")
r = requests.get(f"{base_url}/destinations", headers=headers)
print("Destinations Status:", r.status_code)
if r.status_code == 200:
    destinations = r.json().get("models", [])
    for d in destinations:
        print(f" - {d.get('name')}: {d.get('id')} Config: {d.get('config')}")

print("\nListing connections...")
r = requests.get(f"{base_url}/connections", headers=headers)
print("Connections Status:", r.status_code)
if r.status_code == 200:
    connections = r.json().get("models", [])
    for c in connections:
        print(f" - {c.get('name')}: {c.get('id')} Source: {c.get('source', {}).get('id')} -> Dest: {c.get('destination', {}).get('id')}")
