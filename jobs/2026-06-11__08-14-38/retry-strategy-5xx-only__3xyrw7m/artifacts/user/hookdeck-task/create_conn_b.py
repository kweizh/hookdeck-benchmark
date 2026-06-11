import os
import requests
import json

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload_b = {
    "name": f"conn-b-{run_id}",
    "source": {
        "name": f"src-b-{run_id}",
        "type": "WEBHOOK"
    },
    "destination": {
        "name": f"dest-b-{run_id}",
        "type": "HTTP",
        "config": {
            "url": "https://httpstat.us/422"
        }
    },
    "rules": [
        {
            "type": "retry",
            "strategy": "linear",
            "interval": 30000,
            "count": 5,
            "response_status_codes": ["500", "502", "503", "504"]
        }
    ]
}

print("Creating Connection B...")
res = requests.post("https://api.hookdeck.com/2025-07-01/connections", headers=headers, json=payload_b)
print("Status Code:", res.status_code)
print("Response:", json.dumps(res.json(), indent=2))
