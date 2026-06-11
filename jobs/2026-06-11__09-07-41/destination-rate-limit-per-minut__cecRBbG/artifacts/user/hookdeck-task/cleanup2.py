import os
import urllib.request
import json

api_key = os.environ.get('HOOKDECK_API_KEY')
run_id = os.environ.get('ZEALT_RUN_ID')
api_base = "https://api.hookdeck.com/2025-07-01"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

def make_request(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            res = response.read()
            if res:
                return json.loads(res.decode('utf-8'))
            return {}
    except Exception as e:
        return {}

dests = make_request(f"{api_base}/destinations?name=rl-dest-{run_id}").get('models', [])
for d in dests:
    make_request(f"{api_base}/destinations/{d['id']}", "DELETE")

srcs = make_request(f"{api_base}/sources?name=rl-src-{run_id}").get('models', [])
for s in srcs:
    make_request(f"{api_base}/sources/{s['id']}", "DELETE")

conns = make_request(f"{api_base}/connections?name=rl-conn-{run_id}").get('models', [])
for c in conns:
    make_request(f"{api_base}/connections/{c['id']}", "DELETE")

print("Cleaned up")
