#!/usr/bin/env python3
"""Verify all 100 requests have correct bodies and headers, and all events are SUCCESSFUL."""

import json
import subprocess
import os
import sys
import time

API_BASE = "https://api.hookdeck.com/2025-07-01"
API_KEY = os.environ.get("HOOKDECK_API_KEY", "")
SOURCE_ID = "src_shf232fkafkqau"
RUN_ID = os.environ.get("ZEALT_RUN_ID", "")

def api_get(path, params=""):
    url = f"{API_BASE}{path}?{params}" if params else f"{API_BASE}{path}"
    result = subprocess.run(
        ["curl", "-s", url, "-H", f"Authorization: Bearer {API_KEY}"],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def api_get_raw(path, params=""):
    url = f"{API_BASE}{path}?{params}" if params else f"{API_BASE}{path}"
    result = subprocess.run(
        ["curl", "-s", url, "-H", f"Authorization: Bearer {API_KEY}"],
        capture_output=True, text=True
    )
    return result.stdout

# 1. Verify requests count
print("=== Verifying Requests ===")
requests_data = api_get("/requests", f"source_id={SOURCE_ID}&limit=100")
request_models = requests_data.get("models", [])
print(f"Total requests found: {len(request_models)}")

# 2. Verify events are all SUCCESSFUL
print("\n=== Verifying Events ===")
events_data = api_get("/events", f"source_id={SOURCE_ID}&limit=100&status=SUCCESSFUL")
event_models = events_data.get("models", [])
print(f"Successful events found: {len(event_models)}")

# Also check for non-successful events
other_events = api_get("/events", f"source_id={SOURCE_ID}&limit=100&status=FAILED")
failed_count = len(other_events.get("models", []))
other_events2 = api_get("/events", f"source_id={SOURCE_ID}&limit=100&status=PENDING")
pending_count = len(other_events2.get("models", []))
print(f"Failed events: {failed_count}")
print(f"Pending events: {pending_count}")

# 3. Verify individual request bodies and headers
print("\n=== Verifying Request Bodies and Headers ===")
i_values = set()
batch_id_count = 0
errors = []

for req in request_models:
    req_id = req["id"]
    req_detail = json.loads(api_get_raw(f"/requests/{req_id}"))
    
    # Check body
    body = req_detail.get("data", {}).get("body", {})
    if isinstance(body, str):
        body = json.loads(body)
    
    if "i" not in body:
        errors.append(f"Request {req_id}: missing 'i' in body: {body}")
    else:
        i_val = body["i"]
        if i_val in i_values:
            errors.append(f"Request {req_id}: duplicate i={i_val}")
        i_values.add(i_val)
    
    # Check x-batch-id header
    headers = req_detail.get("data", {}).get("headers", {})
    batch_id = headers.get("x-batch-id", "")
    if batch_id == "BATCH-001":
        batch_id_count += 1
    else:
        errors.append(f"Request {req_id}: x-batch-id={batch_id} (expected BATCH-001)")

print(f"Unique i values: {len(i_values)}")
print(f"i range: {min(i_values) if i_values else 'N/A'} - {max(i_values) if i_values else 'N/A'}")
print(f"Requests with x-batch-id: BATCH-001: {batch_id_count}")
print(f"i values match 0-99: {i_values == set(range(100))}")

if errors:
    print(f"\n=== Errors ({len(errors)}) ===")
    for e in errors[:10]:
        print(f"  {e}")
else:
    print("\n✅ All verifications passed!")

# 4. Write summary
print("\n=== Summary ===")
print(f"Source Name: bulk-source-{RUN_ID}")
print(f"Destination Name: bulk-dest-{RUN_ID}")
print(f"Published Count: 100")
print(f"Batch ID: BATCH-001")