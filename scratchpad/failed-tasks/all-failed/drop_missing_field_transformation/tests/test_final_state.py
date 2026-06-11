import os
import time
import requests
import pytest

LOG_FILE = "/home/user/hookdeck-task/output.log"

@pytest.fixture(scope="session")
def run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is not set"
    return run_id

@pytest.fixture(scope="session")
def api_key():
    key = os.environ.get("HOOKDECK_API_KEY")
    assert key is not None, "HOOKDECK_API_KEY environment variable is not set"
    return key

@pytest.fixture(scope="session")
def source_id():
    assert os.path.isfile(LOG_FILE), f"Log file {LOG_FILE} does not exist"
    with open(LOG_FILE, "r") as f:
        content = f.read()
    
    # Extract Source ID: <source_id>
    import re
    match = re.search(r"Source ID:\s*(src_[a-zA-Z0-9]+)", content)
    assert match is not None, f"Could not find 'Source ID: src_...' in {LOG_FILE}"
    return match.group(1)

def test_transformation_drops_missing_field(run_id, api_key, source_id):
    """Publish events and verify the transformation drops the one missing the required field."""
    
    publish_url = "https://hkdk.events/v1/publish"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": f"source-{run_id}",
        "Content-Type": "application/json"
    }

    # 1. Publish event WITHOUT required_field
    payload_missing = {"other_field": "value"}
    resp_missing = requests.post(publish_url, headers=headers, json=payload_missing)
    assert resp_missing.status_code == 200, f"Failed to publish event missing required field: {resp_missing.text}"

    # 2. Publish event WITH required_field
    payload_present = {"required_field": "value"}
    resp_present = requests.post(publish_url, headers=headers, json=payload_present)
    assert resp_present.status_code == 200, f"Failed to publish event with required field: {resp_present.text}"

    # Sleep to allow Hookdeck to process the events
    time.sleep(5)

    # 3. Retrieve requests for the source
    requests_url = f"https://api.hookdeck.com/2025-07-01/requests?source_id={source_id}"
    req_headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    resp_requests = requests.get(requests_url, headers=req_headers)
    assert resp_requests.status_code == 200, f"Failed to retrieve requests: {resp_requests.text}"
    
    data = resp_requests.json()
    models = data.get("models", [])
    
    # We expect at least 2 requests (the ones we just sent)
    # Find the one with other_field
    req_missing = next((r for r in models if r.get("data", {}).get("body", {}).get("body", {}).get("other_field") == "value"), None)
    assert req_missing is not None, "Could not find the request missing 'required_field' in Hookdeck"
    assert req_missing.get("ignored_count", 0) >= 1, f"Expected the request missing 'required_field' to be ignored, got ignored_count: {req_missing.get('ignored_count')}"
    assert req_missing.get("events_count", 0) == 0, f"Expected the request missing 'required_field' to NOT create an event, got events_count: {req_missing.get('events_count')}"

    # Find the one with required_field
    req_present = next((r for r in models if r.get("data", {}).get("body", {}).get("body", {}).get("required_field") == "value"), None)
    assert req_present is not None, "Could not find the request with 'required_field' in Hookdeck"
    assert req_present.get("events_count", 0) >= 1, f"Expected the request with 'required_field' to create an event, got events_count: {req_present.get('events_count')}"
    assert req_present.get("ignored_count", 0) == 0, f"Expected the request with 'required_field' to NOT be ignored, got ignored_count: {req_present.get('ignored_count')}"
