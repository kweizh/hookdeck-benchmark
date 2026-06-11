import os
import subprocess
import time
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"

def test_hookdeck_transformation_flow():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is not set."
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is not set."

    # Run setup.sh
    setup_script = os.path.join(PROJECT_DIR, "setup.sh")
    assert os.path.isfile(setup_script), "setup.sh not found."
    
    result = subprocess.run(["bash", "setup.sh"], cwd=PROJECT_DIR, capture_output=True, text=True)
    assert result.returncode == 0, f"setup.sh failed with error: {result.stderr}"

    # Wait a bit for the resources to be fully available
    time.sleep(2)

    source_name = f"source-{run_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    sources_resp = requests.get("https://api.hookdeck.com/2025-07-01/sources", headers=headers)
    assert sources_resp.status_code == 200, f"Failed to list sources: {sources_resp.text}"
    sources = sources_resp.json().get("models", [])
    
    source_id = None
    for s in sources:
        if s.get("name") == source_name:
            source_id = s.get("id")
            break
            
    assert source_id is not None, f"Source named {source_name} not found."

    # Publish event
    publish_url = "https://hkdk.events/v1/publish"
    publish_headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Hookdeck-Source-Name": source_name,
        "Content-Type": "application/json"
    }
    test_payload = {
        "data": {
            "object": {
                "flattened": True,
                "test_id": run_id
            }
        }
    }
    
    pub_resp = requests.post(publish_url, headers=publish_headers, json=test_payload)
    assert pub_resp.status_code == 200, f"Failed to publish event: {pub_resp.text}"

    # Wait for processing
    time.sleep(5)

    # Inspect events
    inspect_url = f"https://api.hookdeck.com/2025-07-01/events?source_id={source_id}&status=SUCCESSFUL"
    inspect_resp = requests.get(inspect_url, headers=headers)
    assert inspect_resp.status_code == 200, f"Failed to get events: {inspect_resp.text}"
    
    events = inspect_resp.json().get("models", [])
    assert len(events) > 0, "No successful events found for the source."
    
    # Find the event with our test_id
    found_transformed = False
    for event in events:
        body = event.get("body", {})
        if body.get("test_id") == run_id:
            assert body.get("flattened") is True, f"Payload was not flattened correctly. Got body: {body}"
            found_transformed = True
            break
            
    assert found_transformed, "Could not find the successfully transformed event with the expected test_id."
