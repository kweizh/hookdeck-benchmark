#!/bin/bash
# Hookdeck JS Transformation Setup Script
# Creates a Hookdeck connection with a JS transformation that:
#   1. Renames old_key -> new_key in the JSON body
#   2. Adds x-custom-secret header from MY_SECRET_ENV environment variable

set -e

RUN_ID="${ZEALT_RUN_ID}"
echo "Setting up Hookdeck resources for RUN_ID: $RUN_ID"

# Step 1: Create the webhook source
echo ""
echo "=== Creating Source: webhook-source-${RUN_ID} ==="
SOURCE_RESPONSE=$(curl -s -X POST "https://api.hookdeck.com/2025-01-01/sources" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"webhook-source-${RUN_ID}\", \"type\": \"WEBHOOK\"}")
SOURCE_ID=$(echo "$SOURCE_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Source created: $SOURCE_ID"

# Step 2: Create the mock destination
echo ""
echo "=== Creating Destination: mock-dest-${RUN_ID} ==="
DEST_RESPONSE=$(curl -s -X POST "https://api.hookdeck.com/2025-01-01/destinations" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"mock-dest-${RUN_ID}\", \"type\": \"MOCK_API\"}")
DEST_ID=$(echo "$DEST_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Destination created: $DEST_ID"

# Step 3: Create the transformation
echo ""
echo "=== Creating Transformation: transform-${RUN_ID} ==="
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

result = subprocess.run(
    ["curl", "-s", "-X", "POST",
     "https://api.hookdeck.com/2025-01-01/transformations",
     "-H", f"Authorization: Bearer {api_key}",
     "-H", "Content-Type: application/json",
     "-d", json.dumps(payload)],
    capture_output=True, text=True
)

data = json.loads(result.stdout)
print(f"Transformation created: {data['id']}")
print(f"ENV: {data.get('env', {})}")

with open("/tmp/hookdeck_transform_id.txt", "w") as f:
    f.write(data["id"])
PYEOF

TRANSFORM_ID=$(cat /tmp/hookdeck_transform_id.txt)

# Step 4: Create the connection with transformation rule
echo ""
echo "=== Creating Connection: transform-connection-${RUN_ID} ==="
CONNECTION_RESPONSE=$(curl -s -X POST "https://api.hookdeck.com/2025-01-01/connections" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"transform-connection-${RUN_ID}\",
    \"source_id\": \"${SOURCE_ID}\",
    \"destination_id\": \"${DEST_ID}\",
    \"rules\": [
      {
        \"type\": \"transform\",
        \"transformation_id\": \"${TRANSFORM_ID}\"
      }
    ]
  }")
CONNECTION_ID=$(echo "$CONNECTION_RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
echo "Connection created: $CONNECTION_ID"

echo ""
echo "=== Setup Complete ==="
echo "Source:          webhook-source-${RUN_ID} (${SOURCE_ID})"
echo "Destination:     mock-dest-${RUN_ID} (${DEST_ID})"
echo "Transformation:  transform-${RUN_ID} (${TRANSFORM_ID})"
echo "Connection:      transform-connection-${RUN_ID} (${CONNECTION_ID})"
