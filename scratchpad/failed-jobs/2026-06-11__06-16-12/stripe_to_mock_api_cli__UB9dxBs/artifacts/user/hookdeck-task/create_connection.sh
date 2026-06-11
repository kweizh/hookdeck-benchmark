#!/bin/bash
set -e

RUN_ID="${ZEALT_RUN_ID}"
CONNECTION_NAME="stripe-to-mock-${RUN_ID}"
SOURCE_NAME="stripe-${RUN_ID}"
DESTINATION_NAME="mock-api-${RUN_ID}"

echo "Creating Hookdeck connection..."
echo "  Connection name: ${CONNECTION_NAME}"
echo "  Source name: ${SOURCE_NAME} (type: STRIPE)"
echo "  Destination name: ${DESTINATION_NAME} (type: MOCK_API)"

RESULT=$(hookdeck connection create \
  --name "${CONNECTION_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type "STRIPE" \
  --destination-name "${DESTINATION_NAME}" \
  --destination-type "MOCK_API" \
  --output json)

echo "Response: ${RESULT}"

# Extract the connection ID from the JSON response
CONNECTION_ID=$(echo "${RESULT}" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('id', data.get('connection_id', '')))")

echo "Connection ID: ${CONNECTION_ID}"

# Write the connection ID to the log file
mkdir -p /home/user/hookdeck-task
echo "Connection ID: ${CONNECTION_ID}" > /home/user/hookdeck-task/output.log

echo "Done. Connection ID saved to /home/user/hookdeck-task/output.log"