import os
import requests
import pytest

def test_connection_exists_and_configured_correctly():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."
    
    conn_name = f"cli-forward-conn-{run_id}"
    url = f"https://api.hookdeck.com/2025-07-01/connections?name={conn_name}"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"API request failed with status {response.status_code}: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    
    assert len(models) > 0, f"Connection {conn_name} not found."
    
    connection = models[0]
    assert connection.get("name") == conn_name, f"Expected connection name {conn_name}, got {connection.get('name')}"
    
    source = connection.get("source", {})
    expected_source_name = f"my-source-{run_id}"
    assert source.get("name") == expected_source_name, f"Expected source name {expected_source_name}, got {source.get('name')}"
    
    destination = connection.get("destination", {})
    expected_dest_name = f"my-cli-dest-{run_id}"
    assert destination.get("name") == expected_dest_name, f"Expected destination name {expected_dest_name}, got {destination.get('name')}"
    
    assert destination.get("cli_path") == "/api/webhooks", f"Expected destination cli_path /api/webhooks, got {destination.get('cli_path')}"
