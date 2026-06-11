#!/bin/bash
set -e

# Read ZEALT_RUN_ID environment variable
RUN_ID="${ZEALT_RUN_ID}"
if [ -z "$RUN_ID" ]; then
  echo "Error: ZEALT_RUN_ID environment variable is not set." >&2
  exit 1
fi

echo "Using RUN_ID: ${RUN_ID}"

# Configure/authenticate Hookdeck CLI
echo "Configuring Hookdeck CLI..."
hookdeck ci

# Define names
SOURCE_NAME="stripe-${RUN_ID}"
DESTINATION_NAME="mock-api-${RUN_ID}"
CONNECTION_NAME="stripe-to-mock-${RUN_ID}"

# 1. Create or retrieve Source
echo "Setting up Source: ${SOURCE_NAME}..."
SOURCE_ID=""
if hookdeck gateway source create --name "${SOURCE_NAME}" --type STRIPE > /tmp/source_create.log 2>&1; then
  SOURCE_ID=$(cat /tmp/source_create.log | grep -o 'src_[a-zA-Z0-9]*' | head -n 1)
  echo "Created new source with ID: ${SOURCE_ID}"
else
  echo "Source already exists or creation failed. Retrieving existing source ID..."
  SOURCE_ID=$(hookdeck gateway source list | grep -A 1 "${SOURCE_NAME}" | grep "ID:" | awk '{print $2}')
  if [ -z "$SOURCE_ID" ]; then
    echo "Error: Could not retrieve ID for source ${SOURCE_NAME}" >&2
    exit 1
  fi
  echo "Found existing source with ID: ${SOURCE_ID}"
fi

# 2. Create or retrieve Destination
echo "Setting up Destination: ${DESTINATION_NAME}..."
DESTINATION_ID=""
if hookdeck gateway destination create --name "${DESTINATION_NAME}" --type MOCK_API > /tmp/destination_create.log 2>&1; then
  DESTINATION_ID=$(cat /tmp/destination_create.log | grep -o 'des_[a-zA-Z0-9]*' | head -n 1)
  echo "Created new destination with ID: ${DESTINATION_ID}"
else
  echo "Destination already exists or creation failed. Retrieving existing destination ID..."
  DESTINATION_ID=$(hookdeck gateway destination list | grep -A 1 "${DESTINATION_NAME}" | grep "ID:" | awk '{print $2}')
  if [ -z "$DESTINATION_ID" ]; then
    echo "Error: Could not retrieve ID for destination ${DESTINATION_NAME}" >&2
    exit 1
  fi
  echo "Found existing destination with ID: ${DESTINATION_ID}"
fi

# 3. Create or retrieve Connection
echo "Setting up Connection: ${CONNECTION_NAME}..."
CONNECTION_ID=""
if hookdeck gateway connection create --name "${CONNECTION_NAME}" --source-id "${SOURCE_ID}" --destination-id "${DESTINATION_ID}" > /tmp/connection_create.log 2>&1; then
  CONNECTION_ID=$(cat /tmp/connection_create.log | grep -o 'web_[a-zA-Z0-9]*' | head -n 1)
  echo "Created new connection with ID: ${CONNECTION_ID}"
else
  echo "Connection already exists or creation failed. Retrieving existing connection ID..."
  CONNECTION_ID=$(hookdeck gateway connection list | grep -A 1 "${CONNECTION_NAME}" | grep "ID:" | awk '{print $2}')
  if [ -z "$CONNECTION_ID" ]; then
    echo "Error: Could not retrieve ID for connection ${CONNECTION_NAME}" >&2
    exit 1
  fi
  echo "Found existing connection with ID: ${CONNECTION_ID}"
fi

# 4. Save connection ID to log file
OUTPUT_FILE="/home/user/hookdeck-task/output.log"
mkdir -p "$(dirname "$OUTPUT_FILE")"
echo "Connection ID: ${CONNECTION_ID}" > "$OUTPUT_FILE"
echo "Successfully wrote connection ID to ${OUTPUT_FILE}:"
cat "$OUTPUT_FILE"
