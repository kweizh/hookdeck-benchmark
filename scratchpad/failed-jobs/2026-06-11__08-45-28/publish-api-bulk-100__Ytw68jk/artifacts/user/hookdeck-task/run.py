#!/usr/bin/env python3
"""
Bulk publish 100 events via Hookdeck Publish API, verify via Inspect API,
and write a summary log.
"""

import os
import sys
import json
import time
import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
PUBLISH_URL = "https://hkdk.events/v1/publish"

API_KEY = os.environ["HOOKDECK_API_KEY"]
RUN_ID = os.environ["ZEALT_RUN_ID"]

SOURCE_NAME = f"bulk-source-{RUN_ID}"
DEST_NAME = f"bulk-dest-{RUN_ID}"
BATCH_ID = "BATCH-001"
EVENT_COUNT = 100

LOG_PATH = "/home/user/hookdeck-task/output.log"

SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
})


def api_get(path, params=None):
    url = f"{API_BASE}{path}"
    resp = SESSION.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def api_put(path, body):
    url = f"{API_BASE}{path}"
    resp = SESSION.put(url, json=body)
    if not resp.ok:
        print(f"  PUT {path} -> {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json()


def create_connection():
    print(f"Creating connection: {SOURCE_NAME} -> {DEST_NAME} (MOCK_API)...")
    payload = {
        "name": f"bulk-conn-{RUN_ID}",
        "source": {
            "name": SOURCE_NAME,
        },
        "destination": {
            "name": DEST_NAME,
            "type": "MOCK_API",
        },
    }
    result = api_put("/connections", payload)
    source_id = result["source"]["id"]
    dest_id = result["destination"]["id"]
    conn_id = result["id"]
    print(f"  Connection ID:  {conn_id}")
    print(f"  Source ID:      {source_id}")
    print(f"  Destination ID: {dest_id}")
    return source_id, dest_id, conn_id


def publish_events(source_name):
    print(f"\nPublishing {EVENT_COUNT} events to source '{source_name}'...")
    # Use a separate session without the default Content-Type
    pub_session = requests.Session()
    success_count = 0
    for i in range(EVENT_COUNT):
        body = {"i": i}
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "X-Hookdeck-Source-Name": source_name,
            "x-batch-id": BATCH_ID,
        }
        resp = pub_session.post(PUBLISH_URL, json=body, headers=headers)
        if resp.ok:
            success_count += 1
        else:
            print(f"  WARN: publish i={i} failed: {resp.status_code} {resp.text}")

        if (i + 1) % 20 == 0:
            print(f"  Published {i + 1}/{EVENT_COUNT}...")

    print(f"  Done. Successful publishes: {success_count}/{EVENT_COUNT}")
    return success_count


def poll_requests(source_id, expected=100, timeout=120):
    """Poll until we see `expected` requests for this source."""
    print(f"\nPolling for {expected} requests on source {source_id}...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = api_get("/requests", params={"source_id": source_id, "limit": 100})
        count = result.get("count", 0)
        print(f"  Requests count: {count}")
        if count >= expected:
            print(f"  Reached {count} requests.")
            return result
        time.sleep(5)
    result = api_get("/requests", params={"source_id": source_id, "limit": 100})
    return result


def poll_events(source_id, expected=100, timeout=180):
    """Poll until we see `expected` SUCCESSFUL events."""
    print(f"\nPolling for {expected} SUCCESSFUL events on source {source_id}...")
    deadline = time.time() + timeout
    successful = 0
    last_result = None
    while time.time() < deadline:
        result = api_get("/events", params={"source_id": source_id, "limit": 250})
        models = result.get("models", [])
        successful = sum(1 for e in models if e.get("status") == "SUCCESSFUL")
        total = len(models)
        print(f"  Events: total={total}, SUCCESSFUL={successful}")
        last_result = result
        if successful >= expected:
            print(f"  Reached {successful} SUCCESSFUL events.")
            return result, successful
        time.sleep(8)
    if last_result is None:
        last_result = api_get("/events", params={"source_id": source_id, "limit": 250})
        models = last_result.get("models", [])
        successful = sum(1 for e in models if e.get("status") == "SUCCESSFUL")
    return last_result, successful


def verify_request_details(source_id, expected_count=100):
    """
    Fetch each request detail to verify x-batch-id header and body coverage.
    Returns (batch_header_count, body_values_set).
    """
    print(f"\nVerifying request details for source {source_id}...")
    # Fetch all requests (up to 250)
    result = api_get("/requests", params={"source_id": source_id, "limit": 250})
    models = result.get("models", [])
    print(f"  Total requests fetched: {len(models)}")

    batch_header_count = 0
    body_values = set()

    for idx, req in enumerate(models):
        req_id = req["id"]
        detail = api_get(f"/requests/{req_id}")
        data = detail.get("data", {})

        # Headers are at data.headers (top-level request headers)
        headers = data.get("headers", {})
        # Hookdeck lowercases header names
        batch_val = headers.get("x-batch-id")
        if batch_val == BATCH_ID:
            batch_header_count += 1

        # Body is at data.body
        body = data.get("body", {})
        if isinstance(body, dict):
            i_val = body.get("i")
            if i_val is not None:
                body_values.add(int(i_val))

        if (idx + 1) % 20 == 0:
            print(f"  Checked {idx + 1}/{len(models)} requests...")

    print(f"  Requests with x-batch-id={BATCH_ID}: {batch_header_count}")
    print(f"  Unique 'i' body values found: {len(body_values)}")

    expected_values = set(range(expected_count))
    missing = expected_values - body_values
    extra = body_values - expected_values
    if missing:
        print(f"  WARN: Missing i values: {sorted(missing)}")
    if extra:
        print(f"  WARN: Extra i values: {sorted(extra)}")

    return batch_header_count, body_values


def main():
    print("=" * 60)
    print(f"Run ID:           {RUN_ID}")
    print(f"Source Name:      {SOURCE_NAME}")
    print(f"Destination Name: {DEST_NAME}")
    print("=" * 60)

    # Step 1: Create connection
    source_id, dest_id, conn_id = create_connection()

    # Step 2: Publish 100 events
    published = publish_events(SOURCE_NAME)

    # Give Hookdeck a moment to ingest
    print("\nWaiting 5s for initial ingestion...")
    time.sleep(5)

    # Step 3: Poll until all requests appear
    req_result = poll_requests(source_id, expected=EVENT_COUNT, timeout=120)
    req_count = req_result.get("count", 0)

    # Step 4: Poll until all events are SUCCESSFUL
    evt_result, successful_count = poll_events(source_id, expected=EVENT_COUNT, timeout=180)

    # Step 5: Verify headers and bodies per request
    batch_header_count, body_values = verify_request_details(source_id, expected_count=EVENT_COUNT)

    body_complete = (set(range(EVENT_COUNT)) == body_values)

    # Step 6: Write log
    print(f"\nWriting log to {LOG_PATH}...")
    with open(LOG_PATH, "w") as f:
        f.write(f"Source Name: {SOURCE_NAME}\n")
        f.write(f"Destination Name: {DEST_NAME}\n")
        f.write(f"Published Count: {EVENT_COUNT}\n")
        f.write(f"Batch ID: {BATCH_ID}\n")
        f.write(f"Connection ID: {conn_id}\n")
        f.write(f"Source ID: {source_id}\n")
        f.write(f"Destination ID: {dest_id}\n")
        f.write(f"Requests Ingested: {req_count}\n")
        f.write(f"Events Successful: {successful_count}\n")
        f.write(f"Requests With Batch Header: {batch_header_count}\n")
        f.write(f"Unique Body i-Values: {len(body_values)}\n")
        f.write(f"Body Coverage Complete: {body_complete}\n")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Source Name:           {SOURCE_NAME}")
    print(f"Destination Name:      {DEST_NAME}")
    print(f"Published Count:       {EVENT_COUNT}")
    print(f"Batch ID:              {BATCH_ID}")
    print(f"Requests Ingested:     {req_count}")
    print(f"Events Successful:     {successful_count}")
    print(f"Batch Header Count:    {batch_header_count}")
    print(f"Body Coverage:         {len(body_values)}/100  (complete={body_complete})")
    print(f"Log written to:        {LOG_PATH}")

    ok = True
    if successful_count < EVENT_COUNT:
        print(f"\nWARN: Only {successful_count}/{EVENT_COUNT} events SUCCESSFUL")
        ok = False
    if batch_header_count < EVENT_COUNT:
        print(f"\nWARN: Only {batch_header_count}/{EVENT_COUNT} requests have x-batch-id header")
        ok = False
    if not body_complete:
        print(f"\nWARN: Body i-values incomplete. Got {len(body_values)}/100")
        ok = False

    if ok:
        print("\nAll acceptance criteria met!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
