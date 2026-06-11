#!/bin/bash
set -e

# Authenticate Hookdeck CLI
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Generate a unique run-id
run_id=$(date +%s)

# Create connection
hookdeck connection create \
    --name "mock-conn-${run_id}" \
    --source-type WEBHOOK \
    --source-name "mock-source-${run_id}" \
    --destination-type MOCK_API \
    --destination-name "mock-dest-${run_id}" \
    --output json > /dev/null

# Trigger an event via Publish API
response=$(curl -s -X POST https://hkdk.events/v1/publish \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $HOOKDECK_API_KEY" \
    -H "X-Hookdeck-Source-Name: mock-source-${run_id}" \
    -d '{"message": "hello mock"}')

request_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('request_id', ''))")

if [ -z "$request_id" ] || [ "$request_id" == "null" ]; then
    echo "Failed to get request_id from publish API. Response: $response"
    exit 1
fi

# We need to wait a few seconds for the event to be processed and available in the API
sleep 5

# Fetch the event ID
event_response=$(curl -s -X GET "https://api.hookdeck.com/2025-07-01/events?request_id=${request_id}" \
    -H "Authorization: Bearer $HOOKDECK_API_KEY")

event_id=$(echo "$event_response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('models', [{}])[0].get('id', ''))" 2>/dev/null || echo "")

if [ -z "$event_id" ]; then
    echo "Failed to retrieve event_id. Response: $event_response"
    exit 1
fi

echo "Event ID: $event_id" >> /home/user/hookdeck-task/output.log

echo "Success! Event ID: $event_id"
