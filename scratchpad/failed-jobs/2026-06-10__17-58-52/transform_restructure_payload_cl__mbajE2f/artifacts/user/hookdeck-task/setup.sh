#!/usr/bin/env bash
set -euo pipefail

# Read run ID
RUN_ID="${ZEALT_RUN_ID}"
API_KEY="${HOOKDECK_API_KEY}"

CONNECTION_NAME="legacy-to-mock-${RUN_ID}"
SOURCE_NAME="legacy-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
TRANSFORM_NAME="transform-${RUN_ID}"
SECRET_TOKEN="super_secret_value_${RUN_ID}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_LOG="${SCRIPT_DIR}/output.log"

echo "=== Hookdeck Transformation Setup ==="
echo "Run ID       : ${RUN_ID}"
echo "Connection   : ${CONNECTION_NAME}"
echo "Source       : ${SOURCE_NAME}"
echo "Destination  : ${DEST_NAME}"
echo "Transform    : ${TRANSFORM_NAME}"

# Authenticate
echo ""
echo "--- Authenticating ---"
hookdeck ci --api-key "${API_KEY}"

# Write transformation JS code to a temp file
TRANSFORM_CODE_FILE=$(mktemp /tmp/transform-XXXXXX.js)
cat > "${TRANSFORM_CODE_FILE}" << 'JSCODE'
addHandler("transform", (request, context) => {
  // Extract data.object as the new body
  if (request.body && request.body.data && request.body.data.object !== undefined) {
    request.body = request.body.data.object;
  }

  // Add custom headers
  request.headers["x-hookdeck-transformed"] = "true";
  request.headers["x-secret-token"] = context.env.SECRET_TOKEN;

  return request;
});
JSCODE

echo ""
echo "--- Creating Transformation ---"
TRANSFORM_OUTPUT=$(hookdeck gateway transformation create \
  --name "${TRANSFORM_NAME}" \
  --code-file "${TRANSFORM_CODE_FILE}" \
  --env "SECRET_TOKEN=${SECRET_TOKEN}" \
  --output json 2>&1)
echo "${TRANSFORM_OUTPUT}"

TRANSFORM_ID=$(echo "${TRANSFORM_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null || echo "")
echo "Transformation ID: ${TRANSFORM_ID}"

# Clean up temp file
rm -f "${TRANSFORM_CODE_FILE}"

echo ""
echo "--- Creating Destination (Mock API) ---"
DEST_OUTPUT=$(hookdeck gateway destination create \
  --name "${DEST_NAME}" \
  --type MOCK_API \
  --output json 2>&1)
echo "${DEST_OUTPUT}"

DEST_ID=$(echo "${DEST_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null || echo "")
echo "Destination ID: ${DEST_ID}"

echo ""
echo "--- Creating Connection with inline source, existing destination ---"
CONNECTION_OUTPUT=$(hookdeck gateway connection create \
  --name "${CONNECTION_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-id "${DEST_ID}" \
  --output json 2>&1)
echo "${CONNECTION_OUTPUT}"

CONNECTION_ID=$(echo "${CONNECTION_OUTPUT}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])" 2>/dev/null || echo "")
echo "Connection ID: ${CONNECTION_ID}"

echo ""
echo "--- Attaching Transformation to Connection ---"
UPDATE_OUTPUT=$(hookdeck gateway connection update "${CONNECTION_ID}" \
  --rules "[{\"type\":\"transform\",\"transformation_id\":\"${TRANSFORM_ID}\"}]" \
  --output json 2>&1)
echo "${UPDATE_OUTPUT}"

# Save to log file
echo "Connection ID: ${CONNECTION_ID}" > "${OUTPUT_LOG}"
echo "Connection Name: ${CONNECTION_NAME}" >> "${OUTPUT_LOG}"
echo "Source Name: ${SOURCE_NAME}" >> "${OUTPUT_LOG}"
echo "Destination Name: ${DEST_NAME}" >> "${OUTPUT_LOG}"
echo "Transformation Name: ${TRANSFORM_NAME}" >> "${OUTPUT_LOG}"
echo "Transformation ID: ${TRANSFORM_ID}" >> "${OUTPUT_LOG}"
echo "Run ID: ${RUN_ID}" >> "${OUTPUT_LOG}"

echo ""
echo "=== Setup Complete ==="
echo "Log written to: ${OUTPUT_LOG}"
cat "${OUTPUT_LOG}"
