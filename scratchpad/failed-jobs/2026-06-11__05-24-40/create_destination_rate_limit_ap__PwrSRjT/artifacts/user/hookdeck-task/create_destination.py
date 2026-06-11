import os
import json
import requests

def main():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    run_id = os.environ.get("ZEALT_RUN_ID")

    if not api_key:
        print("Error: HOOKDECK_API_KEY environment variable is not set.")
        return

    if not run_id:
        print("Error: ZEALT_RUN_ID environment variable is not set.")
        return

    dest_name = f"rate-limited-dest-{run_id}"
    url = "https://api.hookdeck.com/2025-07-01/destinations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "name": dest_name,
        "type": "HTTP",
        "config": {
            "url": "https://mock.hookdeck.com/rate-limited",
            "rate_limit": 10,
            "rate_limit_period": "second"
        }
    }

    print(f"Creating destination with name: {dest_name}")
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code not in (200, 201):
        print(f"Failed to create destination. Status code: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    dest_id = data.get("id")
    print(f"Successfully created destination. ID: {dest_id}")

    output_log_path = "/home/user/hookdeck-task/output.log"
    with open(output_log_path, "w") as f:
        f.write(f"Destination ID: {dest_id}\n")

    print(f"Saved destination ID to {output_log_path}")

if __name__ == "__main__":
    main()
