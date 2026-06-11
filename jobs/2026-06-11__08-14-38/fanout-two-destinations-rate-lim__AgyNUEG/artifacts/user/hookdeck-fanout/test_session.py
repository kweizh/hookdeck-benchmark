import os
import requests
import time

api_key = os.environ.get("HOOKDECK_API_KEY")
source_id = "src_8snare8mg9uxik"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "X-Hookdeck-Source-Id": source_id
}

session = requests.Session()
session.headers.update(headers)

start = time.time()
for i in range(12):
    session.post("https://hkdk.events/v1/publish", json={"i": i})
print("Time taken with single thread + session:", time.time() - start)
