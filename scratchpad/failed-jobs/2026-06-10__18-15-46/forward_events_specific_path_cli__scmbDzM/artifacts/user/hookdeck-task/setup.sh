#!/bin/bash
set -e

# Read run-id from environment variable
RUN_ID="${ZEALT_RUN_ID}"

if [ -z "$RUN_ID" ]; then
  echo "Error: ZEALT_RUN_ID environment variable is not set"
  exit 1
fi

# Authenticate with Hookdeck CI
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Create the connection with inline source and destination
hookdeck gateway connection create \
  --name "cli-forward-conn-${RUN_ID}" \
  --source-name "my-source-${RUN_ID}" \
  --source-type PUBLISH_API \
  --destination-name "my-cli-dest-${RUN_ID}" \
  --destination-type CLI \
  --destination-cli-path /api/webhooks