#!/usr/bin/env bash
set -euo pipefail

# Read the run ID from the environment
run_id="${ZEALT_RUN_ID:?ZEALT_RUN_ID environment variable must be set}"

# Authenticate with Hookdeck in headless CI mode
echo "Authenticating with Hookdeck..."
hookdeck ci --api-key "${HOOKDECK_API_KEY:?HOOKDECK_API_KEY environment variable must be set}"

# Create the connection, source, and destination in one command
echo "Creating Hookdeck connection..."
hookdeck gateway connection create \
  --name "cli-forward-conn-${run_id}" \
  --source-name "my-source-${run_id}" \
  --source-type "HTTP" \
  --destination-name "my-cli-dest-${run_id}" \
  --destination-type "CLI" \
  --destination-cli-path "/api/webhooks"

echo "Connection created successfully."
