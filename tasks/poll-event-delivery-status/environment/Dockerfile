FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g hookdeck-cli && \
    pip3 install --break-system-packages pytest-json-ctrf requests && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/user && chmod 0755 /home/user
RUN mkdir -p /workspace && chmod 0755 /workspace
RUN mkdir -p /opt

# Seeding helper: creates a Hookdeck source, two destinations (one returning
# 200, one returning 500 via Hookdeck's Mock API), two connections (with
# retries disabled so the failing event reaches FAILED quickly), publishes a
# single event, then writes the resulting successful + failed event ids to
# /workspace/.seeded_events.env. The script is intended to be invoked by
# test_initial_state.py once at the start of the container's lifecycle.
RUN cat >/opt/seed_hookdeck_events.py <<'PYEOF'
#!/usr/bin/env python3
"""Seed Hookdeck with one SUCCESSFUL and one FAILED event for the
poll_event_delivery_status task."""

from __future__ import annotations

import json
import os
import sys
import time

import requests

API_BASE = "https://api.hookdeck.com/2025-07-01"
PUBLISH_URL = "https://hkdk.events/v1/publish"
SEEDED_ENV_FILE = "/workspace/.seeded_events.env"

TERMINAL_STATUSES = {"SUCCESSFUL", "FAILED"}


def _api_key() -> str:
    key = os.environ.get("HOOKDECK_API_KEY")
    if not key:
        print("HOOKDECK_API_KEY is not set", file=sys.stderr)
        sys.exit(2)
    return key


def _run_id() -> str:
    return os.environ.get("ZEALT_RUN_ID", "local").lower()


def _headers(key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _upsert_connection(key: str, body: dict) -> dict:
    r = requests.put(
        f"{API_BASE}/connections",
        headers=_headers(key),
        data=json.dumps(body),
        timeout=30,
    )
    if r.status_code >= 400:
        print(
            f"PUT /connections failed: {r.status_code} {r.text}",
            file=sys.stderr,
        )
        r.raise_for_status()
    return r.json()


def _publish(key: str, source_name: str, payload: dict) -> dict:
    headers = _headers(key)
    headers["X-Hookdeck-Source-Name"] = source_name
    r = requests.post(
        PUBLISH_URL,
        headers=headers,
        data=json.dumps(payload),
        timeout=30,
    )
    if r.status_code >= 400:
        print(
            f"Publish failed: {r.status_code} {r.text}",
            file=sys.stderr,
        )
        r.raise_for_status()
    return r.json()


def _wait_for_terminal_event(
    key: str,
    source_id: str,
    destination_id: str,
    not_before_iso: str,
    timeout_s: int = 120,
) -> dict:
    """Poll /events until a terminal event for (source, destination) appears."""
    deadline = time.time() + timeout_s
    last_seen: dict | None = None
    while time.time() < deadline:
        r = requests.get(
            f"{API_BASE}/events",
            headers=_headers(key),
            params={
                "source_id": source_id,
                "destination_id": destination_id,
                "created_at[gte]": not_before_iso,
                "limit": 20,
            },
            timeout=30,
        )
        r.raise_for_status()
        models = r.json().get("models", [])
        for evt in models:
            last_seen = evt
            if evt.get("status") in TERMINAL_STATUSES:
                return evt
        time.sleep(3)
    raise RuntimeError(
        "Timed out waiting for a terminal event for "
        f"source={source_id} destination={destination_id}; last_seen={last_seen}"
    )


def main() -> int:
    key = _api_key()
    run_id = _run_id()

    source_name = f"await-src-{run_id}"
    success_dest_name = f"await-success-dest-{run_id}"
    failure_dest_name = f"await-failure-dest-{run_id}"
    success_conn_name = f"await-success-conn-{run_id}"
    failure_conn_name = f"await-failure-conn-{run_id}"

    no_retry_rule = {
        "type": "retry",
        "strategy": "linear",
        "count": 0,
        "interval": 1000,
    }

    success_conn = _upsert_connection(
        key,
        {
            "name": success_conn_name,
            "source": {"name": source_name, "type": "WEBHOOK"},
            "destination": {
                "name": success_dest_name,
                "type": "HTTP",
                "config": {"url": "https://mock.hookdeck.com/example"},
            },
            "rules": [no_retry_rule],
        },
    )
    failure_conn = _upsert_connection(
        key,
        {
            "name": failure_conn_name,
            "source": {"name": source_name, "type": "WEBHOOK"},
            "destination": {
                "name": failure_dest_name,
                "type": "HTTP",
                "config": {"url": "https://mock.hookdeck.com/example?status=500"},
            },
            "rules": [no_retry_rule],
        },
    )

    source_id = success_conn["source"]["id"]
    success_dest_id = success_conn["destination"]["id"]
    failure_dest_id = failure_conn["destination"]["id"]

    # Stamp the publish time so we don't pick up older events from prior runs.
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    _publish(
        key,
        source_name,
        {"trigger": "await.test", "run_id": run_id, "published_at": now_iso},
    )

    success_evt = _wait_for_terminal_event(
        key, source_id, success_dest_id, now_iso
    )
    failure_evt = _wait_for_terminal_event(
        key, source_id, failure_dest_id, now_iso
    )

    if success_evt.get("status") != "SUCCESSFUL":
        print(
            f"Seeded success event ended in unexpected status: {success_evt}",
            file=sys.stderr,
        )
        return 3
    if failure_evt.get("status") != "FAILED":
        print(
            f"Seeded failure event ended in unexpected status: {failure_evt}",
            file=sys.stderr,
        )
        return 4

    os.makedirs(os.path.dirname(SEEDED_ENV_FILE), exist_ok=True)
    with open(SEEDED_ENV_FILE, "w") as f:
        f.write(f"SUCCESSFUL_EVENT_ID={success_evt['id']}\n")
        f.write(f"FAILED_EVENT_ID={failure_evt['id']}\n")
    print(
        f"Seeded: SUCCESSFUL_EVENT_ID={success_evt['id']} "
        f"FAILED_EVENT_ID={failure_evt['id']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
PYEOF

RUN chmod 0755 /opt/seed_hookdeck_events.py

LABEL Author="generate-harbor-tasks"
LABEL Description="Hookdeck poll_event_delivery_status: workspace with seed helper that creates one SUCCESSFUL and one FAILED Hookdeck event for the executor's script to poll."

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

# Container contents:
#   - always required apt packages: curl wget ca-certificates git python3 python3-pip python3-pytest bash ripgrep
#   - always required pip3 packages: pytest-json-ctrf
#   - Node.js v24 (for hookdeck CLI)
#   - hookdeck CLI (installed globally via npm)
#   - pip3 packages used by the verifier and seeding script: requests
#   - /workspace: empty working directory where the executor must create await_delivery.py
#   - /opt/seed_hookdeck_events.py: seeding helper invoked by test_initial_state.py to
#     create one SUCCESSFUL and one FAILED Hookdeck event and write their ids to
#     /workspace/.seeded_events.env (uses HOOKDECK_API_KEY and ZEALT_RUN_ID env vars).
