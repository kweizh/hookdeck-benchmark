#!/usr/bin/env bash
set -euo pipefail

# Read the run-id from the environment
RUN_ID="${ZEALT_RUN_ID:?ZEALT_RUN_ID environment variable must be set}"

# Helper function to extract a JSON field using python3
extract_id() {
    python3 -c "import sys, json; print(json.load(sys.stdin)['id'])"
}

echo "==> Authenticating with Hookdeck..."
hookdeck ci --api-key "$HOOKDECK_API_KEY"

echo "==> Creating Source: source-${RUN_ID}..."
SOURCE_OUTPUT=$(hookdeck gateway source create \
  --name "source-${RUN_ID}" \
  --type WEBHOOK \
  --output json)
SOURCE_ID=$(echo "$SOURCE_OUTPUT" | extract_id)
echo "    Source ID: ${SOURCE_ID}"

echo "==> Creating Mock Destination: dest-${RUN_ID}..."
DEST_OUTPUT=$(hookdeck gateway destination create \
  --name "dest-${RUN_ID}" \
  --type MOCK_API \
  --output json)
DEST_ID=$(echo "$DEST_OUTPUT" | extract_id)
echo "    Destination ID: ${DEST_ID}"

echo "==> Creating Transformation: flatten-${RUN_ID}..."
TRANSFORM_CODE='addHandler("transform", (request, context) => {
  if (request.body && request.body.data && request.body.data.object) {
    request.body = request.body.data.object;
  }
  return request;
});'

TRANSFORM_OUTPUT=$(hookdeck gateway transformation create \
  --name "flatten-${RUN_ID}" \
  --code "$TRANSFORM_CODE" \
  --output json)
TRANSFORM_ID=$(echo "$TRANSFORM_OUTPUT" | extract_id)
echo "    Transformation ID: ${TRANSFORM_ID}"

echo "==> Creating Connection: conn-${RUN_ID}..."
CONN_OUTPUT=$(hookdeck gateway connection create \
  --name "conn-${RUN_ID}" \
  --source-id "$SOURCE_ID" \
  --destination-id "$DEST_ID" \
  --rule-transform-name "flatten-${RUN_ID}" \
  --output json)
CONN_ID=$(echo "$CONN_OUTPUT" | extract_id)
echo "    Connection ID: ${CONN_ID}"

echo ""
echo "==> Setup complete!"
echo "    Source:         source-${RUN_ID} (${SOURCE_ID})"
echo "    Destination:    dest-${RUN_ID} (${DEST_ID})"
echo "    Transformation: flatten-${RUN_ID} (${TRANSFORM_ID})"
echo "    Connection:     conn-${RUN_ID} (${CONN_ID})"
