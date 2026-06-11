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
dest_a_id = "des_bBH5ldsfGdcG"
source_a_url = "https://hkdk.events/eaqws0fris7o61"

print("1. Triggering a NEW Event A by posting to source A...")
trigger_res = requests.post(source_a_url, json={"trigger": "event-a-v2", "run_id": run_id})
print("Trigger status:", trigger_res.status_code)
print("Trigger response:", trigger_res.text)

# Poll for the new event to be created (most recent one)
print("\n2. Polling for the new event to be created in Hookdeck...")
event_id = None
for i in range(30):
    res = requests.get(f"https://api.hookdeck.com/2025-07-01/events?webhook_id={conn_a_id}&order_by=created_at&dir=desc", headers=headers)
    if res.status_code == 200:
        events = res.json().get("models", [])
        if events:
            # We want the one triggered by "event-a-v2"
            for ev in events:
                body = ev.get("body", {})
                # body might be stringified JSON or dict
                if isinstance(body, str):
                    try:
                        body = json.loads(body)
                    except:
                        pass
                if isinstance(body, dict) and body.get("trigger") == "event-a-v2":
                    event_id = ev["id"]
                    print(f"Found NEW Event A ID: {event_id}")
                    break
            if event_id:
                break
    else:
        print(f"Error fetching events: {res.status_code} - {res.text}")
    time.sleep(2)

if not event_id:
    print("Failed to find Event A ID!")
    exit(1)

# Poll for attempts to reach a certain target count
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
                # Also make sure the latest attempt is not in-flight (status is either SUCCESSFUL or FAILED)
                # Filter out in-flight if any
                completed_attempts = [a for a in attempts if a.get("status") in ["SUCCESSFUL", "FAILED"]]
                if len(completed_attempts) >= target_count:
                    return completed_attempts
        else:
            print(f"Error fetching attempts: {res.status_code} - {res.text}")
        time.sleep(3)
    raise TimeoutError(f"Timed out waiting for attempts to reach {target_count}")

# Wait for the first attempt to complete (it should fail with 500)
attempts = wait_for_attempts(1)

# Trigger manual retry for attempt 2
print("\n3. Triggering manual retry for attempt 2...")
retry_res = requests.post(f"https://api.hookdeck.com/2025-07-01/events/{event_id}/retry", headers=headers, json={})
print("Retry 2 response:", retry_res.status_code)

# Wait for attempt 2 to be recorded
attempts = wait_for_attempts(2)

# Trigger manual retry for attempt 3
print("\n4. Triggering manual retry for attempt 3...")
retry_res = requests.post(f"https://api.hookdeck.com/2025-07-01/events/{event_id}/retry", headers=headers, json={})
print("Retry 3 response:", retry_res.status_code)

# Wait for attempt 3 to be recorded
attempts = wait_for_attempts(3)

# Now repoint Destination A to https://mock.codes/200
print("\n5. Repointing Destination A to https://mock.codes/200...")
update_res = requests.put(f"https://api.hookdeck.com/2025-07-01/destinations/{dest_a_id}", headers=headers, json={
    "config": {
        "url": "https://mock.codes/200"
    }
})
print("Update destination status:", update_res.status_code)

# Wait a couple of seconds for settings to propagate
time.sleep(3)

# Trigger manual retry for attempt 4 (which should succeed)
print("\n6. Triggering manual retry for attempt 4 (should succeed)...")
retry_res = requests.post(f"https://api.hookdeck.com/2025-07-01/events/{event_id}/retry", headers=headers, json={})
print("Retry 4 response:", retry_res.status_code)

# Wait for attempt 4 to be recorded and check status
attempts = wait_for_attempts(4)

print("\n7. Final check of Event A status...")
event_res = requests.get(f"https://api.hookdeck.com/2025-07-01/events/{event_id}", headers=headers)
if event_res.status_code == 200:
    ev = event_res.json()
    print(f"Event ID: {ev.get('id')}")
    print(f"Event Status: {ev.get('status')}")
    print(f"Event Attempts Count: {ev.get('attempts')}")
else:
    print("Error fetching event:", event_res.status_code, event_res.text)
