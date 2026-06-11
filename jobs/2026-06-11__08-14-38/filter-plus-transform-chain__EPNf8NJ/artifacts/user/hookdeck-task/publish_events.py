import os
import requests
import json
import time

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

if not api_key:
    print("Error: HOOKDECK_API_KEY environment variable is not set.")
    exit(1)

if not run_id:
    print("Error: ZEALT_RUN_ID environment variable is not set.")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "X-Hookdeck-Source-Name": f"chain-src-{run_id}"
}

publish_url = "https://hkdk.events/v1/publish"

events = [
    # 2 order.created events (should pass filter and be transformed)
    {"type": "order.created", "order_id": "ord_101", "amount": 99.99},
    {"type": "order.created", "order_id": "ord_102", "amount": 149.50},
    # 2 other events (should be filtered out)
    {"type": "order.updated", "order_id": "ord_101", "status": "shipped"},
    {"type": "customer.created", "customer_id": "cust_201", "email": "customer@example.com"}
]

for i, ev in enumerate(events, 1):
    print(f"Publishing event {i}: {ev}")
    res = requests.post(publish_url, headers=headers, json=ev)
    print(f"Status code: {res.status_code}")
    print(res.text)
    time.sleep(1) # small delay between requests

print("All 4 events published.")
