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
    
    connection_name = f"mock-conn-{run_id}"
    source_name = f"mock-source-{run_id}"
    dest_name = f"mock-dest-{run_id}"

    # Let's try 2025-07-01 version first
    url = "https://api.hookdeck.com/2025-07-01/connections"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    payload = {
        "name": connection_name,
        "source": {
            "name": source_name
        },
        "destination": {
            "name": dest_name,
            "type": "MOCK_API"
        }
    }

    print(f"Creating connection: {connection_name}")
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            print("Response Status:", response.status)
            print("Response Body:", res_body)
            # Parse response to get source details
            data = json.loads(res_body)
            print("Connection created successfully!")
            print(f"Source ID: {data.get('source', {}).get('id')}")
            print(f"Source URL: {data.get('source', {}).get('url')}")
    except urllib.error.HTTPError as e:
        print("HTTP Error:", e.code)
        print("Error Response:", e.read().decode("utf-8"))
        sys.exit(1)
    except Exception as e:
        print("Error occurred:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
