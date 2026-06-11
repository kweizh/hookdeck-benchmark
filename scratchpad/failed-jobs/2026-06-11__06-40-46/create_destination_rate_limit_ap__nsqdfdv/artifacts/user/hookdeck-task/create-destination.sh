#!/usr/bin/env bash
set -euo pipefail

API_KEY="${HOOKDECK_API_KEY:?HOOKDECK_API_KEY is required}"
RUN_ID="${ZEALT_RUN_ID:?ZEALT_RUN_ID is required}"
DEST_NAME="rate-limited-dest-${RUN_ID}"
DEST_URL="https://mock.hookdeck.com/rate-limited"
LOG_FILE="/home/user/hookdeck-task/output.log"

echo "Creating Hookdeck destination: ${DEST_NAME}"

RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "https://api.hookdeck.com/2025-07-01/destinations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(cat <<EOF
{
  "name": "${DEST_NAME}",
  "type": "HTTP",
  "config": {
    "url": "${DEST_URL}",
    "rate_limit": 10,
    "rate_limit_period": "second"
  }
}
EOF
)")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

# Extract the destination ID using grep/sed (no jq dependency)
DEST_ID=$(echo "$BODY" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

if [ "$HTTP_CODE" = "409" ] && [ -n "$DEST_ID" ]; then
  echo "Destination already exists with ID: ${DEST_ID}"
  echo "Destination ID: ${DEST_ID}" > "${LOG_FILE}"
  exit 0
fi

if [ "$HTTP_CODE" -lt 200 ] || [ "$HTTP_CODE" -ge 300 ]; then
  echo "Error: API returned HTTP ${HTTP_CODE}"
  echo "Response: ${BODY}"
  exit 1
fi

if [ -z "$DEST_ID" ]; then
  echo "Error: Failed to extract destination ID from response"
  echo "Response: ${BODY}"
  exit 1
fi

echo "Destination ID: ${DEST_ID}" > "${LOG_FILE}"
echo "Successfully created destination with ID: ${DEST_ID}"
