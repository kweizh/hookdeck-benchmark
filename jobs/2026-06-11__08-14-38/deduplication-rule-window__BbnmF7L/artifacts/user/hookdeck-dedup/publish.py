import os
import time
import requests

HOOKDECK_API_KEY = os.environ.get("HOOKDECK_API_KEY")
RUN_ID = os.environ.get("ZEALT_RUN_ID")

if not HOOKDECK_API_KEY or not RUN_ID:
    print("Error: HOOKDECK_API_KEY and ZEALT_RUN_ID must be set.")
    exit(1)

source_name = f"dedup-src-{RUN_ID}"
publish_url = "https://hkdk.events/v1/publish"

headers = {
    "Authorization": f"Bearer {HOOKDECK_API_KEY}",
    "Content-Type": "application/json",
    "X-Hookdeck-Source-Name": source_name
}

# We already sent 1 request with {"id": "dup-1", "type": "test-type"}.
# Let's send 4 more identical requests to complete the duplicate group of 5.
print("Sending 4 more duplicate requests...")
for i in range(4):
    payload = {"id": "dup-1", "type": "test-type"}
    res = requests.post(publish_url, json=payload, headers=headers)
    print(f"Duplicate {i+1}: {res.status_code} - {res.text}")
    time.sleep(1)

# Now send 2 distinct requests (different from duplicate group and each other)
print("\nSending 2 distinct requests...")
distinct_payloads = [
    {"id": "distinct-1", "type": "test-distinct-1"},
    {"id": "distinct-2", "type": "test-distinct-2"}
]

for i, payload in enumerate(distinct_payloads):
    res = requests.post(publish_url, json=payload, headers=headers)
    print(f"Distinct {i+1}: {res.status_code} - {res.text}")
    time.sleep(1)

print("\nDone publishing requests.")
