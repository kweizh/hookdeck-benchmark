import os
import re
import time
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"
LOG_FILE = os.path.join(PROJECT_DIR, "output.log")
API_BASE = "https://api.hookdeck.com/2025-07-01"


def _read_source_id_from_log() -> str:
    assert os.path.isfile(LOG_FILE), f"Log file not found at {LOG_FILE}"
    with open(LOG_FILE, "r") as f:
        content = f.read()
    match = re.search(r"Source ID:\s*(src_[A-Za-z0-9]+)", content)
    assert match, (
        f"Could not find a line matching 'Source ID: <id>' in log file. File content: {content!r}"
    )
    return match.group(1).strip()


def _auth_headers() -> dict:
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    return {"Authorization": f"Bearer {api_key}"}


def test_source_exists_with_shopify_verification():
    """Verify the Source was created with SHOPIFY type and signature verification enabled."""
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."

    source_id = _read_source_id_from_log()

    response = requests.get(f"{API_BASE}/sources/{source_id}", headers=_auth_headers())
    assert response.status_code == 200, (
        f"Failed to retrieve source {source_id}. "
        f"Status: {response.status_code}, Body: {response.text}"
    )
    data = response.json()

    expected_name = f"shopify-verify-{run_id}"
    assert data.get("name") == expected_name, (
        f"Expected source name '{expected_name}', got '{data.get('name')}'."
    )
    assert data.get("type") == "SHOPIFY", (
        f"Expected source type 'SHOPIFY', got '{data.get('type')}'."
    )
    assert data.get("authenticated") is True, (
        "Source must have signature verification configured "
        f"(field 'authenticated' should be true). Got source payload: {data}"
    )


def test_signed_and_tampered_requests_are_recorded_with_correct_verification():
    """
    Verify via the Inspect API that:
      - at least 2 requests were ingested for the Source,
      - at least one request has verified == true,
      - at least one request has verified == false AND rejection_cause == 'VERIFICATION_FAILED'.
    """
    source_id = _read_source_id_from_log()

    deadline = time.time() + 30.0
    models = []
    last_status = None
    last_body = None
    while time.time() < deadline:
        response = requests.get(
            f"{API_BASE}/requests",
            headers=_auth_headers(),
            params={"source_id": source_id, "limit": 50},
        )
        last_status = response.status_code
        last_body = response.text
        if response.status_code == 200:
            models = response.json().get("models", []) or []
            if len(models) >= 2:
                break
        time.sleep(2)

    assert last_status == 200, (
        f"Failed to list requests for source {source_id}. "
        f"Last status: {last_status}, Body: {last_body}"
    )
    assert len(models) >= 2, (
        f"Expected at least 2 ingested requests for source {source_id}, "
        f"got {len(models)}. Models: {models}"
    )

    verified_true = [m for m in models if m.get("verified") is True]
    verified_failed = [
        m
        for m in models
        if m.get("verified") is False and m.get("rejection_cause") == "VERIFICATION_FAILED"
    ]

    assert len(verified_true) >= 1, (
        "Expected at least one request with verified == true "
        "(the correctly Shopify-HMAC-signed request). "
        f"Got models: {models}"
    )
    assert len(verified_failed) >= 1, (
        "Expected at least one request with verified == false AND "
        "rejection_cause == 'VERIFICATION_FAILED' (the tampered/unsigned request). "
        f"Got models: {models}"
    )
