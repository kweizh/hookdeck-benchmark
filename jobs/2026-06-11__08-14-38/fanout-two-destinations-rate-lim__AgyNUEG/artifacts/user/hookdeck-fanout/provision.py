import os
import requests
import json
import sys

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

if not api_key or not run_id:
    print("Error: HOOKDECK_API_KEY or ZEALT_RUN_ID not set")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
base_url = "https://api.hookdeck.com/2025-07-01"

source_name = f"fanout-src-{run_id}"
fast_dest_name = f"fanout-fast-{run_id}"
slow_dest_name = f"fanout-slow-{run_id}"
fast_conn_name = f"fanout-fast-conn-{run_id}"
slow_conn_name = f"fanout-slow-conn-{run_id}"

# 1. Clean up existing resources to avoid conflicts
print("Cleaning up existing connections...")
r = requests.get(f"{base_url}/connections", headers=headers)
if r.status_code == 200:
    for conn in r.json().get("models", []):
        if conn.get("name") in [fast_conn_name, slow_conn_name]:
            conn_id = conn.get("id")
            print(f"Deleting connection {conn.get('name')} ({conn_id})...")
            requests.delete(f"{base_url}/connections/{conn_id}", headers=headers)

print("Cleaning up existing destinations...")
r = requests.get(f"{base_url}/destinations", headers=headers)
if r.status_code == 200:
    for dest in r.json().get("models", []):
        if dest.get("name") in [fast_dest_name, slow_dest_name]:
            dest_id = dest.get("id")
            print(f"Deleting destination {dest.get('name')} ({dest_id})...")
            requests.delete(f"{base_url}/destinations/{dest_id}", headers=headers)

print("Cleaning up existing sources...")
r = requests.get(f"{base_url}/sources", headers=headers)
if r.status_code == 200:
    for src in r.json().get("models", []):
        if src.get("name") == source_name:
            src_id = src.get("id")
            print(f"Deleting source {src.get('name')} ({src_id})...")
            requests.delete(f"{base_url}/sources/{src_id}", headers=headers)


# 2. Create Source
print(f"\nCreating source {source_name}...")
src_payload = {
    "name": source_name,
    "type": "WEBHOOK"
}
r = requests.post(f"{base_url}/sources", headers=headers, json=src_payload)
print("Source creation status:", r.status_code)
if r.status_code not in [200, 201]:
    print("Error details:", r.text)
    sys.exit(1)
source_data = r.json()
source_id = source_data.get("id")
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
r = requests.post(f"{base_url}/destinations", headers=headers, json=fast_dest_payload)
print("Fast Destination creation status:", r.status_code)
if r.status_code not in [200, 201]:
    print("Error details:", r.text)
    sys.exit(1)
fast_dest_data = r.json()
fast_dest_id = fast_dest_data.get("id")
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
r = requests.post(f"{base_url}/destinations", headers=headers, json=slow_dest_payload)
print("Slow Destination creation status:", r.status_code)
if r.status_code not in [200, 201]:
    print("Error details:", r.text)
    sys.exit(1)
slow_dest_data = r.json()
slow_dest_id = slow_dest_data.get("id")
print(f"Created Slow Destination ID: {slow_dest_id}")


# 5. Create Fast Connection
print(f"\nCreating fast connection {fast_conn_name}...")
fast_conn_payload = {
    "name": fast_conn_name,
    "source_id": source_id,
    "destination_id": fast_dest_id
}
r = requests.post(f"{base_url}/connections", headers=headers, json=fast_conn_payload)
print("Fast Connection creation status:", r.status_code)
if r.status_code not in [200, 201]:
    print("Error details:", r.text)
    sys.exit(1)
fast_conn_data = r.json()
fast_conn_id = fast_conn_data.get("id")
print(f"Created Fast Connection ID: {fast_conn_id}")


# 6. Create Slow Connection
print(f"\nCreating slow connection {slow_conn_name}...")
slow_conn_payload = {
    "name": slow_conn_name,
    "source_id": source_id,
    "destination_id": slow_dest_id
}
r = requests.post(f"{base_url}/connections", headers=headers, json=slow_conn_payload)
print("Slow Connection creation status:", r.status_code)
if r.status_code not in [200, 201]:
    print("Error details:", r.text)
    sys.exit(1)
slow_conn_data = r.json()
slow_conn_id = slow_conn_data.get("id")
print(f"Created Slow Connection ID: {slow_conn_id}")

print("\nAll resources successfully provisioned!")
print(f"source_id: {source_id}")
print(f"fast_destination_id: {fast_dest_id}")
print(f"slow_destination_id: {slow_dest_id}")
print(f"fast_connection_id: {fast_conn_id}")
print(f"slow_connection_id: {slow_conn_id}")

# Write to state file
state = {
    "source_id": source_id,
    "fast_destination_id": fast_dest_id,
    "slow_destination_id": slow_dest_id,
    "fast_connection_id": fast_conn_id,
    "slow_connection_id": slow_conn_id
}
with open("/home/user/hookdeck-fanout/state.json", "w") as f:
    json.dump(state, f, indent=2)
print("Wrote state to state.json")
