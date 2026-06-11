#!/bin/bash
set -e

# Authenticate with Hookdeck
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Create the connection and write output to the log file
hookdeck gateway connection create \
  --name "stripe-to-mock-${ZEALT_RUN_ID}" \
  --source-type STRIPE \
  --source-name "stripe-${ZEALT_RUN_ID}" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-${ZEALT_RUN_ID}" > /home/user/hookdeck-task/output.log
