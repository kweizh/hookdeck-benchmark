import os
import requests

def test_output_log_exists():
    log_file = "/home/user/hookdeck-task/output.log"
    assert os.path.isfile(log_file), f"Log file {log_file} does not exist."

def test_connection_created_in_hookdeck():
    run_id = os.environ.get("ZEALT_RUN_ID")
    assert run_id, "ZEALT_RUN_ID environment variable is not set."
    
    api_key = os.environ.get("HOOKDECK_API_KEY")
    assert api_key, "HOOKDECK_API_KEY environment variable is not set."

    expected_conn_name = f"stripe-to-mock-{run_id}"
    expected_source_name = f"stripe-{run_id}"
    expected_dest_name = f"mock-dest-{run_id}"

    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    response = requests.get(
        "https://api.hookdeck.com/2025-07-01/connections",
        headers=headers,
        params={"name": expected_conn_name}
    )
    
    assert response.status_code == 200, f"Failed to list connections: {response.text}"
    
    data = response.json()
    models = data.get("models", [])
    
    connection = next((conn for conn in models if conn.get("name") == expected_conn_name), None)
    assert connection is not None, f"Connection with name '{expected_conn_name}' not found."
    
    source = connection.get("source", {})
    destination = connection.get("destination", {})
    
    assert source.get("name") == expected_source_name, \
        f"Expected source name '{expected_source_name}', got '{source.get('name')}'"
    
    assert source.get("type", "").lower() == "stripe", \
        f"Expected source type 'stripe', got '{source.get('type')}'"
        
    assert destination.get("name") == expected_dest_name, \
        f"Expected destination name '{expected_dest_name}', got '{destination.get('name')}'"
        
    assert destination.get("type", "").lower() in ["mock", "mock_api"], \
        f"Expected destination type 'mock', got '{destination.get('type')}'"