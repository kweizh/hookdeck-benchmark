import os
import requests
import json
import time

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Connection A details
conn_a_id = "web_Sp1zO5QmkIx3"
source_a_url = "https://hkdk.events/eaqws0fris7o61"

print("1. Triggering Event A by posting to source A...")
trigger_res = requests.post(source_a_url, json={"trigger": "event-a", "run_id": run_id})
print("Trigger status:", trigger_res.status_code)
print("Trigger response:", trigger_res.text)

# Poll for the event to be created
print("\n2. Polling for the event to be created in Hookdeck...")
event_id = None
for i in range(30):
    res = requests.get(f"https://api.hookdeck.com/2025-07-01/events?webhook_id={conn_a_id}", headers=headers)
    if res.status_code == 200:
        events = res.json().get("models", [])
        if events:
            event_id = events[0]["id"]
            print(f"Found Event A ID: {event_id}")
            break
    else:
        print(f"Error fetching events: {res.status_code} - {res.text}")
    time.sleep(2)

if not event_id:
    print("Failed to find Event A ID!")
    exit(1)

# Poll for attempts to reach at least 1
def wait_for_attempts(target_count, max_wait_sec=120):
    print(f"Waiting for attempts to reach at least {target_count}...")
    start_time = time.time()
    while time.time() - start_time < max_wait_sec:
        res = requests.get(f"https://api.hookdeck.com/2025-07-01/attempts?event_id={event_id}", headers=headers)
        if res.status_code == 200:
            attempts = res.json().get("models", [])
            print(f"Current attempts count: {len(attempts)}")
            for att in attempts:
                print(f"  Attempt #{att.get('attempt_number')}: status={att.get('status')}, response_status={att.get('response_status')}")
            if len(attempts) >= target_count:
                return attempts
        else:
            print(f"Error fetching attempts: {res.status_code} - {res.text}")
        time.sleep(3)
    raise TimeoutError(f"Timed out waiting for attempts to reach {target_count}")

# Wait for the first attempt to complete (it should fail with 500)
attempts = wait_for_attempts(1)

# Now manually trigger a retry to get to attempt 2
print("\n3. Triggering manual retry for attempt 2...")
retry_res = requests.post(f"https://api.hookdeck.com/2025-07-01/events/{event_id}/retry", headers=headers, json={})
print("Retry 2 response:", retry_res.status_code, retry_res.text)

# Wait for attempt 2 to be recorded
attempts = wait_for_attempts(2)

# Trigger another manual retry to get to attempt 3
print("\n4. Triggering manual retry for attempt 3...")
retry_res = requests.post(f"https://api.hookdeck.com/2025-07-01/events/{event_id}/retry", headers=headers, json={})
print("Retry 3 response:", retry_res.status_code, retry_res.text)

# Wait for attempt 3 to be recorded
attempts = wait_for_attempts(3)

print("\nEvent A has accumulated 3 attempts!")
