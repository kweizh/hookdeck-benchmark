#!/bin/bash
set -e

# Ensure ZEALT_RUN_ID is set
if [ -z "${ZEALT_RUN_ID}" ]; then
  echo "Error: ZEALT_RUN_ID environment variable is not set."
  exit 1
fi

# Ensure HOOKDECK_API_KEY is set
if [ -z "${HOOKDECK_API_KEY}" ]; then
  echo "Error: HOOKDECK_API_KEY environment variable is not set."
  exit 1
fi

echo "Authenticating Hookdeck CLI..."
hookdeck ci --api-key "${HOOKDECK_API_KEY}"

RUN_ID="${ZEALT_RUN_ID}"
echo "Using RUN_ID: ${RUN_ID}"

# 1. Create Source
echo "Creating Source source-${RUN_ID}..."
SRC_JSON=$(hookdeck gateway source create --name "source-${RUN_ID}" --type WEBHOOK --output json)
SRC_ID=$(echo "$SRC_JSON" | node -e "const data = require('fs').readFileSync(0, 'utf-8'); console.log(JSON.parse(data).id);")
echo "Created Source with ID: ${SRC_ID}"

# 2. Create Mock Destination
echo "Creating Mock Destination dest-${RUN_ID}..."
DST_JSON=$(hookdeck gateway destination create --name "dest-${RUN_ID}" --type MOCK_API --output json)
DST_ID=$(echo "$DST_JSON" | node -e "const data = require('fs').readFileSync(0, 'utf-8'); console.log(JSON.parse(data).id);")
echo "Created Destination with ID: ${DST_ID}"

# 3. Create Transformation
echo "Creating JavaScript Transformation flatten-${RUN_ID}..."
XFORM_JSON=$(hookdeck gateway transformation create --name "flatten-${RUN_ID}" --code-file /home/user/hookdeck-task/flatten.js --output json)
XFORM_ID=$(echo "$XFORM_JSON" | node -e "const data = require('fs').readFileSync(0, 'utf-8'); console.log(JSON.parse(data).id);")
echo "Created Transformation with ID: ${XFORM_ID}"

# 4. Create Connection
echo "Creating Connection conn-${RUN_ID}..."
CONN_JSON=$(hookdeck gateway connection create --name "conn-${RUN_ID}" --source-id "${SRC_ID}" --destination-id "${DST_ID}" --rule-transform-name "flatten-${RUN_ID}" --output json)
CONN_ID=$(echo "$CONN_JSON" | node -e "const data = require('fs').readFileSync(0, 'utf-8'); console.log(JSON.parse(data).id);")
echo "Created Connection with ID: ${CONN_ID}"

echo "Setup completed successfully!"
