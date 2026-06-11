import os
import sys
import json
import urllib.request
import urllib.error

def main():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")

    if not run_id:
        print("Error: ZEALT_RUN_ID is not set")
        sys.exit(1)
    if not api_key:
        print("Error: HOOKDECK_API_KEY is not set")
        sys.exit(1)

    print(f"Using ZEALT_RUN_ID: {run_id}")
    
    source_name = f"mock-source-{run_id}"
    payload = {
        "event": "test.created",
        "data": {
            "run_id": run_id
        }
    }

    # Attempt 1: Using Publish API endpoint (https://hkdk.events/v1/publish)
    publish_url = "https://hkdk.events/v1/publish"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Hookdeck-Source-Name": source_name,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    print(f"Publishing event to {source_name} via Publish API...")
    req = urllib.request.Request(publish_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print("Response Status:", response.status)
            print("Response Body:", res_body)
            print("Successfully published event via Publish API!")
    except urllib.error.HTTPError as e:
        print("HTTP Error on Publish API:", e.code)
        print("Error Response:", e.read().decode("utf-8"))
        sys.exit(1)
    except Exception as e:
        print("Error occurred on Publish API:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
