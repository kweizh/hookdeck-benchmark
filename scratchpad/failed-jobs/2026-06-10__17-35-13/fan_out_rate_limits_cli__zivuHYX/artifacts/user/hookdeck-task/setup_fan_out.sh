#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Read run-id from ZEALT_RUN_ID environment variable
RUN_ID="${ZEALT_RUN_ID}"
if [ -z "$RUN_ID" ]; then
  echo "Error: ZEALT_RUN_ID environment variable is not set." >&2
  exit 1
fi

PROJECT_DIR="/home/user/hookdeck-task"
mkdir -p "$PROJECT_DIR"

# Ensure Hookdeck CLI is authenticated
if [ -n "$HOOKDECK_API_KEY" ]; then
  echo "Authenticating Hookdeck CLI..."
  hookdeck ci --api-key "$HOOKDECK_API_KEY"
fi

echo "Creating the first connection (rate limit: 10/s) with inline Source and Destination..."
# Create first connection with inline source and destination
CONN1_JSON=$(hookdeck gateway connection create \
  --name "fanout-conn-1-${RUN_ID}" \
  --source-type WEBHOOK \
  --source-name "fan-out-source-${RUN_ID}" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-1-${RUN_ID}" \
  --destination-rate-limit 10 \
  --destination-rate-limit-period second \
  --output json)

# Extract Source ID and Source URL using Python
SOURCE_ID=$(echo "$CONN1_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['id'])")
SOURCE_URL=$(echo "$CONN1_JSON" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['url'])")

if [ -z "$SOURCE_ID" ] || [ -z "$SOURCE_URL" ]; then
  echo "Error: Failed to retrieve Source ID or Source URL from connection 1 creation." >&2
  exit 1
fi

echo "Successfully created connection 1."
echo "Source ID: $SOURCE_ID"
echo "Source URL: $SOURCE_URL"

echo "Creating the second connection (rate limit: 50/s) using the same Source ID..."
# Create second connection using the same source
CONN2_JSON=$(hookdeck gateway connection create \
  --name "fanout-conn-2-${RUN_ID}" \
  --source-id "$SOURCE_ID" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-2-${RUN_ID}" \
  --destination-rate-limit 50 \
  --destination-rate-limit-period second \
  --output json)

echo "Successfully created connection 2."

# Write the Source URL to the output log file
OUTPUT_LOG="$PROJECT_DIR/output.log"
echo "Source URL: $SOURCE_URL" > "$OUTPUT_LOG"

echo "All resources created successfully!"
echo "Source URL has been written to $OUTPUT_LOG"
cat "$OUTPUT_LOG"
