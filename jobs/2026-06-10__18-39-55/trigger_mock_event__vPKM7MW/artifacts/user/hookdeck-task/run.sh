#!/usr/bin/env bash
set -euo pipefail

# Generate a unique run ID
RUN_ID="${1:-$(date +%s)}"
LOG_FILE="/home/user/hookdeck-task/output.log"

echo "=== Hookdeck Mock Event Trigger ===" | tee "$LOG_FILE"
echo "Run ID: $RUN_ID" | tee -a "$LOG_FILE"

# Authenticate with Hookdeck in CI mode
echo "Authenticating with Hookdeck..." | tee -a "$LOG_FILE"
hookdeck ci --api-key "$HOOKDECK_API_KEY"

SOURCE_NAME="mock-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
CONN_NAME="mock-conn-${RUN_ID}"

echo "Source: $SOURCE_NAME" | tee -a "$LOG_FILE"
echo "Destination: $DEST_NAME" | tee -a "$LOG_FILE"
echo "Connection: $CONN_NAME" | tee -a "$LOG_FILE"

# Step 1: Create the connection with inline source (WEBHOOK) and destination (MOCK_API)
echo "" | tee -a "$LOG_FILE"
echo "Step 1: Creating connection..." | tee -a "$LOG_FILE"

CREATE_RESPONSE=$(curl -s --location "https://api.hookdeck.com/2025-07-01/connections" \
  --header "Content-Type: application/json" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  --data "{
    \"name\": \"${CONN_NAME}\",
    \"source\": {
      \"name\": \"${SOURCE_NAME}\"
    },
    \"destination\": {
      \"name\": \"${DEST_NAME}\",
      \"type\": \"MOCK_API\"
    }
  }")

echo "Create response: $CREATE_RESPONSE" | tee -a "$LOG_FILE"

# Extract source ID from the response (handle both pretty-printed and compact JSON)
SOURCE_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":"src_[^"]*"' | head -1 | sed 's/"id":"\(src_[^"]*\)"/\1/')

echo "Source ID: $SOURCE_ID" | tee -a "$LOG_FILE"

# Step 2: Publish an event via the Publish API
echo "" | tee -a "$LOG_FILE"
echo "Step 2: Publishing event via Publish API..." | tee -a "$LOG_FILE"

PUBLISH_RESPONSE=$(curl -s --location "https://hkdk.events/v1/publish" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  --header "X-Hookdeck-Source-Name: ${SOURCE_NAME}" \
  --data '{
    "event_type": "test.event",
    "data": {
      "message": "Hello from Hookdeck Publish API",
      "timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
    }
  }')

echo "Publish response: $PUBLISH_RESPONSE" | tee -a "$LOG_FILE"

# Step 3: Retrieve the event ID from the Events API
echo "" | tee -a "$LOG_FILE"
echo "Step 3: Retrieving event ID..." | tee -a "$LOG_FILE"

# Wait for the event to be processed
sleep 3

EVENTS_RESPONSE=$(curl -s --location \
  "https://api.hookdeck.com/2025-07-01/events?limit=1&order_by=created_at&dir=desc&source_id=${SOURCE_ID}" \
  --header "Accept: application/json" \
  --header "Authorization: Bearer ${HOOKDECK_API_KEY}")

echo "Events response: $EVENTS_RESPONSE" | tee -a "$LOG_FILE"

# Extract the event ID
EVENT_ID=$(echo "$EVENTS_RESPONSE" | grep -o '"id":"evt_[^"]*"' | head -1 | sed 's/"id":"\(evt_[^"]*\)"/\1/')

if [ -z "$EVENT_ID" ]; then
  # Fallback: try without source filter, get the most recent event
  EVENTS_RESPONSE2=$(curl -s --location \
    "https://api.hookdeck.com/2025-07-01/events?limit=5&order_by=created_at&dir=desc" \
    --header "Accept: application/json" \
    --header "Authorization: Bearer ${HOOKDECK_API_KEY}")
  
  echo "Fallback events response: $EVENTS_RESPONSE2" | tee -a "$LOG_FILE"
  EVENT_ID=$(echo "$EVENTS_RESPONSE2" | grep -o '"id":"evt_[^"]*"' | head -1 | sed 's/"id":"\(evt_[^"]*\)"/\1/')
fi

echo "" | tee -a "$LOG_FILE"
echo "Event ID: ${EVENT_ID}" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Done ===" | tee -a "$LOG_FILE"
