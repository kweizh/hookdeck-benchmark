import os
import sys
import json
import urllib.request
import urllib.error
import time

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")

    if not run_id:
        print("Error: ZEALT_RUN_ID is not set")
        sys.exit(1)
    if not api_key:
        print("Error: HOOKDECK_API_KEY is not set")
        sys.exit(1)

    # Let's wait a couple of seconds for processing
    time.sleep(2)

    url = "https://api.hookdeck.com/2025-07-01/events"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    print("Fetching events from Hookdeck API...")
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            # Find events related to our run_id or source
            events = data.get("models", [])
            print(f"Total events found: {len(events)}")
            for event in events:
                source = event.get("source", {})
                source_name = source.get("name") if isinstance(source, dict) else ""
                dest = event.get("destination", {})
                dest_name = dest.get("name") if isinstance(dest, dict) else ""
                
                # In some API versions, source and destination might just be strings or dicts
                # Let's handle both
                if not source_name and isinstance(event.get("source_id"), str):
                    # It's an ID, let's print basic info
                    pass

                print(f"Event ID: {event.get('id')}")
                print(f"  Status: {event.get('status')}")
                print(f"  Source: {source_name or event.get('source_id')}")
                print(f"  Destination: {dest_name or event.get('destination_id')}")
                
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code)
        print("Error Response:", e.read().decode("utf-8"))
    except Exception as e:
        print("Error occurred:", e)

if __name__ == "__main__":
    main()
