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

def make_request(url, method="GET", data=None, headers=headers):
    req = urllib.request.Request(url, method=method, headers=headers)
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req) as response:
            res = response.read()
            if res:
                return json.loads(res.decode('utf-8'))
            return {}
    except Exception as e:
        print(e)
        return {}

make_request(f"{api_base}/connections/web_Anb26srz3rp0", method="DELETE")
make_request(f"{api_base}/sources/src_cy98kns7uock4g", method="DELETE")
make_request(f"{api_base}/destinations/des_4gue6Ah8OhZi", method="DELETE")

