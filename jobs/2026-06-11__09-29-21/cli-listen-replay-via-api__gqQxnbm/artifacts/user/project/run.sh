#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${ZEALT_RUN_ID}"
SOURCE_NAME="cli-replay-${RUN_ID}"
SOURCE_NAME_LOWER=$(echo "$SOURCE_NAME" | tr '[:upper:]' '[:lower:]')
LOG_FILE="/home/user/project/output.log"

# Clear log file
> "$LOG_FILE"

echo "=== Starting Hookdeck CLI Replay Workflow ==="
echo "Source Name: $SOURCE_NAME_LOWER"

# Step 1: Start local HTTP server in background
echo "Starting local HTTP server on port 3000..."
node /home/user/project/server.js &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Give server time to start
sleep 2

# Verify server is running
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/test || true
echo ""

# Step 2: Authenticate Hookdeck CLI
echo "Authenticating Hookdeck CLI..."
echo "$HOOKDECK_API_KEY" | hookdeck login --cli

# Step 3: Run hookdeck listen in background
echo "Starting hookdeck listen..."
hookdeck listen 3000 "$SOURCE_NAME_LOWER" --path /hooks --output quiet &
LISTEN_PID=$!
echo "Listen PID: $LISTEN_PID"

# Wait for the connection to be established
echo "Waiting for connection to be established..."
sleep 10

# Step 4: Get connection info via REST API
echo "Fetching connection info..."
CONNECTION_RESPONSE=$(curl -s -X GET "https://api.hookdeck.com/connections?source_name=$SOURCE_NAME_LOWER" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json")

echo "Connection response: $CONNECTION_RESPONSE"

# Extract connection ID
CONNECTION_ID=$(echo "$CONNECTION_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('models', data.get('data', []))
if models:
    print(models[0]['id'])
else:
    print('')
")

echo "Connection ID: $CONNECTION_ID"

# Step 5: Publish an event to the source
echo "Publishing event to source..."
PUBLISH_RESPONSE=$(curl -s -X POST "https://hkdk.events/v1/publish" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "X-Hookdeck-Source-Name: $SOURCE_NAME_LOWER" \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "message": "hello from cli replay"}')

echo "Publish response: $PUBLISH_RESPONSE"

# Extract event ID from publish response
EVENT_ID=$(echo "$PUBLISH_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
# The publish API may return the event ID in different formats
event_id = data.get('id', data.get('event_id', ''))
print(event_id)
")

echo "Event ID: $EVENT_ID"

# Step 6: Wait for first delivery attempt to fail
echo "Waiting for first delivery attempt to fail..."
sleep 10

# Check event status
EVENT_STATUS=$(curl -s -X GET "https://api.hookdeck.com/events/$EVENT_ID" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json")

echo "Event status after first attempt: $EVENT_STATUS"

# Step 7: Retry the event via REST API
echo "Retrying event $EVENT_ID..."
RETRY_RESPONSE=$(curl -s -X POST "https://api.hookdeck.com/events/$EVENT_ID/retry" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json")

echo "Retry response: $RETRY_RESPONSE"

# Extract retry response event ID - the retry endpoint returns the Event object at the root
RETRY_EVENT_ID=$(echo "$RETRY_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
event_id = data.get('id', '')
print(event_id)
")

echo "Retry Response Event ID: $RETRY_EVENT_ID"

# Step 8: Poll until status is SUCCESSFUL and attempts == 2
echo "Polling for successful delivery..."
MAX_POLLS=30
POLL_INTERVAL=5
FINAL_STATUS=""
FINAL_ATTEMPTS=""

for i in $(seq 1 $MAX_POLLS); do
  echo "Poll $i: Checking event status..."
  
  EVENT_CHECK=$(curl -s -X GET "https://api.hookdeck.com/events/$EVENT_ID" \
    -H "Authorization: Bearer $HOOKDECK_API_KEY" \
    -H "Content-Type: application/json")
  
  STATUS=$(echo "$EVENT_CHECK" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('status', ''))
")
  
  ATTEMPTS=$(echo "$EVENT_CHECK" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('attempts', 0))
")
  
  echo "  Status: $STATUS, Attempts: $ATTEMPTS"
  
  if [ "$STATUS" = "SUCCESSFUL" ] && [ "$ATTEMPTS" = "2" ]; then
    FINAL_STATUS="$STATUS"
    FINAL_ATTEMPTS="$ATTEMPTS"
    echo "Success! Event delivered successfully after retry."
    break
  fi
  
  if [ "$i" -eq "$MAX_POLLS" ]; then
    FINAL_STATUS="$STATUS"
    FINAL_ATTEMPTS="$ATTEMPTS"
    echo "Warning: Max polls reached. Last status: $STATUS, attempts: $ATTEMPTS"
  fi
  
  sleep $POLL_INTERVAL
done

# Step 9: Write output.log
echo "Writing output.log..."
cat > "$LOG_FILE" << EOF
Source Name: $SOURCE_NAME_LOWER
Connection ID: $CONNECTION_ID
Event ID: $EVENT_ID
Retry Response Event ID: $RETRY_EVENT_ID
Final Status: $FINAL_STATUS
Final Attempts: $FINAL_ATTEMPTS
EOF

echo "=== Output Log ==="
cat "$LOG_FILE"

# Cleanup
echo "Cleaning up..."
kill $LISTEN_PID 2>/dev/null || true
kill $SERVER_PID 2>/dev/null || true

echo "=== Workflow Complete ==="