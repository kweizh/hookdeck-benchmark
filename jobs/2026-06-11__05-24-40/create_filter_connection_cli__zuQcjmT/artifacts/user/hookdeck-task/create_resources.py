import os
import sys
import json
import requests

def main():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    run_id = os.environ.get("ZEALT_RUN_ID")

    if not api_key:
        print("Error: HOOKDECK_API_KEY is not set.")
        sys.exit(1)
    if not run_id:
        print("Error: ZEALT_RUN_ID is not set.")
        sys.exit(1)

    source_name = f"source-{run_id}"
    dest_name = f"dest-{run_id}"
    conn_name = f"conn-{run_id}"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Attempt to create everything in a single call (Connection with inline Source, Destination, and Filter rule)
    url = "https://api.hookdeck.com/2025-07-01/connections"
    payload = {
        "name": conn_name,
        "source": {
            "name": source_name,
            "type": "WEBHOOK"
        },
        "destination": {
            "name": dest_name,
            "type": "MOCK_API"
        },
        "rules": [
            {
                "type": "filter",
                "body": {
                    "type": "order.created"
                }
            }
        ]
    }

    print(f"Sending POST to {url} with payload:")
    print(json.dumps(payload, indent=2))

    response = requests.post(url, json=payload, headers=headers)
    print(f"Response Status Code: {response.status_code}")
    
    if response.status_code in (200, 201):
        data = response.json()
        print("Successfully created connection and resources!")
        print(json.dumps(data, indent=2))
        
        connection_id = data.get("id")
        if not connection_id:
            print("Error: Connection ID not found in response.")
            sys.exit(1)
            
        output_log_path = "/home/user/hookdeck-task/output.log"
        with open(output_log_path, "w") as f:
            f.write(f"Connection ID: {connection_id}\n")
        print(f"Wrote connection ID '{connection_id}' to {output_log_path}")
    else:
        print("Failed to create connection inline. Response details:")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
