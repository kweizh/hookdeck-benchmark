#!/bin/bash
set -e

RUN_ID="${ZEALT_RUN_ID}"
SOURCE_NAME="fan-out-source-${RUN_ID}"
DEST1_NAME="mock-dest-1-${RUN_ID}"
DEST2_NAME="mock-dest-2-${RUN_ID}"
OUTPUT_FILE="/home/user/hookdeck-task/output.log"

echo "Creating fan-out architecture for run ID: ${RUN_ID}"

# Authenticate with Hookdeck
hookdeck ci --api-key "${HOOKDECK_API_KEY}"

# Create first connection: source -> mock-dest-1 with rate limit 10/sec
RESULT1=$(hookdeck gateway connection create \
  --name "conn-1-${RUN_ID}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST1_NAME}" \
  --destination-type MOCK_API \
  --destination-rate-limit 10 \
  --destination-rate-limit-period second \
  --output json)

# Extract source URL from the first connection's output
SOURCE_URL=$(echo "${RESULT1}" | python3 -c "import sys,json; print(json.load(sys.stdin)['source']['url'])")

echo "Source URL: ${SOURCE_URL}"

# Create second connection: same source -> mock-dest-2 with rate limit 50/sec
RESULT2=$(hookdeck gateway connection create \
  --name "conn-2-${RUN_ID}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST2_NAME}" \
  --destination-type MOCK_API \
  --destination-rate-limit 50 \
  --destination-rate-limit-period second \
  --output json)

echo "Destination 1: ${DEST1_NAME} (10 req/sec)"
echo "Destination 2: ${DEST2_NAME} (50 req/sec)"

# Write source URL to output log
echo "Source URL: ${SOURCE_URL}" > "${OUTPUT_FILE}"

echo "Fan-out setup complete. Source URL written to ${OUTPUT_FILE}"