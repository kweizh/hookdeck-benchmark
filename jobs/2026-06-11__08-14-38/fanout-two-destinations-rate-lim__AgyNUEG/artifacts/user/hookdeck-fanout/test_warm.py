import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor

api_key = os.environ.get("HOOKDECK_API_KEY")
source_id = "src_xu9oqxbv77uikn"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "X-Hookdeck-Source-Id": source_id
}

session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount('https://', adapter)
session.headers.update(headers)

print("Pre-warming session...")
# Make 12 dummy requests in parallel to pre-warm 12 TCP connections in the pool!
def warm(i):
    try:
        session.post("https://hkdk.events/v1/publish", json={})
    except Exception:
        pass

with ThreadPoolExecutor(max_workers=12) as executor:
    list(executor.map(warm, range(12)))

print("Starting tight concurrent publish...")
start = time.time()

def send_req(i):
    session.post("https://hkdk.events/v1/publish", json={"i": i})

with ThreadPoolExecutor(max_workers=12) as executor:
    list(executor.map(send_req, range(12)))

print("Time taken to publish 12 events:", time.time() - start)
