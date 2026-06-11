#!/bin/bash
# Publish 100 events to Hookdeck via the Publish API

RUN_ID="$ZEALT_RUN_ID"
API_KEY="$HOOKDECK_API_KEY"
SOURCE_NAME="bulk-source-${RUN_ID}"
PUBLISH_URL="https://hkdk.events/v1/publish"

echo "Publishing 100 events to source: ${SOURCE_NAME}"

SUCCESS_COUNT=0
FAIL_COUNT=0

for i in $(seq 0 99); do
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${PUBLISH_URL}" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "X-Hookdeck-Source-Name: ${SOURCE_NAME}" \
    -H "x-batch-id: BATCH-001" \
    -d "{\"i\": ${i}}")
  
  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | sed '$d')
  
  if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "202" ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo "FAILED: i=$i, status=$HTTP_CODE, body=$BODY"
  fi
done

echo "Publishing complete. Success: $SUCCESS_COUNT, Failed: $FAIL_COUNT"