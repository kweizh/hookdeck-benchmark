#!/bin/bash

# Retrieve run-id from environment variable
RUN_ID="${ZEALT_RUN_ID}"
DEST_NAME="rate-limited-dest-${RUN_ID}"

# Create destination via Hookdeck API
RESPONSE=$(curl -s -X POST https://api.hookdeck.com/destinations \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${DEST_NAME}\",
    \"type\": \"HTTP\",
    \"config\": {
      \"url\": \"https://mock.hookdeck.com/rate-limited\",
      \"rate_limit\": 10,
      \"rate_limit_period\": \"second\"
    }
  }")

# Check if it was created or already exists
DEST_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -n 1 | cut -d'"' -f4)

# If DEST_ID is empty, try to GET it
if [ -z "$DEST_ID" ]; then
  RESPONSE=$(curl -s -H "Authorization: Bearer ${HOOKDECK_API_KEY}" "https://api.hookdeck.com/destinations?name=${DEST_NAME}")
  DEST_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -n 1 | cut -d'"' -f4)
fi

# Write to log file
echo "Destination ID: ${DEST_ID}" > /home/user/hookdeck-task/output.log
