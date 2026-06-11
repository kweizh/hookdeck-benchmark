#!/bin/bash
set -e

# Ensure we are logged in
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Read RUN_ID from environment
RUN_ID="${ZEALT_RUN_ID}"
if [ -z "$RUN_ID" ]; then
  echo "Error: ZEALT_RUN_ID is not set." >&2
  exit 1
fi

CONN_NAME="header-filter-conn-${RUN_ID}"
SRC_NAME="header-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"

echo "Creating Hookdeck Connection with name: ${CONN_NAME}"

# Create connection and capture output
OUTPUT=$(hookdeck gateway connection create \
  --name "${CONN_NAME}" \
  --source-type WEBHOOK \
  --source-name "${SRC_NAME}" \
  --destination-type MOCK_API \
  --destination-name "${DEST_NAME}" \
  --rule-filter-headers '{"x-target-event": "process"}' \
  --output json)

# Parse connection ID using python
CONN_ID=$(echo "$OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

if [ -z "$CONN_ID" ]; then
  echo "Error: Failed to retrieve Connection ID from Hookdeck output." >&2
  echo "Output: $OUTPUT" >&2
  exit 1
fi

echo "Created Connection ID: ${CONN_ID}"

# Write to output.log
echo "Connection ID: ${CONN_ID}" > /home/user/hookdeck-task/output.log

echo "Successfully wrote Connection ID to /home/user/hookdeck-task/output.log"
