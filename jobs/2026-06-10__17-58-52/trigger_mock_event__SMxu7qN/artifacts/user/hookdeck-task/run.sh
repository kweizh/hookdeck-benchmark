#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
API_KEY="${HOOKDECK_API_KEY}"
API_BASE="https://api.hookdeck.com/2025-07-01"
LOG_FILE="$(cd "$(dirname "$0")" && pwd)/output.log"

# Generate a unique run-id (8 hex chars)
RUN_ID="$(date +%s%N | md5sum | head -c 8)"

CONN_NAME="mock-conn-${RUN_ID}"
SOURCE_NAME="mock-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"

echo "Run ID   : ${RUN_ID}"
echo "Conn     : ${CONN_NAME}"
echo "Source   : ${SOURCE_NAME}"
echo "Dest     : ${DEST_NAME}"
echo "Log file : ${LOG_FILE}"

# -------------------------------------------------------------------
# Step 1: Authenticate CLI (headless / CI)
# -------------------------------------------------------------------
echo ""
echo "==> Authenticating Hookdeck CLI..."
hookdeck ci --api-key "${API_KEY}"

# -------------------------------------------------------------------
# Step 2: Create the connection (source -> MOCK_API destination)
# -------------------------------------------------------------------
echo ""
echo "==> Creating connection '${CONN_NAME}'..."
CONN_JSON=$(hookdeck connection create \
  --name "${CONN_NAME}" \
  --source-name "${SOURCE_NAME}" \
  --source-type WEBHOOK \
  --destination-name "${DEST_NAME}" \
  --destination-type MOCK_API \
  --output json 2>/dev/null)

echo "Connection created: $(echo "${CONN_JSON}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('id=' + d['id'])")"

# Extract the source ID from the connection response
SOURCE_ID=$(echo "${CONN_JSON}" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d['source']['id'])")
SOURCE_URL=$(echo "${CONN_JSON}" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d['source']['url'])")
echo "Source ID  : ${SOURCE_ID}"
echo "Source URL : ${SOURCE_URL}"

# -------------------------------------------------------------------
# Step 3: Publish an event to the source via Publish API
# -------------------------------------------------------------------
echo ""
echo "==> Publishing event to ${SOURCE_URL} ..."

PUBLISH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -d "{\"event\":\"test\",\"run_id\":\"${RUN_ID}\",\"message\":\"Hello from mock event trigger\"}")

HTTP_STATUS=$(echo "${PUBLISH_RESPONSE}" | tail -n1)
PUBLISH_BODY=$(echo "${PUBLISH_RESPONSE}" | head -n -1)

echo "Publish HTTP status : ${HTTP_STATUS}"
echo "Publish response    : ${PUBLISH_BODY}"

if [ "${HTTP_STATUS}" != "200" ] && [ "${HTTP_STATUS}" != "201" ] && [ "${HTTP_STATUS}" != "202" ]; then
  echo "ERROR: Publish API returned unexpected status ${HTTP_STATUS}" >&2
  exit 1
fi

# Extract the request_id from the publish response (used to look up the event)
REQUEST_ID=$(echo "${PUBLISH_BODY}" | python3 -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('request_id',''))" 2>/dev/null || true)
echo "Publish request_id : ${REQUEST_ID}"

# -------------------------------------------------------------------
# Step 4: Retrieve the event ID via the Events API
# -------------------------------------------------------------------
echo ""
echo "==> Waiting for event to be indexed..."
sleep 5

EVENT_ID=""
RETRIES=12
for i in $(seq 1 ${RETRIES}); do
  echo "Attempt ${i}/${RETRIES}: fetching events for source ${SOURCE_ID}..."

  EVENTS_JSON=$(curl -s -X GET \
    "${API_BASE}/events?source_id=${SOURCE_ID}&limit=5" \
    -H "Authorization: Bearer ${API_KEY}")

  EVENT_ID=$(echo "${EVENTS_JSON}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
models = d.get('models', [])
if models:
    print(models[0]['id'])
" 2>/dev/null || true)

  if [ -n "${EVENT_ID}" ]; then
    echo "Found event ID: ${EVENT_ID}"
    break
  fi

  echo "Event not yet visible, retrying in 3s..."
  sleep 3
done

if [ -z "${EVENT_ID}" ]; then
  echo "ERROR: Could not retrieve event ID after ${RETRIES} attempts." >&2
  exit 1
fi

# -------------------------------------------------------------------
# Step 5: Append event ID to the log file
# -------------------------------------------------------------------
echo ""
echo "==> Appending event ID to log file..."
echo "Event ID: ${EVENT_ID}" >> "${LOG_FILE}"

echo "Successfully wrote to ${LOG_FILE}"
echo ""
echo "--- Log file contents ---"
cat "${LOG_FILE}"
echo "-------------------------"
echo ""
echo "Done."
