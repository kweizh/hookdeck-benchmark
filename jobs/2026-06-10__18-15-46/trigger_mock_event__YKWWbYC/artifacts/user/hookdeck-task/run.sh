#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${ZEALT_RUN_ID}"
LOG_FILE="/home/user/hookdeck-task/output.log"

SOURCE_NAME="mock-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
CONN_NAME="mock-conn-${RUN_ID}"

# Ensure log directory exists, clear previous log
mkdir -p "$(dirname "$LOG_FILE")"
> "$LOG_FILE"

# Step 1: Authenticate with Hookdeck CLI
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Step 2: Create or update connection with MOCK_API destination (using upsert for idempotency)
CONN_OUTPUT=$(hookdeck connection upsert "$CONN_NAME" \
  --source-name "$SOURCE_NAME" \
  --source-type WEBHOOK \
  --destination-name "$DEST_NAME" \
  --destination-type MOCK_API \
  --output json)

echo "Connection output: $CONN_OUTPUT"

# Extract source ID from connection output
SOURCE_ID=$(python3 -c "import json,sys; print(json.loads(sys.stdin.read())['source']['id'])" <<< "$CONN_OUTPUT")
echo "Source ID: $SOURCE_ID"

# Step 3: Publish an event to the source using the Publish API
PUBLISH_RESPONSE=$(curl -s -X POST "https://hkdk.events/v1/publish" \
  -H "x-hookdeck-source-name: $SOURCE_NAME" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "test event from mock"}')

echo "Publish response: $PUBLISH_RESPONSE"

# Step 4: Retrieve the event ID using the Inspect API
# Give a brief moment for the event to be processed
sleep 3

# List events filtered by source name and extract the most recent event ID
EVENTS_RESPONSE=$(curl -s "https://api.hookdeck.com/2025-07-01/events?source_name=$SOURCE_NAME" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json")

echo "Events response: $EVENTS_RESPONSE"

# Extract the event ID from the response using python3
# The API returns events in a "models" array
EVENT_ID=$(python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
models = data.get('models', data.get('data', []))
if len(models) > 0:
    print(models[0]['id'])
else:
    print('NOT_FOUND')
" <<< "$EVENTS_RESPONSE")

echo "Event ID: $EVENT_ID"

# Step 5: Write event ID to log file
echo "Event ID: $EVENT_ID" > "$LOG_FILE"

echo "Done. Log file contents:"
cat "$LOG_FILE"