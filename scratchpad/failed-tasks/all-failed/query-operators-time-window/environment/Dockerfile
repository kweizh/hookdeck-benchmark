FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm i -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /workspace && chmod 0777 /workspace

# Seed script that runs on first invocation of test_initial_state.py.
# It is intentionally idempotent: if /workspace/seed.json already exists,
# the script exits without re-publishing events.
RUN mkdir -p /opt/hookdeck-seed && cat >/opt/hookdeck-seed/seed.py <<'PYEOF'
#!/usr/bin/env python3
"""Seed Hookdeck with a deterministic event burst for the time-window query task.

The seed publishes 15 events into a fresh per-run Hookdeck Source and then
records the middle 5 events (by server-assigned `created_at`) as the
"middle window" the candidate must retrieve.

Outputs `/workspace/seed.json` with:
    {
        "source_id":     "src_...",
        "source_name":   "qwin-<run-id>",
        "window_start":  "<ISO-8601 UTC, e.g. 2026-...Z>",
        "window_end":    "<ISO-8601 UTC>",
        "expected_ids":  ["evt_...", ...]   # exactly the middle-window IDs
    }
"""
import json
import os
import re
import sys
import time

import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
SEED_PATH = "/workspace/seed.json"

TOTAL_EVENTS = 15
INTER_EVENT_SLEEP = 1.0   # ~1s between publishes spreads `created_at` cleanly
PROPAGATION_WAIT = 6.0    # wait after the last publish before listing
LIST_RETRY_WAIT = 4.0     # back-off between list attempts when waiting on ingest
LIST_RETRIES = 12         # ~48s max wait for ingestion to complete


def auth_headers():
    api_key = os.environ.get("HOOKDECK_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("HOOKDECK_API_KEY is required to seed Hookdeck.")
    return {"Authorization": f"Bearer {api_key}"}


def safe_run_id() -> str:
    raw = os.environ.get("ZEALT_RUN_ID", "").strip() or "local"
    cleaned = re.sub(r"[^A-Za-z0-9-]", "-", raw).strip("-").lower()
    if not cleaned:
        cleaned = "local"
    # Hookdeck names allow [a-z0-9-]; trim to a sane length
    return cleaned[:48]


def upsert_connection(source_name: str, dest_name: str, conn_name: str) -> dict:
    body = {
        "name": conn_name,
        "source": {"name": source_name, "type": "WEBHOOK"},
        "destination": {"name": dest_name, "type": "MOCK_API"},
    }
    resp = requests.put(
        f"{API_BASE}/connections",
        headers={**auth_headers(), "Content-Type": "application/json"},
        json=body,
        timeout=30,
    )
    if resp.status_code >= 400:
        raise SystemExit(
            f"Failed to upsert Hookdeck connection ({resp.status_code}): {resp.text}"
        )
    return resp.json()


def publish_events(source_url: str, run_id: str) -> None:
    for i in range(TOTAL_EVENTS):
        payload = {"seq": i, "run_id": run_id}
        resp = requests.post(
            source_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise SystemExit(
                f"Failed to publish event {i} to {source_url}: {resp.status_code} {resp.text}"
            )
        if i < TOTAL_EVENTS - 1:
            time.sleep(INTER_EVENT_SLEEP)


def list_all_events(source_id: str) -> list[dict]:
    events: list[dict] = []
    next_cursor = None
    while True:
        params = [
            ("source_id", source_id),
            ("order_by", "created_at"),
            ("dir", "asc"),
            ("limit", "250"),
        ]
        if next_cursor:
            params.append(("next", next_cursor))
        resp = requests.get(
            f"{API_BASE}/events",
            headers=auth_headers(),
            params=params,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise SystemExit(
                f"Failed to list events: {resp.status_code} {resp.text}"
            )
        body = resp.json()
        events.extend(body.get("models", []) or [])
        next_cursor = (body.get("pagination") or {}).get("next")
        if not next_cursor:
            return events


def main() -> int:
    if os.path.exists(SEED_PATH):
        print(f"{SEED_PATH} already exists; seed step is a no-op.")
        return 0

    run_id = safe_run_id()
    source_name = f"qwin-{run_id}"
    dest_name = f"qwin-dst-{run_id}"
    conn_name = f"qwin-conn-{run_id}"

    print(f"[seed] Upserting Hookdeck connection {conn_name!r}...", flush=True)
    conn = upsert_connection(source_name, dest_name, conn_name)
    source_id = conn["source"]["id"]
    source_url = conn["source"]["url"]
    print(f"[seed] Source id={source_id} url={source_url}", flush=True)

    print(f"[seed] Publishing {TOTAL_EVENTS} events...", flush=True)
    publish_events(source_url, run_id)

    print(f"[seed] Waiting {PROPAGATION_WAIT}s for ingestion...", flush=True)
    time.sleep(PROPAGATION_WAIT)

    events: list[dict] = []
    for attempt in range(1, LIST_RETRIES + 1):
        events = list_all_events(source_id)
        print(f"[seed] Attempt {attempt}: {len(events)}/{TOTAL_EVENTS} events visible", flush=True)
        if len(events) >= TOTAL_EVENTS:
            break
        time.sleep(LIST_RETRY_WAIT)

    if len(events) < TOTAL_EVENTS:
        raise SystemExit(
            f"Only {len(events)}/{TOTAL_EVENTS} events became visible after seeding."
        )

    # `order_by=created_at&dir=asc` keeps timeline order.
    events = events[:TOTAL_EVENTS]
    middle_start_idx = 5
    middle_end_idx = 10  # exclusive
    middle = events[middle_start_idx:middle_end_idx]

    seed_doc = {
        "source_id": source_id,
        "source_name": source_name,
        "window_start": middle[0]["created_at"],
        "window_end": middle[-1]["created_at"],
        "expected_ids": [e["id"] for e in middle],
        "all_event_ids": [e["id"] for e in events],
    }

    os.makedirs(os.path.dirname(SEED_PATH), exist_ok=True)
    tmp = SEED_PATH + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(seed_doc, fh, indent=2)
    os.replace(tmp, SEED_PATH)
    print(f"[seed] Wrote {SEED_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
PYEOF

RUN chmod +x /opt/hookdeck-seed/seed.py

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck CLI + REST API environment seeded with 15 events for time-window query verification."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 for installing the Hookdeck CLI
#   - hookdeck-cli installed globally via npm
#   - requests installed via pip3 for both seeding and verification
#   - /workspace: project root where the candidate writes query.py and window.json
#   - /opt/hookdeck-seed/seed.py: idempotent seeder invoked from test_initial_state.py
