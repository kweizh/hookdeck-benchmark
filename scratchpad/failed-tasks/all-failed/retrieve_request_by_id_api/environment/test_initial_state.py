import os
import time
import urllib.request
import urllib.parse
import json
import pytest

PROJECT_DIR = "/home/user/hookdeck-task"

def test_project_dir_exists():
    assert os.path.isdir(PROJECT_DIR), f"Project directory {PROJECT_DIR} does not exist."

def test_hookdeck_api_key_set():
    assert "HOOKDECK_API_KEY" in os.environ, "HOOKDECK_API_KEY is not set in environment."

def test_target_request_id_prepared():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    if not api_key:
        pytest.skip("HOOKDECK_API_KEY not set")
        
    # Publish an event to ensure there is at least one request
    publish_req = urllib.request.Request(
        "https://hkdk.events/v1/publish",
        data=json.dumps({"event": "test.created", "data": {"id": 123}}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "X-Hookdeck-Source-Name": "my-source",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        urllib.request.urlopen(publish_req)
    except Exception as e:
        print(f"Failed to publish event: {e}")
        
    time.sleep(2) # Wait for ingestion
    
    # Fetch the latest request
    req = urllib.request.Request(
        "https://api.hookdeck.com/2025-07-01/requests?limit=1",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            models = data.get("models", [])
            assert len(models) > 0, "No requests found in Hookdeck workspace."
            request_id = models[0]["id"]
            
            # Export to .bashrc so the agent has it
            bashrc_path = "/home/user/.bashrc"
            with open(bashrc_path, "a") as f:
                f.write(f'\nexport TARGET_REQUEST_ID="{request_id}"\n')
                
            # Also set it in the current environment for subsequent tests if any
            os.environ["TARGET_REQUEST_ID"] = request_id
    except Exception as e:
        pytest.fail(f"Failed to fetch requests to prepare TARGET_REQUEST_ID: {e}")
