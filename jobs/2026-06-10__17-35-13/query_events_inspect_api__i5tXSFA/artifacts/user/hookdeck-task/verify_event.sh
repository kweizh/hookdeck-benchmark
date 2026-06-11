#!/bin/bash
set -euo pipefail

# 1. Read ZEALT_RUN_ID and HOOKDECK_API_KEY
RUN_ID="${ZEALT_RUN_ID:-}"
if [ -z "$RUN_ID" ]; then
  echo "Error: ZEALT_RUN_ID environment variable is not set." >&2
  exit 1
fi

if [ -z "${HOOKDECK_API_KEY:-}" ]; then
  echo "Error: HOOKDECK_API_KEY environment variable is not set." >&2
  exit 1
fi

echo "Using RUN_ID: ${RUN_ID}"

# 2. Authenticate with Hookdeck in headless CI environment
echo "Authenticating with Hookdeck in headless CI environment..."
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# 3. Create or update Hookdeck connection (idempotent)
SOURCE_NAME="test-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
CONN_NAME="conn-${RUN_ID}"

echo "Creating/updating Hookdeck connection linking ${SOURCE_NAME} to ${DEST_NAME}..."
CONN_JSON=$(hookdeck connection upsert "$CONN_NAME" \
  --source-type WEBHOOK \
  --source-name "$SOURCE_NAME" \
  --destination-type MOCK_API \
  --destination-name "$DEST_NAME" \
  --output json)

# 4. Extract source_id (using Python for JSON parsing to avoid jq dependency)
SOURCE_ID=$(echo "$CONN_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('source', {}).get('id', ''))")
if [ -z "$SOURCE_ID" ] || [ "$SOURCE_ID" == "None" ]; then
  echo "Error: Failed to retrieve source_id from connection response." >&2
  exit 1
fi
echo "Source ID: ${SOURCE_ID}"

# 5. Trigger a mock event to the source using the Publish API
echo "Publishing mock event to source ${SOURCE_ID}..."
PUBLISH_RESPONSE=$(curl -s -X POST https://hkdk.events/v1/publish \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -H "X-Hookdeck-Source-Id: ${SOURCE_ID}" \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "run_id": "'"${RUN_ID}"'"}')

REQUEST_ID=$(echo "$PUBLISH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('request_id', ''))")
if [ -z "$REQUEST_ID" ] || [ "$REQUEST_ID" == "None" ]; then
  echo "Error: Failed to publish event. Response: ${PUBLISH_RESPONSE}" >&2
  exit 1
fi
echo "Published successfully. Request ID: ${REQUEST_ID}"

# 6. Query the events for the source using the Inspect API to verify the event delivery status is SUCCESSFUL
echo "Polling Inspect API for successful event delivery..."
MAX_ATTEMPTS=15
ATTEMPT=1
EVENT_ID=""

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
  echo "Checking event status (Attempt ${ATTEMPT}/${MAX_ATTEMPTS})..."
  
  # Query events filtered by source_id using the REST API
  EVENTS_JSON=$(curl -s "https://api.hookdeck.com/2025-07-01/events?source_id=${SOURCE_ID}" \
    -H "Authorization: Bearer ${HOOKDECK_API_KEY}")
  
  # Find the event that has status SUCCESSFUL and corresponds to our request_id
  EVENT_STATUS=$(echo "$EVENTS_JSON" | python3 -c "import sys, json; data = json.load(sys.stdin); print(next((m.get('status', '') for m in data.get('models', []) if m.get('request_id') == '$REQUEST_ID'), ''))")
  EVENT_ID=$(echo "$EVENTS_JSON" | python3 -c "import sys, json; data = json.load(sys.stdin); print(next((m.get('id', '') for m in data.get('models', []) if m.get('request_id') == '$REQUEST_ID'), ''))")

  if [ "$EVENT_STATUS" = "SUCCESSFUL" ]; then
    echo "Event delivered successfully!"
    break
  fi

  echo "Event status is: ${EVENT_STATUS:-not_found_yet}. Waiting..."
  sleep 1
  ATTEMPT=$((ATTEMPT + 1))
done

if [ -z "$EVENT_ID" ] || [ "$EVENT_ID" == "None" ]; then
  echo "Error: Event delivery did not succeed within the timeout period." >&2
  exit 1
fi

# 7. Write the successful event ID to a log file
LOG_FILE="/home/user/hookdeck-task/output.log"
echo "Event ID: ${EVENT_ID}" > "$LOG_FILE"
echo "Successfully logged event ID to ${LOG_FILE}"
