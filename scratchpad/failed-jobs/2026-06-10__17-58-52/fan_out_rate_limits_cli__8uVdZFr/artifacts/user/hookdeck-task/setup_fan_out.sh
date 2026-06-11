#!/usr/bin/env bash
set -euo pipefail

# Read run-id from environment variable
RUN_ID="${ZEALT_RUN_ID:?Error: ZEALT_RUN_ID environment variable is not set}"

# Authenticate the CLI using the API key (CI mode, non-interactive)
if [ -n "${HOOKDECK_API_KEY:-}" ]; then
  echo "Authenticating CLI with HOOKDECK_API_KEY..."
  hookdeck ci --api-key "${HOOKDECK_API_KEY}"
fi

SOURCE_NAME="fan-out-source-${RUN_ID}"
DEST_1_NAME="mock-dest-1-${RUN_ID}"
DEST_2_NAME="mock-dest-2-${RUN_ID}"
CONN_1_NAME="conn-to-dest-1-${RUN_ID}"
CONN_2_NAME="conn-to-dest-2-${RUN_ID}"
OUTPUT_LOG="/home/user/hookdeck-task/output.log"

echo "Creating fan-out connections for run ID: ${RUN_ID}"

# Create Connection 1: fan-out-source -> mock-dest-1 (rate limit: 10/second)
echo "Creating connection to ${DEST_1_NAME} with rate limit 10/second..."
CONN_1_OUTPUT=$(hookdeck gateway connection upsert "${CONN_1_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST_1_NAME}" \
  --destination-type MOCK_API \
  --destination-rate-limit 10 \
  --destination-rate-limit-period second \
  --output json)

echo "Connection 1 created: ${CONN_1_OUTPUT}"

# Create Connection 2: fan-out-source -> mock-dest-2 (rate limit: 50/second)
echo "Creating connection to ${DEST_2_NAME} with rate limit 50/second..."
CONN_2_OUTPUT=$(hookdeck gateway connection upsert "${CONN_2_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST_2_NAME}" \
  --destination-type MOCK_API \
  --destination-rate-limit 50 \
  --destination-rate-limit-period second \
  --output json)

echo "Connection 2 created: ${CONN_2_OUTPUT}"

# Extract the Source URL from the first connection output using jq (preferred) or grep
SOURCE_URL=""
if command -v jq &>/dev/null; then
  SOURCE_URL=$(echo "${CONN_1_OUTPUT}" | jq -r '.source.url // empty' 2>/dev/null || true)
fi

# Fallback: grep for the url field nested under "source"
if [ -z "${SOURCE_URL}" ]; then
  SOURCE_URL=$(echo "${CONN_1_OUTPUT}" | grep -o '"url":"[^"]*"' | head -1 | sed 's/"url":"//;s/"//')
fi

# Second fallback: use hookdeck source get to retrieve the URL
if [ -z "${SOURCE_URL}" ]; then
  echo "Fetching source URL via source get command..."
  SOURCE_OUTPUT=$(hookdeck gateway source get "${SOURCE_NAME}" --output json 2>/dev/null || true)
  if [ -n "${SOURCE_OUTPUT}" ] && command -v jq &>/dev/null; then
    SOURCE_URL=$(echo "${SOURCE_OUTPUT}" | jq -r '.url // empty' 2>/dev/null || true)
  fi
  if [ -z "${SOURCE_URL}" ] && [ -n "${SOURCE_OUTPUT}" ]; then
    SOURCE_URL=$(echo "${SOURCE_OUTPUT}" | grep -o '"url":"[^"]*"' | head -1 | sed 's/"url":"//;s/"//')
  fi
fi

echo "Source URL: ${SOURCE_URL}"

# Write the Source URL to the output log
mkdir -p "$(dirname "${OUTPUT_LOG}")"
echo "Source URL: ${SOURCE_URL}" > "${OUTPUT_LOG}"

echo "Done! Source URL written to ${OUTPUT_LOG}"
