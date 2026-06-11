#!/bin/bash

RUN_ID=$ZEALT_RUN_ID
CONN_NAME="legacy-to-mock-$RUN_ID"
SRC_NAME="legacy-source-$RUN_ID"
DEST_NAME="mock-dest-$RUN_ID"
SECRET="super_secret_value_$RUN_ID"

ENV_JSON="{\"SECRET_TOKEN\": \"$SECRET\"}"
CODE=$(cat /home/user/hookdeck-task/transform.js)

OUTPUT=$(hookdeck connection create \
  --name "$CONN_NAME" \
  --source-type WEBHOOK --source-name "$SRC_NAME" \
  --destination-type MOCK_API --destination-name "$DEST_NAME" \
  --rule-transform-name "transform-$RUN_ID" \
  --rule-transform-code "$CODE" \
  --rule-transform-env "$ENV_JSON" \
  --output json)

echo "Output from CLI:"
echo "$OUTPUT"

CONN_ID=$(echo "$OUTPUT" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$CONN_ID" ]; then
  echo "Failed to parse CONN_ID"
else
  echo "Connection ID: $CONN_ID" > /home/user/hookdeck-task/output.log
  echo "Successfully saved Connection ID: $CONN_ID to output.log"
fi
