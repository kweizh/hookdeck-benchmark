#!/bin/bash
set -e

# Ensure HOOKDECK_API_KEY is set
if [ -z "$HOOKDECK_API_KEY" ]; then
  echo "Error: HOOKDECK_API_KEY environment variable is not set." >&2
  exit 1
fi

# Authenticate Hookdeck CLI
echo "Authenticating Hookdeck CLI..."
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Determine RUN_ID (accept from argument, env, or generate random)
RUN_ID=${1:-${RUN_ID:-$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 8 | head -n 1)}}
echo "Using RUN_ID: ${RUN_ID}"

# Create connection named mock-conn-${RUN_ID} from mock-source-${RUN_ID} to mock-dest-${RUN_ID}
echo "Creating Hookdeck connection..."
CONNECTION_JSON=$(hookdeck gateway connection create \
  --name "mock-conn-${RUN_ID}" \
  --source-type PUBLISH_API \
  --source-name "mock-source-${RUN_ID}" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-${RUN_ID}" \
  --output json)

# Extract Source ID from response
SOURCE_ID=$(echo "$CONNECTION_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['id'])")
echo "Created Source ID: ${SOURCE_ID}"

# Trigger an event using Hookdeck Publish API
echo "Publishing event to Hookdeck..."
PUBLISH_RESPONSE=$(curl -s -X POST https://hkdk.events/v1/publish \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "X-Hookdeck-Source-Id: $SOURCE_ID" \
  -H "Content-Type: application/json" \
  -d '{"test": "data", "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}' )

echo "Publish Response: $PUBLISH_RESPONSE"

# Extract Request ID
REQUEST_ID=$(echo "$PUBLISH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['request_id'])")
echo "Published Request ID: ${REQUEST_ID}"

# Retrieve the event ID using the Inspect API with retry/polling
echo "Retrieving Event ID from Hookdeck Inspect API..."
EVENT_ID=""
for i in {1..15}; do
  EVENTS_JSON=$(curl -s "https://api.hookdeck.com/2025-07-01/events?source_id=${SOURCE_ID}" \
    -H "Authorization: Bearer $HOOKDECK_API_KEY")
  
  EVENT_ID=$(echo "$EVENTS_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
if models:
    print(models[0]['id'])
else:
    print('')
" 2>/dev/null)

  if [ -n "$EVENT_ID" ]; then
    echo "Found Event ID: $EVENT_ID"
    break
  fi
  echo "Event not indexed yet, retrying in 1 second..."
  sleep 1
done

if [ -z "$EVENT_ID" ]; then
  echo "Error: Failed to retrieve event ID from Hookdeck Inspect API" >&2
  exit 1
fi

# Ensure output directory exists
mkdir -p /home/user/hookdeck-task

# Write to log file in exact format
echo "Event ID: $EVENT_ID" >> /home/user/hookdeck-task/output.log
echo "Successfully logged event ID to /home/user/hookdeck-task/output.log"
