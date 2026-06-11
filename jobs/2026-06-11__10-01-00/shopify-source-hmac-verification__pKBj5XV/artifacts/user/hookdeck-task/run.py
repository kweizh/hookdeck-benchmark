#!/usr/bin/env python3
"""
Create a Hookdeck SHOPIFY Source with HMAC verification, then send one correctly
signed request and one tampered request to exercise verification.
"""
import os
import sys
import json
import hmac
import hashlib
import base64
import time
import urllib.request
import urllib.error

# -- Environment --
RUN_ID = os.environ["ZEALT_RUN_ID"]
API_KEY = os.environ["HOOKDECK_API_KEY"]
WEBHOOK_SECRET = os.environ["SHOPIFY_WEBHOOK_SECRET"]

API_BASE = "https://api.hookdeck.com/2025-07-01"
SOURCE_NAME = f"shopify-verify-{RUN_ID}"

def api_request(method, path, body=None):
    """Make an authenticated request to the Hookdeck REST API."""
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    # Use Basic auth: username is API key, password is empty
    credentials = base64.b64encode(f"{API_KEY}:".encode("utf-8")).decode("utf-8")
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"API error {e.code} on {method} {path}: {err_body}", file=sys.stderr)
        raise

# -- Step 1: Create the SHOPIFY source with verification --
print(f"Creating source '{SOURCE_NAME}'...")
source = api_request("POST", "/sources", {
    "name": SOURCE_NAME,
    "type": "SHOPIFY",
    "verification": {
        "type": "SHOPIFY",
        "configs": {
            "webhook_secret_key": WEBHOOK_SECRET,
        },
    },
})

source_id = source["id"]
source_url = source["url"]
print(f"Source ID: {source_id}")
print(f"Source URL: {source_url}")

# -- Step 2: Prepare the JSON payload --
payload = json.dumps({"test": True, "order_id": 12345, "event": "order.created"}, separators=(",", ":"))
raw_body = payload.encode("utf-8")

# -- Step 3: Compute correct HMAC --
# Shopify: base64(HMAC_SHA256(secret, raw_request_body))
computed_hmac = base64.b64encode(
    hmac.new(WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256).digest()
).decode("utf-8")
print(f"Computed HMAC: {computed_hmac}")

# -- Step 4: Send correctly signed request --
print("Sending correctly signed request...")
req1 = urllib.request.Request(source_url, data=raw_body, method="POST")
req1.add_header("Content-Type", "application/json")
req1.add_header("X-Shopify-Hmac-Sha256", computed_hmac)
try:
    with urllib.request.urlopen(req1) as resp:
        print(f"  Correct request: HTTP {resp.status}")
except urllib.error.HTTPError as e:
    print(f"  Correct request: HTTP {e.status}")

# -- Step 5: Send tampered/unsigned request --
print("Sending tampered request...")
req2 = urllib.request.Request(source_url, data=raw_body, method="POST")
req2.add_header("Content-Type", "application/json")
req2.add_header("X-Shopify-Hmac-Sha256", "bad-signature-value")
try:
    with urllib.request.urlopen(req2) as resp:
        print(f"  Tampered request: HTTP {resp.status}")
except urllib.error.HTTPError as e:
    print(f"  Tampered request: HTTP {e.status}")

# -- Step 6: Wait for ingestion --
print("Waiting 5 seconds for ingestion...")
time.sleep(5)

# -- Step 7: Verify via Inspect API --
print("Checking requests via Inspect API...")
requests_data = api_request("GET", f"/requests?source_id={source_id}")

requests_list = requests_data.get("data", requests_data.get("models", []))
if isinstance(requests_list, dict):
    requests_list = requests_list.get("data", requests_list.get("models", []))

print(f"Found {len(requests_list)} request(s)")

verified_true = 0
verified_false = 0
for r in requests_list:
    v = r.get("verified")
    rc = r.get("rejection_cause")
    print(f"  Request {r.get('id')}: verified={v}, rejection_cause={rc}")
    if v is True:
        verified_true += 1
    if v is False and rc == "VERIFICATION_FAILED":
        verified_false += 1

print(f"Verified true: {verified_true}, Verified false with VERIFICATION_FAILED: {verified_false}")

# -- Step 8: Write output.log --
log_path = "/home/user/hookdeck-task/output.log"
with open(log_path, "w") as f:
    f.write(f"Source ID: {source_id}\n")
print(f"Wrote {log_path}")

# Summary
if verified_true >= 1 and verified_false >= 1:
    print("SUCCESS: Both verified and rejected requests found.")
else:
    print("WARNING: Expected at least 1 verified=true and 1 verified=false with VERIFICATION_FAILED.")
    sys.exit(1)
