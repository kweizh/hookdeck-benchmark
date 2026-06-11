#!/bin/bash
set -euo pipefail

# 1. Authenticate with Hookdeck in headless environment
echo "Authenticating with Hookdeck..."
hookdeck ci --api-key "${HOOKDECK_API_KEY}"

# 2. Extract run-id from ZEALT_RUN_ID
RUN_ID="${ZEALT_RUN_ID:-}"
if [ -z "${RUN_ID}" ]; then
  echo "Error: ZEALT_RUN_ID environment variable is not set." >&2
  exit 1
fi

echo "Using RUN_ID: ${RUN_ID}"

# Define names
SOURCE_NAME="stripe-${RUN_ID}"
DESTINATION_NAME="mock-dest-${RUN_ID}"
CONNECTION_NAME="stripe-to-mock-${RUN_ID}"

echo "Creating Hookdeck connection: ${CONNECTION_NAME}"
echo "Source: ${SOURCE_NAME} (STRIPE)"
echo "Destination: ${DESTINATION_NAME} (MOCK_API)"

# 3. Create the connection and save the output to the log file
# Note: we use --destination-type MOCK_API since the CLI expects MOCK_API
hookdeck gateway connection create \
  --name "${CONNECTION_NAME}" \
  --source-type STRIPE \
  --source-name "${SOURCE_NAME}" \
  --destination-type MOCK_API \
  --destination-name "${DESTINATION_NAME}" > "/home/user/hookdeck-task/output.log" 2>&1

echo "Connection creation output saved to /home/user/hookdeck-task/output.log"
cat "/home/user/hookdeck-task/output.log"
