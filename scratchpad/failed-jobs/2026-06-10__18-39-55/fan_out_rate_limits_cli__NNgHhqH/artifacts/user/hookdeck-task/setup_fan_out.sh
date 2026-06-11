#!/usr/bin/env bash
set -euo pipefail

# Read the run-id from the environment
RUN_ID="${ZEALT_RUN_ID:-unknown}"

SOURCE_NAME="fan-out-source-${RUN_ID}"
DEST1_NAME="mock-dest-1-${RUN_ID}"
DEST2_NAME="mock-dest-2-${RUN_ID}"
CONN1_NAME="fan-out-conn-1-${RUN_ID}"
CONN2_NAME="fan-out-conn-2-${RUN_ID}"
OUTPUT_LOG="/home/user/hookdeck-task/output.log"

echo "=== Setting up Hookdeck Fan-out Architecture ==="
echo "Run ID: ${RUN_ID}"
echo "Source: ${SOURCE_NAME}"
echo "Destination 1: ${DEST1_NAME} (10 req/s)"
echo "Destination 2: ${DEST2_NAME} (50 req/s)"

# Step 1: Authenticate with Hookdeck in CI mode
echo ""
echo "--- Authenticating with Hookdeck ---"
hookdeck ci --api-key "${HOOKDECK_API_KEY}"

# Step 2: Create Connection 1 (Source → mock-dest-1 with 10 req/s rate limit)
echo ""
echo "--- Creating Connection 1: ${SOURCE_NAME} → ${DEST1_NAME} (10 req/s) ---"
hookdeck gateway connection upsert "${CONN1_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST1_NAME}" \
  --destination-type MOCK_API \
  --destination-rate-limit 10 \
  --destination-rate-limit-period second

# Step 3: Create Connection 2 (Same Source → mock-dest-2 with 50 req/s rate limit)
echo ""
echo "--- Creating Connection 2: ${SOURCE_NAME} → ${DEST2_NAME} (50 req/s) ---"
hookdeck gateway connection upsert "${CONN2_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST2_NAME}" \
  --destination-type MOCK_API \
  --destination-rate-limit 50 \
  --destination-rate-limit-period second

# Step 4: Retrieve the Source URL
echo ""
echo "--- Retrieving Source URL ---"
# Extract the Source URL from the source get command output or connection output
SOURCE_URL=$(hookdeck gateway source get "${SOURCE_NAME}" 2>&1 | grep -oP 'URL:\s*\Khttps?://\S+' | head -1)

if [ -z "${SOURCE_URL}" ]; then
  # Fallback: try to get it from the connection list output
  SOURCE_URL=$(hookdeck gateway connection get "${CONN1_NAME}" 2>&1 | grep -oP 'Source URL:\s*\Khttps?://\S+' | head -1)
fi

if [ -z "${SOURCE_URL}" ]; then
  echo "ERROR: Could not retrieve Source URL."
  exit 1
fi

echo "Source URL: ${SOURCE_URL}"

# Step 5: Write the Source URL to the output log
mkdir -p "$(dirname "${OUTPUT_LOG}")"
echo "Source URL: ${SOURCE_URL}" > "${OUTPUT_LOG}"

echo ""
echo "=== Fan-out setup complete ==="
echo "Source URL written to: ${OUTPUT_LOG}"
