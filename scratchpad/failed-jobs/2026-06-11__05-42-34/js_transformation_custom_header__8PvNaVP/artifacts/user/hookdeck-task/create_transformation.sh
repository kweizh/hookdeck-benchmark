#!/bin/bash
set -e

RUN_ID="${ZEALT_RUN_ID}"
echo "Using RUN_ID: $RUN_ID"

# Create the transformation using a heredoc to handle the multiline code
TRANSFORM_CODE='addHandler('\''transform'\'', (request, context) => {
  // Rename old_key to new_key if it exists
  if (request.body && request.body.hasOwnProperty('\''old_key'\'')) {
    request.body.new_key = request.body.old_key;
    delete request.body.old_key;
  }

  // Add custom header from env var
  request.headers['\''x-custom-secret'\''] = context.env.MY_SECRET_ENV;

  return request;
});'

python3 - <<PYEOF
import json, os, subprocess

run_id = os.environ["ZEALT_RUN_ID"]
api_key = os.environ["HOOKDECK_API_KEY"]

code = """addHandler('transform', (request, context) => {
  // Rename old_key to new_key if it exists
  if (request.body && request.body.hasOwnProperty('old_key')) {
    request.body.new_key = request.body.old_key;
    delete request.body.old_key;
  }

  // Add custom header from env var
  request.headers['x-custom-secret'] = context.env.MY_SECRET_ENV;

  return request;
});"""

payload = {
    "name": f"transform-{run_id}",
    "code": code,
    "env": {
        "MY_SECRET_ENV": f"secret-val-{run_id}"
    }
}

payload_json = json.dumps(payload)

result = subprocess.run(
    ["curl", "-s", "-X", "POST",
     "https://api.hookdeck.com/2025-01-01/transformations",
     "-H", f"Authorization: Bearer {api_key}",
     "-H", "Content-Type: application/json",
     "-d", payload_json],
    capture_output=True, text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

data = json.loads(result.stdout)
print("\nTransformation ID:", data.get("id"))
print("Transformation Name:", data.get("name"))
print("ENV:", data.get("env"))

# Save transformation ID for next step
with open("/tmp/transform_id.txt", "w") as f:
    f.write(data["id"])
PYEOF
