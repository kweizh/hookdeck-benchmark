#!/bin/bash
set -euo pipefail

PROJECT_DIR="/home/user/hookdeck-task"
LOG_FILE="${PROJECT_DIR}/output.log"

RUN_ID="${ZEALT_RUN_ID:?ZEALT_RUN_ID environment variable is required}"
SOURCE_NAME="test-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"

echo "=== Hookdeck Event Verification Script ==="
echo "Run ID: ${RUN_ID}"
echo "Source Name: ${SOURCE_NAME}"
echo "Destination Name: ${DEST_NAME}"

# Step 1: Authenticate with Hookdeck in headless CI environment
echo "--- Step 1: Authenticating with Hookdeck CI ---"
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Step 2: Create a connection linking the source to a Mock API destination
echo "--- Step 2: Creating connection ---"
CONNECTION_OUTPUT=$(hookdeck connection create \
  --name "${SOURCE_NAME}-connection" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST_NAME}" \
  --destination-type MOCK_API \
  --output json)

echo "Connection created: ${CONNECTION_OUTPUT}"

# Step 3: Get the source_id from the connection output or via REST API
echo "--- Step 3: Getting source ID ---"
SOURCE_ID=$(echo "$CONNECTION_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['id'])" 2>/dev/null || echo "")

if [ -z "$SOURCE_ID" ]; then
  echo "Could not extract source_id from connection output, trying REST API..."
  # Use REST API to look up the source by name
  SOURCE_ID=$(curl -s -X GET "https://api.hookdeck.com/2025-07-01/sources?name=${SOURCE_NAME}" \
    -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
    -H "Content-Type: application/json" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['models'][0]['id'])")
fi

echo "Source ID: ${SOURCE_ID}"

# Step 4: Trigger a mock event to the source using the Publish API
echo "--- Step 4: Publishing event via Publish API ---"
PUBLISH_RESPONSE=$(curl -s -X POST "https://hkdk.events/v1/publish" \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "X-Hookdeck-Source-Id: ${SOURCE_ID}" \
  -d '{"message": "test event from verify_event.sh", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}')

echo "Publish response: ${PUBLISH_RESPONSE}"

# Step 5: Query events for the source using the Inspect API to verify delivery status
echo "--- Step 5: Querying events to verify SUCCESSFUL status ---"

# Poll for the event to become SUCCESSFUL (with retries)
MAX_RETRIES=30
RETRY_INTERVAL=5
EVENT_ID=""

for i in $(seq 1 $MAX_RETRIES); do
  echo "Attempt ${i}/${MAX_RETRIES}..."

  # Use the REST API to query events for this source with SUCCESSFUL status
  EVENTS_RESPONSE=$(curl -s -X GET "https://api.hookdeck.com/2025-07-01/events?source_id=${SOURCE_ID}&status=SUCCESSFUL" \
    -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
    -H "Content-Type: application/json")

  # Check if we got any successful events
  EVENT_COUNT=$(echo "$EVENTS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('models', [])))" 2>/dev/null || echo "0")

  if [ "$EVENT_COUNT" != "0" ]; then
    EVENT_ID=$(echo "$EVENTS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['models'][0]['id'])")
    echo "Found successful event! Event ID: ${EVENT_ID}"
    break
  fi

  echo "No successful events yet, waiting ${RETRY_INTERVAL}s..."
  sleep $RETRY_INTERVAL
done

if [ -z "$EVENT_ID" ]; then
  echo "ERROR: Could not find a SUCCESSFUL event after ${MAX_RETRIES} attempts"
  # Try listing all events for this source regardless of status
  echo "All events for source ${SOURCE_ID}:"
  curl -s -X GET "https://api.hookdeck.com/2025-07-01/events?source_id=${SOURCE_ID}" \
    -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
    -H "Content-Type: application/json" | python3 -m json.tool 2>/dev/null || true
  exit 1
fi

# Step 6: Write the successful event ID to the log file
echo "--- Step 6: Writing event ID to log file ---"
mkdir -p "$(dirname "$LOG_FILE")"
echo "Event ID: ${EVENT_ID}" > "$LOG_FILE"

echo "=== Verification Complete ==="
echo "Event ID: ${EVENT_ID} written to ${LOG_FILE}"
cat "$LOG_FILE"