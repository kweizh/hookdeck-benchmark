#!/usr/bin/env bash
set -euo pipefail

# Authenticate with Hookdeck in headless/CI mode
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Use ZEALT_RUN_ID to build unique resource names
RUN_ID="${ZEALT_RUN_ID}"

SOURCE_NAME="stripe-${RUN_ID}"
DESTINATION_NAME="mock-dest-${RUN_ID}"
CONNECTION_NAME="stripe-to-mock-${RUN_ID}"

LOG_FILE="$(dirname "$0")/output.log"

# Create the connection and save output to the log file
hookdeck gateway connection create \
  --name "$CONNECTION_NAME" \
  --source-name "$SOURCE_NAME" \
  --source-type "STRIPE" \
  --destination-name "$DESTINATION_NAME" \
  --destination-type "MOCK_API" \
  --output json | tee "$LOG_FILE"
