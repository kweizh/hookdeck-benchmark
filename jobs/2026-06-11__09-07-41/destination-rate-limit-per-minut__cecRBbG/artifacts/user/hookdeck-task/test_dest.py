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

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method, headers=headers)
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode('utf-8')}")
        return None

# Try 1: root
p1 = {"name": "test-root", "type": "MOCK_API", "rate_limit": 2, "rate_limit_period": "minute"}
d1 = make_request(f"{api_base}/destinations", "POST", p1)
print("Root:", d1['config']['rate_limit'])

# Try 2: config
p2 = {"name": "test-config", "type": "MOCK_API", "config": {"rate_limit": 2, "rate_limit_period": "minute"}}
d2 = make_request(f"{api_base}/destinations", "POST", p2)
print("Config:", d2['config']['rate_limit'])

make_request(f"{api_base}/destinations/{d1['id']}", "DELETE")
make_request(f"{api_base}/destinations/{d2['id']}", "DELETE")

