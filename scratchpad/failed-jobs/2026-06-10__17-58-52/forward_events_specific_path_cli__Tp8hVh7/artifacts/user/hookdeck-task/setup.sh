#!/usr/bin/env bash
set -euo pipefail

# Authenticate with Hookdeck using the API key (CI/headless mode)
hookdeck ci --api-key "$HOOKDECK_API_KEY"

# Derive resource names from the run ID
RUN_ID="${ZEALT_RUN_ID}"

CONNECTION_NAME="cli-forward-conn-${RUN_ID}"
SOURCE_NAME="my-source-${RUN_ID}"
DESTINATION_NAME="my-cli-dest-${RUN_ID}"

echo "Creating Hookdeck connection: ${CONNECTION_NAME}"
echo "  Source:      ${SOURCE_NAME} (type: API)"
echo "  Destination: ${DESTINATION_NAME} (type: CLI, path: /api/webhooks)"

hookdeck gateway connection create \
  --name "${CONNECTION_NAME}" \
  --source-type "PUBLISH_API" \
  --source-name "${SOURCE_NAME}" \
  --destination-type "CLI" \
  --destination-name "${DESTINATION_NAME}" \
  --destination-cli-path "/api/webhooks"

echo "Connection created successfully."
