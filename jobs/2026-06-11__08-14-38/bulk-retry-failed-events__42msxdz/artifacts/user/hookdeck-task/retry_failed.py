import os
import sys
import time
import requests

def main():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    run_id = os.environ.get("ZEALT_RUN_ID")
    
    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable not set")
        sys.exit(1)
    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable not set")
        sys.exit(1)
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    connection_name = f"bulk-conn-{run_id}"
    print(f"Searching for connection with name: {connection_name}")
    
    # 1. Retrieve the connection ID
    res = requests.get("https://api.hookdeck.com/2025-07-01/connections", headers=headers)
    if res.status_code != 200:
        print(f"Error fetching connections: {res.status_code} - {res.text}")
        sys.exit(1)
        
    connections = res.json().get("models", [])
    target_connection = None
    for conn in connections:
        if conn.get("name") == connection_name:
            target_connection = conn
            break
            
    if not target_connection:
        print(f"Error: Connection with name {connection_name} not found.")
        sys.exit(1)
        
    connection_id = target_connection["id"]
    print(f"Found Connection ID: {connection_id}")
    
    # 2. Query initial FAILED events on the connection
    res = requests.get(
        "https://api.hookdeck.com/2025-07-01/events",
        headers=headers,
        params={"webhook_id": connection_id, "status": "FAILED"}
    )
    if res.status_code != 200:
        print(f"Error fetching initial failed events: {res.status_code} - {res.text}")
        sys.exit(1)
        
    failed_events = res.json().get("models", [])
    failed_event_ids = [event["id"] for event in failed_events]
    print(f"Initial failed events count: {len(failed_event_ids)}")
    print(f"Failed Event IDs: {failed_event_ids}")
    
    if len(failed_event_ids) == 0:
        print("No failed events to retry.")
        write_log(connection_id)
        return

    # 3. Trigger the bulk retry
    print("Triggering bulk retry...")
    body = {
        "query": {
            "webhook_id": connection_id,
            "status": "FAILED"
        }
    }
    res = requests.post(
        "https://api.hookdeck.com/2025-07-01/bulk/events/retry",
        headers=headers,
        json=body
    )
    if res.status_code != 200:
        print(f"Error triggering bulk retry: {res.status_code} - {res.text}")
        sys.exit(1)
        
    bulk_retry_data = res.json()
    bulk_retry_id = bulk_retry_data.get("id")
    print(f"Bulk retry triggered successfully. Bulk Retry ID: {bulk_retry_id}")
    print(bulk_retry_data)
    
    # 4. Poll until count of FAILED events on the connection is 0
    print("Polling events status...")
    max_polls = 60
    poll_count = 0
    while poll_count < max_polls:
        res = requests.get(
            "https://api.hookdeck.com/2025-07-01/events",
            headers=headers,
            params={"webhook_id": connection_id, "status": "FAILED"}
        )
        if res.status_code != 200:
            print(f"Error during polling: {res.status_code} - {res.text}")
            time.sleep(5)
            continue
            
        current_failed = res.json().get("models", [])
        failed_count = len(current_failed)
        print(f"Poll {poll_count + 1}: FAILED events count = {failed_count}")
        
        if failed_count == 0:
            print("All previously FAILED events have converged!")
            break
            
        poll_count += 1
        time.sleep(5)
    else:
        print("Error: Polling timed out. Not all events converged to SUCCESSFUL.")
        sys.exit(1)
        
    # 5. Double check that previously failed events are indeed successful/completed
    print("Verifying success criteria...")
    successful_events_count = 0
    for event_id in failed_event_ids:
        res = requests.get(f"https://api.hookdeck.com/2025-07-01/events/{event_id}", headers=headers)
        if res.status_code != 200:
            print(f"Error fetching event {event_id}: {res.status_code} - {res.text}")
            sys.exit(1)
            
        event_data = res.json()
        status = event_data.get("status")
        attempts = event_data.get("attempts", 0)
        print(f"Event {event_id}: status={status}, attempts={attempts}")
        
        # Check attempts count >= 2
        if attempts < 2:
            print(f"Warning: Event {event_id} has less than 2 attempts ({attempts})")
            
        # Get attempts details to verify trigger
        attempts_res = requests.get(
            "https://api.hookdeck.com/2025-07-01/attempts",
            headers=headers,
            params={"event_id": event_id}
        )
        if attempts_res.status_code != 200:
            print(f"Error fetching attempts for event {event_id}: {attempts_res.status_code}")
            sys.exit(1)
            
        attempts_list = attempts_res.json().get("models", [])
        # Sort attempts by attempt_number descending to find the latest
        attempts_list.sort(key=lambda x: x.get("attempt_number", 0), reverse=True)
        
        if len(attempts_list) == 0:
            print(f"Error: No attempts found for event {event_id}")
            sys.exit(1)
            
        latest_attempt = attempts_list[0]
        trigger = latest_attempt.get("trigger")
        print(f"Latest attempt for {event_id}: attempt_number={latest_attempt.get('attempt_number')}, trigger={trigger}, status={latest_attempt.get('status')}")
        
        if trigger not in ["BULK_RETRY", "MANUAL"]:
            print(f"Error: Latest attempt trigger for {event_id} is {trigger}, expected BULK_RETRY or MANUAL")
            sys.exit(1)
            
        if status == "SUCCESSFUL":
            successful_events_count += 1
            
    print(f"Successfully verified all previously FAILED events! Successful count: {successful_events_count}")
    
    # 6. Write to the output log file
    write_log(connection_id)
    print("Done!")

def write_log(connection_id):
    log_dir = "/home/user/hookdeck-task"
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "output.log")
    with open(log_path, "w") as f:
        f.write(f"Connection ID: {connection_id}\n")
    print(f"Log written to {log_path}")

if __name__ == "__main__":
    main()
