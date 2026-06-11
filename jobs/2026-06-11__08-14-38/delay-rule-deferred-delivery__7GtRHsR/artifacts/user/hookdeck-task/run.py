import os
import time
import json
import urllib.request
import urllib.error
import base64
import subprocess
from datetime import datetime

def post_event(url, data):
    req_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body)
    except Exception as e:
        print(f"Error posting event: {e}")
        return None

def get_request_events(request_id, api_key):
    url = f"https://api.hookdeck.com/2025-07-01/requests/{request_id}/events"
    cmd = [
        "curl", "-s",
        "-H", f"Authorization: Bearer {api_key}",
        "-H", "Content-Type: application/json",
        url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return json.loads(res.stdout)
        else:
            print(f"Curl failed with code {res.returncode}: {res.stderr}")
            return None
    except Exception as e:
        print(f"Error fetching events for request {request_id}: {e}")
        return None

def parse_iso_ms(iso_str):
    # Parses ISO timestamp to millisecond timestamp
    # Hookdeck format: "2026-06-11T08:25:43.828Z"
    if iso_str.endswith('Z'):
        iso_str = iso_str[:-1]
    
    # Handle optional milliseconds
    if '.' in iso_str:
        base_part, ms_part = iso_str.split('.')
        # Pad or truncate ms to 6 digits for microseconds parsing
        ms_part = (ms_part + "000000")[:6]
        dt = datetime.strptime(f"{base_part}.{ms_part}", "%Y-%m-%dT%H:%M:%S.%f")
    else:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S")
        
    return int(dt.timestamp() * 1000)

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")
    if not run_id or not api_key:
        print("Missing ZEALT_RUN_ID or HOOKDECK_API_KEY env variables")
        return
        
    source_url = "https://hkdk.events/jzie17rme6aumi"
    print(f"Publishing 3 events to {source_url}...")
    
    request_ids = []
    for i in range(3):
        payload = {"event_num": i + 1, "timestamp": time.time()}
        res = post_event(source_url, payload)
        if res and "request_id" in res:
            req_id = res["request_id"]
            request_ids.append(req_id)
            print(f"Published event {i+1}, request_id: {req_id}")
        else:
            print(f"Failed to publish event {i+1}")
            return
        time.sleep(1) # sleep 1s between posts
        
    print("Waiting 15 seconds for events to be processed and delivered...")
    time.sleep(15)
    
    events_info = []
    for req_id in request_ids:
        # Poll for event delivery
        attempts = 0
        event_model = None
        while attempts < 10:
            res = get_request_events(req_id, api_key)
            if res and "models" in res and len(res["models"]) > 0:
                model = res["models"][0]
                if model.get("status") == "SUCCESSFUL":
                    event_model = model
                    break
                elif model.get("status") in ["FAILED", "PAUSED", "DISABLED"]:
                    print(f"Event for request {req_id} ended with unexpected status: {model.get('status')}")
                    event_model = model
                    break
            print(f"Event for request {req_id} not successful yet, polling... ({attempts+1}/10)")
            time.sleep(2)
            attempts += 1
            
        if not event_model:
            print(f"Timed out waiting for event associated with request {req_id}")
            return
            
        events_info.append(event_model)
        
    # Verify and write logs
    verified = True
    lines_to_write = []
    
    for i, ev in enumerate(events_info):
        ev_id = ev["id"]
        created_at_str = ev["created_at"]
        successful_at_str = ev["successful_at"]
        status = ev["status"]
        
        created_at_ms = parse_iso_ms(created_at_str)
        successful_at_ms = parse_iso_ms(successful_at_str)
        delay_ms = successful_at_ms - created_at_ms
        
        print(f"\n--- Event {i+1} Verification ---")
        print(f"Event ID: {ev_id}")
        print(f"Status: {status}")
        print(f"Created At: {created_at_str} ({created_at_ms} ms)")
        print(f"Successful At: {successful_at_str} ({successful_at_ms} ms)")
        print(f"Observed Delay: {delay_ms} ms")
        
        if status != "SUCCESSFUL":
            print(f"Verification failed: Status is {status}, expected SUCCESSFUL")
            verified = False
        if delay_ms < 5000:
            print(f"Verification failed: Delay {delay_ms} ms is less than 5000 ms")
            verified = False
        if delay_ms >= 10000:
            print(f"Verification failed: Delay {delay_ms} ms is greater than or equal to 10000 ms")
            verified = False
            
        lines_to_write.append(f"Event ID: {ev_id}\n")
        
    if verified:
        log_dir = "/home/user/hookdeck-task"
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "output.log")
        with open(log_path, "w") as f:
            f.writelines(lines_to_write)
        print(f"\nAll verifications passed! Log written to {log_path}")
    else:
        print("\nSome verifications failed. Log not written.")

if __name__ == "__main__":
    main()
