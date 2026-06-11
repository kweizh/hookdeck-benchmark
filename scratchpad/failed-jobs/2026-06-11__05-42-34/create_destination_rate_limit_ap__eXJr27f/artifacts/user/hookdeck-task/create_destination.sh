#!/bin/bash

set -e

API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
DEST_NAME="rate-limited-dest-${RUN_ID}"
DEST_URL="https://mock.hookdeck.com/rate-limited"
LOG_FILE="/home/user/hookdeck-task/output.log"

echo "Creating destination: ${DEST_NAME}"

RESPONSE=$(curl -s -X POST "https://api.hookdeck.com/latest/destinations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${DEST_NAME}\",
    \"type\": \"HTTP\",
    \"config\": {
      \"url\": \"${DEST_URL}\",
      \"rate_limit\": 10,
      \"rate_limit_period\": \"second\"
    }
  }")

echo "API Response: ${RESPONSE}"

DEST_ID=$(echo "${RESPONSE}" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "${DEST_ID}" ]; then
  echo "Error: Failed to extract destination ID from response"
  echo "Response was: ${RESPONSE}"
  exit 1
fi

echo "Destination ID: ${DEST_ID}" | tee "${LOG_FILE}"
echo "Destination created successfully with ID: ${DEST_ID}"
