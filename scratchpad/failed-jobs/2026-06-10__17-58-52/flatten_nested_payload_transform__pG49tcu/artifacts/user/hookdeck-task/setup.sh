#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Hookdeck – Flatten Nested Payload Transformation setup
# ---------------------------------------------------------------------------
# Reads run-id from ZEALT_RUN_ID, authenticates via HOOKDECK_API_KEY, then
# creates:
#   • Source          source-${run-id}
#   • Destination     dest-${run-id}      (MOCK_API)
#   • Transformation  flatten-${run-id}
#   • Connection      conn-${run-id}      (linking the three above)
# ---------------------------------------------------------------------------

# --- validate env vars -----------------------------------------------------
if [[ -z "${ZEALT_RUN_ID:-}" ]]; then
  echo "ERROR: ZEALT_RUN_ID environment variable is not set." >&2
  exit 1
fi

if [[ -z "${HOOKDECK_API_KEY:-}" ]]; then
  echo "ERROR: HOOKDECK_API_KEY environment variable is not set." >&2
  exit 1
fi

RUN_ID="${ZEALT_RUN_ID}"
SOURCE_NAME="source-${RUN_ID}"
DEST_NAME="dest-${RUN_ID}"
TRANSFORM_NAME="flatten-${RUN_ID}"
CONN_NAME="conn-${RUN_ID}"

API_BASE="https://api.hookdeck.com/2025-07-01"
AUTH_HEADER="Authorization: Bearer ${HOOKDECK_API_KEY}"

echo "==> Run ID        : ${RUN_ID}"
echo "==> Source        : ${SOURCE_NAME}"
echo "==> Destination   : ${DEST_NAME}"
echo "==> Transformation: ${TRANSFORM_NAME}"
echo "==> Connection    : ${CONN_NAME}"
echo ""

# Helper: parse a JSON field value (string) from the first occurrence
json_field() {
  local json="$1"
  local field="$2"
  echo "${json}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['${field}'])
"
}

# --- authenticate in CI (headless) -----------------------------------------
echo "==> Authenticating with Hookdeck CI..."
hookdeck ci --api-key "${HOOKDECK_API_KEY}"

# --- 1. Create Source -------------------------------------------------------
echo "==> Creating source: ${SOURCE_NAME}"
SOURCE_RESP=$(curl -sf -X POST "${API_BASE}/sources" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${SOURCE_NAME}\", \"type\": \"WEBHOOK\"}")
echo "${SOURCE_RESP}" | python3 -m json.tool
SOURCE_ID=$(json_field "${SOURCE_RESP}" "id")
echo "    source id: ${SOURCE_ID}"

# --- 2. Create Mock Destination ---------------------------------------------
echo "==> Creating mock destination: ${DEST_NAME}"
DEST_RESP=$(curl -sf -X POST "${API_BASE}/destinations" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${DEST_NAME}\", \"type\": \"MOCK_API\"}")
echo "${DEST_RESP}" | python3 -m json.tool
DEST_ID=$(json_field "${DEST_RESP}" "id")
echo "    destination id: ${DEST_ID}"

# --- 3. Create Transformation -----------------------------------------------
# If request.body.data.object exists, replace the entire body with it.
TRANSFORM_CODE='addHandler("transform", (request, context) => {
  if (request.body && request.body.data && request.body.data.object !== undefined) {
    request.body = request.body.data.object;
  }
  return request;
});'

echo "==> Creating transformation: ${TRANSFORM_NAME}"
TRANSFORM_PAYLOAD=$(python3 -c "
import json, sys
payload = {
    'name': '${TRANSFORM_NAME}',
    'code': '''${TRANSFORM_CODE}'''
}
print(json.dumps(payload))
")
TRANSFORM_RESP=$(curl -sf -X POST "${API_BASE}/transformations" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "${TRANSFORM_PAYLOAD}")
echo "${TRANSFORM_RESP}" | python3 -m json.tool
TRANSFORM_ID=$(json_field "${TRANSFORM_RESP}" "id")
echo "    transformation id: ${TRANSFORM_ID}"

# --- 4. Create Connection linking Source, Destination, and Transformation ---
echo "==> Creating connection: ${CONN_NAME}"
CONN_PAYLOAD=$(python3 -c "
import json
payload = {
    'name': '${CONN_NAME}',
    'source_id': '${SOURCE_ID}',
    'destination_id': '${DEST_ID}',
    'rules': [
        {
            'type': 'transform',
            'transformation_id': '${TRANSFORM_ID}'
        }
    ]
}
print(json.dumps(payload))
")
CONN_RESP=$(curl -sf -X POST "${API_BASE}/connections" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "${CONN_PAYLOAD}")
echo "${CONN_RESP}" | python3 -m json.tool
CONN_ID=$(json_field "${CONN_RESP}" "id")
echo "    connection id: ${CONN_ID}"

echo ""
echo "==> Setup complete!"
echo "    Source          : ${SOURCE_NAME}   (${SOURCE_ID})"
echo "    Destination     : ${DEST_NAME}  (${DEST_ID})"
echo "    Transformation  : ${TRANSFORM_NAME}  (${TRANSFORM_ID})"
echo "    Connection      : ${CONN_NAME}     (${CONN_ID})"
