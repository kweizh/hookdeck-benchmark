#!/bin/bash
set -e

# Ensure ZEALT_RUN_ID is set
if [ -z "$ZEALT_RUN_ID" ]; then
  echo "ZEALT_RUN_ID is not set"
  exit 1
fi

# Authenticate with Hookdeck in a headless CI environment
hookdeck ci > /dev/null 2>&1

# Create connection
CONNECTION_JSON=$(hookdeck connection create \
  --name "test-conn-$ZEALT_RUN_ID" \
  --source-type WEBHOOK \
  --source-name "test-source-$ZEALT_RUN_ID" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-$ZEALT_RUN_ID" \
  --output json)

SOURCE_ID=$(echo "$CONNECTION_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('source', {}).get('id', ''))")

if [ -z "$SOURCE_ID" ]; then
  echo "Failed to extract source ID from connection JSON:"
  echo "$CONNECTION_JSON"
  exit 1
fi

echo "Created source: $SOURCE_ID"

# Trigger a mock event to the source using the Publish API
REQUEST_JSON=$(curl -s -X POST -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "x-hookdeck-source-id: $SOURCE_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "test event"}' \
  https://hkdk.events/v1/publish)

REQUEST_ID=$(echo "$REQUEST_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin).get('request_id', ''))")
echo "Triggered request: $REQUEST_ID"

# Wait a bit for the event to be processed
sleep 3

# Query the events for the source using the Inspect API
EVENTS_JSON=$(curl -s -H "Authorization: Bearer $HOOKDECK_API_KEY" "https://api.hookdeck.com/2024-03-01/events?source_id=$SOURCE_ID")

EVENT_ID=$(echo "$EVENTS_JSON" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    for m in models:
        if m.get('status') == 'SUCCESSFUL':
            print(m.get('id', ''))
            break
except Exception as e:
    pass
")

if [ -n "$EVENT_ID" ] && [ "$EVENT_ID" != "null" ]; then
  echo "Event ID: $EVENT_ID" > /home/user/hookdeck-task/output.log
  echo "Successfully verified event delivery."
else
  echo "No successful event found."
  echo "Events JSON response:"
  echo "$EVENTS_JSON"
  exit 1
fi
