#!/bin/bash

# Ensure we have the run id
if [ -z "$ZEALT_RUN_ID" ]; then
  echo "ZEALT_RUN_ID is not set"
  exit 1
fi

RUN_ID=$ZEALT_RUN_ID

# Authenticate Hookdeck CI
hookdeck ci --api-key $HOOKDECK_API_KEY

# Create connection
hookdeck gateway connection create \
  --name "cli-forward-conn-${RUN_ID}" \
  --source-type WEBHOOK \
  --source-name "my-source-${RUN_ID}" \
  --destination-type CLI \
  --destination-name "my-cli-dest-${RUN_ID}" \
  --destination-cli-path "/api/webhooks"
