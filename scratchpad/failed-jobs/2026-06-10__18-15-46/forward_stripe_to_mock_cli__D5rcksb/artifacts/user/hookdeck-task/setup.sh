#!/usr/bin/env bash
set -euo pipefail

# Authenticate with Hookdeck in headless/CI environment
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Create a connection with a Stripe source and Mock destination
hookdeck gateway connection create \
  --name "stripe-to-mock-${ZEALT_RUN_ID}" \
  --source-name "stripe-${ZEALT_RUN_ID}" \
  --source-type "STRIPE" \
  --destination-name "mock-dest-${ZEALT_RUN_ID}" \
  --destination-type "MOCK_API" \
  --output json \
  2>&1 | tee /home/user/hookdeck-task/output.log