#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${ZEALT_RUN_ID}"
API_KEY="${HOOKDECK_API_KEY}"
LOG_FILE="/home/user/hookdeck-task/output.log"
HMAC_SECRET="my-super-secret-hmac-key"

# Clear previous log
> "$LOG_FILE"

echo "=== Authenticating with Hookdeck CLI ===" | tee -a "$LOG_FILE"
hookdeck ci --api-key "$API_KEY" 2>&1 | tee -a "$LOG_FILE"

SOURCE_NAME="hmac-source-${RUN_ID}"
DEST_NAME="hmac-dest-${RUN_ID}"
CONNECTION_NAME="hmac-connection-${RUN_ID}"
TRANSFORM_NAME="hmac-transform-${RUN_ID}"

# Transformation code: compute HMAC SHA-256 of the request body and add as header
TRANSFORM_CODE='addHandler("transform", (request, context) => {
  const secret = context.env.HMAC_SECRET;
  const body = JSON.stringify(request.body);
  const hmac = crypto.createHmac("sha256", secret).update(body).digest("hex");
  request.headers["x-hmac-signature"] = hmac;
  return request;
});'

echo "" | tee -a "$LOG_FILE"
echo "=== Creating transformation: ${TRANSFORM_NAME} ===" | tee -a "$LOG_FILE"
TRANSFORM_OUTPUT=$(hookdeck gateway transformation create \
  --name "$TRANSFORM_NAME" \
  --code "$TRANSFORM_CODE" \
  --env "HMAC_SECRET=${HMAC_SECRET}" \
  --output json 2>&1)
echo "$TRANSFORM_OUTPUT" | tee -a "$LOG_FILE"

TRANSFORM_ID=$(echo "$TRANSFORM_OUTPUT" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
echo "Transformation ID: ${TRANSFORM_ID}" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Creating source: ${SOURCE_NAME} ===" | tee -a "$LOG_FILE"
SOURCE_OUTPUT=$(hookdeck gateway source create \
  --name "$SOURCE_NAME" \
  --type WEBHOOK \
  --output json 2>&1)
echo "$SOURCE_OUTPUT" | tee -a "$LOG_FILE"

SOURCE_ID=$(echo "$SOURCE_OUTPUT" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
echo "Source ID: ${SOURCE_ID}" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Creating destination: ${DEST_NAME} ===" | tee -a "$LOG_FILE"
DEST_OUTPUT=$(hookdeck gateway destination create \
  --name "$DEST_NAME" \
  --type MOCK_API \
  --output json 2>&1)
echo "$DEST_OUTPUT" | tee -a "$LOG_FILE"

DEST_ID=$(echo "$DEST_OUTPUT" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
echo "Destination ID: ${DEST_ID}" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Creating connection: ${CONNECTION_NAME} ===" | tee -a "$LOG_FILE"
CONN_OUTPUT=$(hookdeck gateway connection create \
  --name "$CONNECTION_NAME" \
  --source-id "$SOURCE_ID" \
  --destination-id "$DEST_ID" \
  --rule-transform-name "$TRANSFORM_ID" \
  --output json 2>&1)
echo "$CONN_OUTPUT" | tee -a "$LOG_FILE"

CONNECTION_ID=$(echo "$CONN_OUTPUT" | grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
echo "Connection ID: ${CONNECTION_ID}" | tee -a "$LOG_FILE"

# Write the required formatted output to the log file
echo "" >> "$LOG_FILE"
echo "Source ID: ${SOURCE_ID}" >> "$LOG_FILE"
echo "Connection ID: ${CONNECTION_ID}" >> "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "=== Done ===" | tee -a "$LOG_FILE"
echo "Source ID: ${SOURCE_ID}" | tee -a "$LOG_FILE"
echo "Connection ID: ${CONNECTION_ID}" | tee -a "$LOG_FILE"
