#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${ZEALT_RUN_ID:?ZEALT_RUN_ID environment variable is required}"
API_KEY="${HOOKDECK_API_KEY:?HOOKDECK_API_KEY environment variable is required}"
LOG_FILE="/home/user/hookdeck-task/output.log"

# Authenticate with Hookdeck in headless/CI mode
hookdeck ci --api-key "$API_KEY"

# Create the connection with inline source (STRIPE) and destination (MOCK)
hookdeck gateway connection create \
  --name "stripe-to-mock-${RUN_ID}" \
  --source-type STRIPE \
  --source-name "stripe-${RUN_ID}" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-${RUN_ID}" \
  --output json \
  | tee "$LOG_FILE"
