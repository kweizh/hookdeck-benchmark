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

event_ids = ["evt_ddEWoCKS7mV9yEOhr3","evt_qLZTuJ5IOOi5LO2hZJ","evt_hh8nJrSF0rkur4CDsJ","evt_JKR1KjvmQEqJo3borC","evt_AYmR8W2I4caCUls4Mo"]

for eid in event_ids:
    req = urllib.request.Request(f"{api_base}/events/{eid}", headers=headers)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(data['id'], data.get('successful_at'))
