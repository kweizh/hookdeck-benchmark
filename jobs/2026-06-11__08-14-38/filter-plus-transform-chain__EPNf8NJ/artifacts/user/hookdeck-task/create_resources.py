import os
import requests
import json

api_key = os.environ.get("HOOKDECK_API_KEY")
run_id = os.environ.get("ZEALT_RUN_ID")

if not api_key:
    print("Error: HOOKDECK_API_KEY environment variable is not set.")
    exit(1)

if not run_id:
    print("Error: ZEALT_RUN_ID environment variable is not set.")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

base_url = "https://api.hookdeck.com/2025-07-01"

# 1. Create Transformation
transform_name = f"chain-trans-{run_id}"
transform_code = """addHandler("transform", (request, context) => {
  if (!request.body) {
    request.body = {};
  }
  request.body.processed_at = new Date().toISOString();
  if (!request.headers) {
    request.headers = {};
  }
  request.headers["x-processed"] = "true";
  return request;
});"""

print(f"Creating transformation: {transform_name}")
transform_payload = {
    "name": transform_name,
    "code": transform_code
}

res = requests.post(f"{base_url}/transformations", headers=headers, json=transform_payload)
print(f"Transformation status: {res.status_code}")
print(res.text)

if res.status_code in [200, 201]:
    transformation_id = res.json()["id"]
elif res.status_code == 409:
    transformation_id = res.json()["data"]["transformation"]["id"]
    print(f"Reusing existing transformation: {transformation_id}")
else:
    print("Failed to create transformation")
    exit(1)

print(f"Created/Reused Transformation ID: {transformation_id}")

# 2. Create Connection (which creates Source and Destination inline)
connection_name = f"chain-conn-{run_id}"
source_name = f"chain-src-{run_id}"
destination_name = f"chain-dest-{run_id}"

connection_payload = {
    "name": connection_name,
    "source": {
        "name": source_name,
        "type": "WEBHOOK"
    },
    "destination": {
        "name": destination_name,
        "type": "MOCK_API"
    },
    "rules": [
        {
            "type": "filter",
            "body": {
                "type": "order.created"
            }
        },
        {
            "type": "transform",
            "transformation_id": transformation_id
        }
    ]
}

print(f"Creating connection: {connection_name}")
res_conn = requests.post(f"{base_url}/connections", headers=headers, json=connection_payload)
print(f"Connection status: {res_conn.status_code}")
print(res_conn.text)

if res_conn.status_code not in [200, 201]:
    print("Failed to create connection")
    exit(1)

conn_data = res_conn.json()
connection_id = conn_data["id"]
print(f"Created Connection ID: {connection_id}")
