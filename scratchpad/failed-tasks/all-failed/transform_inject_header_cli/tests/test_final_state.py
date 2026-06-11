import os
import requests
import pytest

def get_env_vars():
    run_id = os.environ.get("ZEALT_RUN_ID")
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert run_id, "ZEALT_RUN_ID environment variable is missing"
    assert api_key, "HOOKDECK_API_KEY environment variable is missing"
    return run_id, api_key

def test_connection_exists_and_configured():
    run_id, api_key = get_env_vars()
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # Check Connection
    conn_name = f"header-conn-{run_id}"
    url = f"https://api.hookdeck.com/2025-07-01/connections?name={conn_name}"
    resp = requests.get(url, headers=headers)
    assert resp.status_code == 200, f"Failed to fetch connections: {resp.text}"
    
    data = resp.json()
    assert data.get("count", 0) > 0, f"Connection '{conn_name}' not found."
    
    models = data.get("models", [])
    conn = models[0]
    
    # Verify Source and Destination
    source = conn.get("source", {})
    destination = conn.get("destination", {})
    
    assert source.get("name") == f"source-{run_id}", f"Expected source name 'source-{run_id}', got {source.get('name')}"
    assert destination.get("name") == f"mock-dest-{run_id}", f"Expected destination name 'mock-dest-{run_id}', got {destination.get('name')}"
    
    # Verify Destination Type via Destination object
    # In Hookdeck API, the destination type might be in the destination object or we can fetch it separately
    dest_url = f"https://api.hookdeck.com/2025-07-01/destinations?name=mock-dest-{run_id}"
    dest_resp = requests.get(dest_url, headers=headers)
    assert dest_resp.status_code == 200, f"Failed to fetch destinations: {dest_resp.text}"
    dest_data = dest_resp.json()
    assert dest_data.get("count", 0) > 0, f"Destination 'mock-dest-{run_id}' not found."
    dest_model = dest_data.get("models", [])[0]
    
    # Check destination type (could be "MOCK" or similar depending on Hookdeck API, mock-api etc)
    # The requirement says type MOCK
    # We will check if it's CLI or MOCK but we specifically requested MOCK
    # The actual API might return 'cli' or 'mock'
    assert dest_model.get("type", "").upper() == "MOCK", f"Expected destination type MOCK, got {dest_model.get('type')}"
    
    # Verify Transformation
    rules = conn.get("rules", [])
    transformation_rule = None
    for rule in rules:
        if rule.get("type") == "transform":
            transformation_rule = rule
            break
            
    assert transformation_rule is not None, "No transformation rule found on the connection."
    
    # The rule contains transformation ID
    transform_id = transformation_rule.get("transformation_id")
    assert transform_id, "Transformation rule does not have a transformation_id."
    
    # Fetch Transformation Code
    transform_url = f"https://api.hookdeck.com/2025-07-01/transformations/{transform_id}"
    trans_resp = requests.get(transform_url, headers=headers)
    assert trans_resp.status_code == 200, f"Failed to fetch transformation: {trans_resp.text}"
    
    trans_data = trans_resp.json()
    assert trans_data.get("name") == f"inject-header-{run_id}", f"Expected transformation name 'inject-header-{run_id}', got {trans_data.get('name')}"
    
    code = trans_data.get("code", "")
    assert "request.headers" in code, "Transformation code does not modify request.headers"
    assert "x-custom-run-id" in code.lower(), "Transformation code does not inject 'x-custom-run-id' header"
    assert run_id in code, f"Transformation code does not contain the run-id '{run_id}'"
