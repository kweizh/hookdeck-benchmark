import os
import urllib.request
import json

api_key = os.environ.get('HOOKDECK_API_KEY')
api_base = "https://api.hookdeck.com/2025-07-01"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

req = urllib.request.Request(f"{api_base}/destinations/des_4gue6Ah8OhZi", headers=headers)
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode('utf-8'))
    print(json.dumps(data, indent=2))
