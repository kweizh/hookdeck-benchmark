import os
import requests

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

print(f"API Key length: {len(api_key) if api_key else 'None'}")
print(f"Run ID: {run_id}")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Let's try to query the projects or connections to verify authentication
url = "https://api.hookdeck.com/2025-07-01/connections"
try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
