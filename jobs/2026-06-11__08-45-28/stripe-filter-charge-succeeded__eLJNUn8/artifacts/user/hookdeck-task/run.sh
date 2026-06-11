#!/usr/bin/env bash
set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
BASE_URL="https://api.hookdeck.com/2025-07-01"
PUBLISH_URL="https://hkdk.events/v1/publish"
LOG_FILE="/home/user/hookdeck-task/output.log"

SOURCE_NAME="stripe-src-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
CONN_NAME="stripe-charge-succeeded-${RUN_ID}"

echo "=== Hookdeck Stripe Filter Task ==="
echo "Run ID   : ${RUN_ID}"
echo "Source   : ${SOURCE_NAME}"
echo "Dest     : ${DEST_NAME}"
echo "Conn     : ${CONN_NAME}"
echo ""

# ─── Step 1: Authenticate CLI ────────────────────────────────────────────────
echo "[1/5] Authenticating CLI..."
hookdeck ci --api-key "$API_KEY"
echo "CLI authenticated."

# ─── Step 2: Create Connection via REST API ───────────────────────────────────
echo "[2/5] Creating Connection (Source + Destination + Filter rule)..."

CONN_PAYLOAD=$(cat <<EOF
{
  "name": "${CONN_NAME}",
  "source": {
    "name": "${SOURCE_NAME}",
    "type": "STRIPE"
  },
  "destination": {
    "name": "${DEST_NAME}",
    "type": "MOCK_API"
  },
  "rules": [
    {
      "type": "filter",
      "body": {
        "type": "charge.succeeded"
      }
    }
  ]
}
EOF
)

CONN_RESP=$(curl -s -X POST "${BASE_URL}/connections" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "${CONN_PAYLOAD}")

echo "Connection API response:"
echo "${CONN_RESP}" | python3 -m json.tool

# Extract IDs
CONN_ID=$(echo "${CONN_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
SRC_ID=$(echo "${CONN_RESP}"  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['source']['id'])")
DEST_ID=$(echo "${CONN_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['destination']['id'])")

echo ""
echo "Connection ID : ${CONN_ID}"
echo "Source ID     : ${SRC_ID}"
echo "Destination ID: ${DEST_ID}"

# ─── Step 3: Publish 4 events ─────────────────────────────────────────────────
echo ""
echo "[3/5] Publishing 4 Stripe events via Publish API..."

for EVENT_TYPE in "charge.succeeded" "charge.failed" "charge.refunded" "charge.captured"; do
  echo "  Publishing: ${EVENT_TYPE}"
  PUB_RESP=$(curl -s -X POST "${PUBLISH_URL}" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -H "X-Hookdeck-Source-Name: ${SOURCE_NAME}" \
    -d "{\"type\": \"${EVENT_TYPE}\", \"data\": {\"amount\": 1000, \"currency\": \"usd\"}}")
  echo "    Response: ${PUB_RESP}"
done

# ─── Step 4: Poll until processing stabilizes ─────────────────────────────────
echo ""
echo "[4/5] Polling Inspect API for events on connection ${CONN_ID}..."

MAX_ATTEMPTS=30
SLEEP_SEC=3
DELIVERED_COUNT=0

for i in $(seq 1 ${MAX_ATTEMPTS}); do
  echo "  Poll attempt ${i}/${MAX_ATTEMPTS}..."
  EVENTS_RESP=$(curl -s "${BASE_URL}/events?webhook_id=${CONN_ID}" \
    -H "Authorization: Bearer ${API_KEY}")
  
  DELIVERED_COUNT=$(echo "${EVENTS_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['count'])" 2>/dev/null || echo "0")
  
  echo "    Delivered event count: ${DELIVERED_COUNT}"
  
  if [ "${DELIVERED_COUNT}" -ge 1 ]; then
    # Check if event is SUCCESSFUL (not still QUEUED/SCHEDULED)
    STATUS=$(echo "${EVENTS_RESP}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d['count']>0:
    print(d['models'][0]['status'])
else:
    print('NONE')
" 2>/dev/null || echo "NONE")
    echo "    Event status: ${STATUS}"
    if [ "${STATUS}" = "SUCCESSFUL" ]; then
      echo "  Event is SUCCESSFUL. Stopping poll."
      break
    fi
  fi
  
  if [ "${i}" -eq "${MAX_ATTEMPTS}" ]; then
    echo "WARNING: Max poll attempts reached."
  else
    sleep "${SLEEP_SEC}"
  fi
done

# ─── Step 5: Verify and write log ─────────────────────────────────────────────
echo ""
echo "[5/5] Verifying results and writing log..."

FINAL_EVENTS=$(curl -s "${BASE_URL}/events?webhook_id=${CONN_ID}" \
  -H "Authorization: Bearer ${API_KEY}")

echo "Final events response:"
echo "${FINAL_EVENTS}" | python3 -m json.tool

FINAL_COUNT=$(echo "${FINAL_EVENTS}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['count'])")
echo "Final event count: ${FINAL_COUNT}"

if [ "${FINAL_COUNT}" != "1" ]; then
  echo "ERROR: Expected exactly 1 event, got ${FINAL_COUNT}"
  exit 1
fi

EVENT_ID=$(echo "${FINAL_EVENTS}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['models'][0]['id'])")
EVENT_STATUS=$(echo "${FINAL_EVENTS}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['models'][0]['status'])")

echo "Event ID    : ${EVENT_ID}"
echo "Event Status: ${EVENT_STATUS}"

if [ "${EVENT_STATUS}" != "SUCCESSFUL" ]; then
  echo "ERROR: Event status is ${EVENT_STATUS}, expected SUCCESSFUL"
  exit 1
fi

# Verify event body type is charge.succeeded
EVENT_DETAIL=$(curl -s "${BASE_URL}/events/${EVENT_ID}" \
  -H "Authorization: Bearer ${API_KEY}")

echo ""
echo "Event detail response:"
echo "${EVENT_DETAIL}" | python3 -m json.tool

BODY_TYPE=$(echo "${EVENT_DETAIL}" | python3 -c "
import sys,json
d=json.load(sys.stdin)
# Try data.body.body.type first (nested structure), then data.body.type (flat structure)
try:
    val = d['data']['body']['body']['type']
    print(val)
except (KeyError, TypeError):
    try:
        val = d['data']['body']['type']
        print(val)
    except Exception as e:
        print('UNKNOWN: '+str(e))
" 2>/dev/null || echo "UNKNOWN")

echo "Event body type: ${BODY_TYPE}"

if [ "${BODY_TYPE}" != "charge.succeeded" ]; then
  echo "ERROR: Expected body type 'charge.succeeded', got '${BODY_TYPE}'"
  exit 1
fi

# ─── Write log file ───────────────────────────────────────────────────────────
cat > "${LOG_FILE}" <<LOGEOF
Connection ID: ${CONN_ID}
Source ID: ${SRC_ID}
Destination ID: ${DEST_ID}
Delivered Event ID: ${EVENT_ID}
LOGEOF

echo ""
echo "=== Log file written to ${LOG_FILE} ==="
cat "${LOG_FILE}"
echo ""
echo "=== TASK COMPLETE ==="
