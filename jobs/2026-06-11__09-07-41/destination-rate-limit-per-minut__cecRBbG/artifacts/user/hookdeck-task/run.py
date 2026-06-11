import os
import time
import json
import urllib.request
import urllib.error

api_key = os.environ.get('HOOKDECK_API_KEY')
run_id = os.environ.get('ZEALT_RUN_ID')

if not api_key or not run_id:
    raise ValueError("Missing HOOKDECK_API_KEY or ZEALT_RUN_ID")

api_base = "https://api.hookdeck.com/2025-07-01"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def make_request(url, method="GET", data=None, headers=headers):
    req = urllib.request.Request(url, method=method, headers=headers)
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error {e.code} on {url}:")
        print(e.read().decode('utf-8'))
        raise

print("Creating destination...")
dest_name = f"rl-dest-{run_id}"
dest_payload = {
    "name": dest_name,
    "type": "MOCK_API",
    "config": {
        "rate_limit": 2,
        "rate_limit_period": "minute"
    }
}
dest_resp = make_request(f"{api_base}/destinations", method="POST", data=dest_payload)
dest_id = dest_resp['id']
print(f"Destination ID: {dest_id}")

print("Creating source...")
src_name = f"rl-src-{run_id}"
src_payload = {
    "name": src_name,
    "type": "WEBHOOK"
}
src_resp = make_request(f"{api_base}/sources", method="POST", data=src_payload)
src_id = src_resp['id']
src_url = src_resp['url']
print(f"Source ID: {src_id}")

print("Creating connection...")
conn_name = f"rl-conn-{run_id}"
conn_payload = {
    "name": conn_name,
    "source_id": src_id,
    "destination_id": dest_id
}
conn_resp = make_request(f"{api_base}/connections", method="POST", data=conn_payload)
conn_id = conn_resp['id']
print(f"Connection ID: {conn_id}")

print("Publishing 5 events...")
for i in range(5):
    make_request(src_url, method="POST", data={"test": i}, headers={"Content-Type": "application/json"})
print("Published!")

print("Polling for successful events...")
successful_events = []
while len(successful_events) < 5:
    time.sleep(10)
    events_resp = make_request(f"{api_base}/events?destination_id={dest_id}&status=SUCCESSFUL&limit=10")
    items = events_resp.get('models', [])
    successful_events = items
    print(f"Found {len(successful_events)} successful events")

event_ids = [e['id'] for e in successful_events]

log_path = "/home/user/hookdeck-task/output.log"
with open(log_path, "w") as f:
    f.write(f"Destination ID: {dest_id}\n")
    f.write(f"Source ID: {src_id}\n")
    f.write(f"Connection ID: {conn_id}\n")
    f.write(f"Event IDs: {','.join(event_ids)}\n")

print(f"Done. Log written to {log_path}")
