import os
import json
import pytest
import requests

PROJECT_DIR = "/home/user/hookdeck-task"
API_KEY = os.environ.get("HOOKDECK_API_KEY", "")
BASE_URL = "https://api.hookdeck.com/2025-07-01"

@pytest.fixture(scope="session")
def run_id():
    return os.environ.get("ZEALT_RUN_ID", "")

@pytest.fixture(scope="session")
def headers():
    return {"Authorization": f"Bearer {API_KEY}"}

def test_output_json_exists_and_valid(run_id):
    output_file = os.path.join(PROJECT_DIR, "output.json")
    assert os.path.isfile(output_file), f"Output file {output_file} does not exist."
    with open(output_file, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            pytest.fail("Output file is not valid JSON.")
    
    assert "connections" in data, "Key 'connections' missing in output.json."
    connections = data["connections"]
    assert type(connections) == list, "'connections' must be a list."
    assert f"conn-1-{run_id}" in connections, f"conn-1-{run_id} not found in connections array."
    assert f"conn-2-{run_id}" in connections, f"conn-2-{run_id} not found in connections array."

def test_source_created(run_id, headers):
    source_name = f"fanout-source-{run_id}"
    res = requests.get(f"{BASE_URL}/sources?name={source_name}", headers=headers)
    assert res.status_code == 200, f"Failed to fetch sources: {res.text}"
    data = res.json()
    assert data.get("count", 0) == 1, f"Expected exactly 1 source named {source_name}, found {data.get('count', 0)}."

def test_destinations_created(run_id, headers):
    for dest_name in [f"mock-dest-1-{run_id}", f"mock-dest-2-{run_id}"]:
        res = requests.get(f"{BASE_URL}/destinations?name={dest_name}", headers=headers)
        assert res.status_code == 200, f"Failed to fetch destination {dest_name}: {res.text}"
        data = res.json()
        assert data.get("count", 0) == 1, f"Expected exactly 1 destination named {dest_name}, found {data.get('count', 0)}."

def test_connections_created(run_id, headers):
    source_name = f"fanout-source-{run_id}"
    res_source = requests.get(f"{BASE_URL}/sources?name={source_name}", headers=headers).json()
    assert res_source.get("count", 0) > 0, f"Source {source_name} not found."
    source_id = res_source["models"][0]["id"]
    
    dest1_name = f"mock-dest-1-{run_id}"
    res_dest1 = requests.get(f"{BASE_URL}/destinations?name={dest1_name}", headers=headers).json()
    assert res_dest1.get("count", 0) > 0, f"Destination {dest1_name} not found."
    dest1_id = res_dest1["models"][0]["id"]
    
    dest2_name = f"mock-dest-2-{run_id}"
    res_dest2 = requests.get(f"{BASE_URL}/destinations?name={dest2_name}", headers=headers).json()
    assert res_dest2.get("count", 0) > 0, f"Destination {dest2_name} not found."
    dest2_id = res_dest2["models"][0]["id"]
    
    # Check connection 1
    conn1_name = f"conn-1-{run_id}"
    res_conn1 = requests.get(f"{BASE_URL}/connections?name={conn1_name}", headers=headers)
    assert res_conn1.status_code == 200
    data1 = res_conn1.json()
    assert data1.get("count", 0) == 1, f"Expected exactly 1 connection named {conn1_name}"
    conn1 = data1["models"][0]
    
    conn1_source_id = conn1.get("source_id") or conn1.get("source", {}).get("id")
    conn1_dest_id = conn1.get("destination_id") or conn1.get("destination", {}).get("id")
    assert conn1_source_id == source_id, f"{conn1_name} does not link to correct source."
    assert conn1_dest_id == dest1_id, f"{conn1_name} does not link to correct destination."
    
    # Check connection 2
    conn2_name = f"conn-2-{run_id}"
    res_conn2 = requests.get(f"{BASE_URL}/connections?name={conn2_name}", headers=headers)
    assert res_conn2.status_code == 200
    data2 = res_conn2.json()
    assert data2.get("count", 0) == 1, f"Expected exactly 1 connection named {conn2_name}"
    conn2 = data2["models"][0]
    
    conn2_source_id = conn2.get("source_id") or conn2.get("source", {}).get("id")
    conn2_dest_id = conn2.get("destination_id") or conn2.get("destination", {}).get("id")
    assert conn2_source_id == source_id, f"{conn2_name} does not link to correct source."
    assert conn2_dest_id == dest2_id, f"{conn2_name} does not link to correct destination."