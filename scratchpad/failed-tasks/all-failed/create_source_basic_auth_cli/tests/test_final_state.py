import os
import json
import requests
import pytest

PROJECT_DIR = "/home/user/hookdeck-project"
SOURCE_JSON_PATH = os.path.join(PROJECT_DIR, "source.json")

@pytest.fixture
def run_id():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id is not None, "ZEALT_RUN_ID environment variable is missing"
    return run_id

@pytest.fixture
def api_key():
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key is not None, "HOOKDECK_API_KEY environment variable is missing"
    return api_key

@pytest.fixture
def source_id():
    assert os.path.exists(SOURCE_JSON_PATH), f"{SOURCE_JSON_PATH} does not exist"
    with open(SOURCE_JSON_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            pytest.fail(f"{SOURCE_JSON_PATH} does not contain valid JSON")
    
    assert "source_id" in data, "source_id field is missing in source.json"
    return data["source_id"]

def test_source_configuration(run_id, api_key, source_id):
    url = f"https://api.hookdeck.com/2025-07-01/sources/{source_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to retrieve source: {response.text}"
    
    source = response.json()
    expected_name = f"secure-source-{run_id}"
    assert source.get("name") == expected_name, f"Expected source name {expected_name}, got {source.get('name')}"
    
    config = source.get("config", {})
    assert config.get("auth_type") == "BASIC_AUTH", f"Expected auth_type BASIC_AUTH, got {config.get('auth_type')}"
    
    auth = config.get("auth", {})
    assert auth.get("username") == "admin", f"Expected username admin, got {auth.get('username')}"
    expected_password = f"secret-password-{run_id}"
    assert auth.get("password") == expected_password, f"Expected password {expected_password}, got {auth.get('password')}"

def test_connection_and_destination_configuration(run_id, api_key, source_id):
    url = f"https://api.hookdeck.com/2025-07-01/connections?source_id={source_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(url, headers=headers)
    assert response.status_code == 200, f"Failed to retrieve connections: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    
    expected_conn_name = f"secure-connection-{run_id}"
    connection = next((conn for conn in models if conn.get("name") == expected_conn_name), None)
    assert connection is not None, f"Connection {expected_conn_name} not found for source {source_id}"
    
    destination = connection.get("destination")
    assert destination is not None, "Connection does not have an associated destination"
    
    dest_id = destination.get("id")
    assert dest_id is not None, "Destination ID is missing"
    
    dest_url = f"https://api.hookdeck.com/2025-07-01/destinations/{dest_id}"
    dest_response = requests.get(dest_url, headers=headers)
    assert dest_response.status_code == 200, f"Failed to retrieve destination: {dest_response.text}"
    
    dest_data = dest_response.json()
    expected_dest_name = f"mock-dest-{run_id}"
    assert dest_data.get("name") == expected_dest_name, f"Expected destination name {expected_dest_name}, got {dest_data.get('name')}"
    
    # Destination type MOCK_API or HTTP with mock url
    dest_type = dest_data.get("type")
    assert dest_type == "MOCK_API" or (dest_type == "HTTP" and "mock.hookdeck.com" in dest_data.get("config", {}).get("url", "")), \
        f"Expected destination type MOCK_API or mock HTTP, got {dest_type}"
