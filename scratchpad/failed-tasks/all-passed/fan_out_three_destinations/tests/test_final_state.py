import os
import requests
import pytest

def get_api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is missing"
    return api_key

def get_run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is missing"
    return run_id

def get_headers():
    return {
        "Authorization": f"Bearer {get_api_key()}"
    }

def test_source_exists():
    run_id = get_run_id()
    expected_name = f"fanout-source-{run_id}"
    
    url = "https://api.hookdeck.com/2025-07-01/sources"
    response = requests.get(url, headers=get_headers())
    assert response.status_code == 200, f"Failed to fetch sources: {response.text}"
    
    data = response.json()
    sources = data.get("models", [])
    
    source_names = [s.get("name") for s in sources]
    assert expected_name in source_names, f"Expected source {expected_name} not found. Available sources: {source_names}"

def test_destinations_exist_with_correct_configs():
    run_id = get_run_id()
    expected_mock1 = f"mock-dest-1-{run_id}"
    expected_mock2 = f"mock-dest-2-{run_id}"
    expected_cli = f"cli-dest-{run_id}"
    
    url = "https://api.hookdeck.com/2025-07-01/destinations"
    response = requests.get(url, headers=get_headers())
    assert response.status_code == 200, f"Failed to fetch destinations: {response.text}"
    
    data = response.json()
    destinations = data.get("models", [])
    
    # Store by name for easy lookup
    dests_by_name = {d.get("name"): d for d in destinations}
    
    # Check mock 1
    assert expected_mock1 in dests_by_name, f"Expected destination {expected_mock1} not found"
    mock1 = dests_by_name[expected_mock1]
    assert mock1.get("type") == "MOCK_API", f"Expected {expected_mock1} type to be MOCK_API, got {mock1.get('type')}"
    assert mock1.get("config", {}).get("rate_limit") == 10, f"Expected {expected_mock1} rate_limit to be 10"
    assert mock1.get("config", {}).get("rate_limit_period") == "second", f"Expected {expected_mock1} rate_limit_period to be second"
    
    # Check mock 2
    assert expected_mock2 in dests_by_name, f"Expected destination {expected_mock2} not found"
    mock2 = dests_by_name[expected_mock2]
    assert mock2.get("type") == "MOCK_API", f"Expected {expected_mock2} type to be MOCK_API, got {mock2.get('type')}"
    assert mock2.get("config", {}).get("rate_limit") == 5, f"Expected {expected_mock2} rate_limit to be 5"
    assert mock2.get("config", {}).get("rate_limit_period") == "minute", f"Expected {expected_mock2} rate_limit_period to be minute"
    
    # Check cli
    assert expected_cli in dests_by_name, f"Expected destination {expected_cli} not found"
    cli_dest = dests_by_name[expected_cli]
    assert cli_dest.get("type") == "CLI", f"Expected {expected_cli} type to be CLI, got {cli_dest.get('type')}"

def test_connections_exist():
    run_id = get_run_id()
    expected_source = f"fanout-source-{run_id}"
    expected_dests = [
        f"mock-dest-1-{run_id}",
        f"mock-dest-2-{run_id}",
        f"cli-dest-{run_id}"
    ]
    
    url = "https://api.hookdeck.com/2025-07-01/connections"
    response = requests.get(url, headers=get_headers())
    assert response.status_code == 200, f"Failed to fetch connections: {response.text}"
    
    data = response.json()
    connections = data.get("models", [])
    
    # Check connections for the specific source
    source_conns = [c for c in connections if c.get("source", {}).get("name") == expected_source]
    
    connected_dests = [c.get("destination", {}).get("name") for c in source_conns]
    
    for dest in expected_dests:
        assert dest in connected_dests, f"Expected connection from {expected_source} to {dest} not found. Found connections to: {connected_dests}"
