#!/usr/bin/env bash
set -euo pipefail

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
SOURCE_NAME="cli-replay-${RUN_ID}"
LOG_FILE="/home/user/project/output.log"
API_BASE="https://api.hookdeck.com/2025-01-01"

echo "[run] ZEALT_RUN_ID=${RUN_ID}"
echo "[run] SOURCE_NAME=${SOURCE_NAME}"
echo "[run] LOG_FILE=${LOG_FILE}"

# ── Cleanup any leftover processes ───────────────────────────────────────────
pkill -f "hookdeck listen" 2>/dev/null || true
pkill -f "server.js" 2>/dev/null || true
sleep 1

# ── 1. Start local HTTP server ───────────────────────────────────────────────
echo "[run] Starting local HTTP server on port 3000..."
node /home/user/project/server.js &
SERVER_PID=$!
echo "[run] Server PID=${SERVER_PID}"

# Give server time to start
sleep 1

# Verify server is up
curl -s -X POST http://127.0.0.1:3000/hooks -H "Content-Type: application/json" -d '{"ping":1}' || true
echo "[run] Server first call done (expected 500 above, resetting for real test)"

# The server now has firstRequest=false after the test call above, so we need
# to restart the server fresh
kill "${SERVER_PID}" 2>/dev/null || true
sleep 1
node /home/user/project/server.js &
SERVER_PID=$!
echo "[run] Server restarted with PID=${SERVER_PID}"
sleep 1

# ── 2. Start hookdeck listen in background ───────────────────────────────────
echo "[run] Starting hookdeck listen..."
rm -f /tmp/hookdeck-listen.log
hookdeck listen 3000 "${SOURCE_NAME}" \
  --path /hooks \
  --output compact \
  --color off \
  > /tmp/hookdeck-listen.log 2>&1 &
LISTEN_PID=$!
echo "[run] hookdeck listen PID=${LISTEN_PID}"

# ── 3. Wait for hookdeck to establish connection ─────────────────────────────
echo "[run] Waiting for hookdeck CLI to be READY..."
WAIT_SECS=0
MAX_WAIT=90

# Wait for "Getting ready..." to appear first, then "Ready" or for events to flow
until grep -q "Getting ready" /tmp/hookdeck-listen.log 2>/dev/null; do
  sleep 1
  WAIT_SECS=$((WAIT_SECS + 1))
  if [ $WAIT_SECS -ge $MAX_WAIT ]; then
    echo "[run] ERROR: hookdeck listen never started after ${MAX_WAIT}s"
    cat /tmp/hookdeck-listen.log
    exit 1
  fi
done

echo "[run] hookdeck CLI is initializing, waiting additional 10s for full readiness..."
sleep 10

echo "[run] hookdeck listen log so far:"
cat /tmp/hookdeck-listen.log

# ── 4. Discover source + connection via REST API ──────────────────────────────
echo "[run] Querying Hookdeck API for source '${SOURCE_NAME}'..."

SOURCE_RESP=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${API_BASE}/sources?name=${SOURCE_NAME}")
echo "[run] Source response: ${SOURCE_RESP}"

SOURCE_ID=$(echo "${SOURCE_RESP}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
if models:
    print(models[0]['id'])
")

if [ -z "${SOURCE_ID}" ]; then
  echo "[run] ERROR: Could not find source '${SOURCE_NAME}'"
  exit 1
fi
echo "[run] SOURCE_ID=${SOURCE_ID}"

# Discover connection
CONN_RESP=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
  "${API_BASE}/connections?source_id=${SOURCE_ID}")
echo "[run] Connection response: ${CONN_RESP}"

CONNECTION_ID=$(echo "${CONN_RESP}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
if models:
    print(models[0]['id'])
")

if [ -z "${CONNECTION_ID}" ]; then
  echo "[run] ERROR: Could not find connection for source '${SOURCE_NAME}'"
  exit 1
fi
echo "[run] CONNECTION_ID=${CONNECTION_ID}"

# ── 5. Publish event to the source ──────────────────────────────────────────
echo "[run] Publishing event to source '${SOURCE_NAME}'..."

PUBLISH_RESP=$(curl -s -X POST "https://hkdk.events/v1/publish" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "X-Hookdeck-Source-Name: ${SOURCE_NAME}" \
  -H "Content-Type: application/json" \
  -d '{"test": "event", "run_id": "'"${RUN_ID}"'"}')

echo "[run] Publish response: ${PUBLISH_RESP}"

# Brief wait for delivery attempt
sleep 5

# Check hookdeck listen log for event delivery
echo "[run] hookdeck listen log after publish:"
cat /tmp/hookdeck-listen.log

# ── 6. Wait for the failed event ────────────────────────────────────────────
echo "[run] Waiting for a FAILED event..."
EVENT_ID=""
WAIT_SECS=0
MAX_WAIT=120

while [ -z "${EVENT_ID}" ]; do
  sleep 3
  WAIT_SECS=$((WAIT_SECS + 3))
  
  EVENTS_RESP=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${API_BASE}/events?source_id=${SOURCE_ID}&status=FAILED&limit=10")
  
  EVENT_ID=$(echo "${EVENTS_RESP}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
if models:
    print(models[0]['id'])
" 2>/dev/null || true)
  
  echo "[run] Waiting for failed event... (${WAIT_SECS}s) EVENT_ID='${EVENT_ID}'"
  
  if [ $WAIT_SECS -ge $MAX_WAIT ]; then
    echo "[run] No FAILED event. Checking all events..."
    ALL_EVENTS=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
      "${API_BASE}/events?source_id=${SOURCE_ID}&limit=10")
    echo "[run] All events: ${ALL_EVENTS}"
    # Also check requests
    REQS=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
      "${API_BASE}/requests?source_id=${SOURCE_ID}&limit=5")
    echo "[run] Requests: ${REQS}"
    echo "[run] hookdeck listen log:"
    cat /tmp/hookdeck-listen.log
    exit 1
  fi
done

echo "[run] Found FAILED event: ${EVENT_ID}"

# ── 7. Replay the event via REST API ────────────────────────────────────────
echo "[run] Retrying event ${EVENT_ID}..."

RETRY_RESP=$(curl -s -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  "${API_BASE}/events/${EVENT_ID}/retry")

echo "[run] Retry response: ${RETRY_RESP}"

RETRY_EVENT_ID=$(echo "${RETRY_RESP}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# The response is the Event object directly at the root (no wrapper)
print(data.get('id', ''))
" 2>/dev/null || true)

echo "[run] RETRY_EVENT_ID=${RETRY_EVENT_ID}"

# ── 8. Poll until SUCCESSFUL with attempts==2 ───────────────────────────────
echo "[run] Polling event until SUCCESSFUL with 2 attempts..."
FINAL_STATUS=""
FINAL_ATTEMPTS=0
WAIT_SECS=0
MAX_WAIT=120

while true; do
  sleep 3
  WAIT_SECS=$((WAIT_SECS + 3))
  
  POLL_RESP=$(curl -s -H "Authorization: Bearer ${API_KEY}" \
    "${API_BASE}/events/${EVENT_ID}")
  
  FINAL_STATUS=$(echo "${POLL_RESP}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('status', ''))
" 2>/dev/null || true)
  
  FINAL_ATTEMPTS=$(echo "${POLL_RESP}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('attempts', 0))
" 2>/dev/null || true)
  
  echo "[run] Status=${FINAL_STATUS} Attempts=${FINAL_ATTEMPTS} (${WAIT_SECS}s)"
  
  if [ "${FINAL_STATUS}" = "SUCCESSFUL" ] && [ "${FINAL_ATTEMPTS}" = "2" ]; then
    echo "[run] Event is SUCCESSFUL with 2 attempts!"
    break
  fi
  
  if [ $WAIT_SECS -ge $MAX_WAIT ]; then
    echo "[run] ERROR: Event did not become SUCCESSFUL with 2 attempts after ${MAX_WAIT}s"
    echo "[run] Final poll response: ${POLL_RESP}"
    exit 1
  fi
done

# ── 9. Write output log ──────────────────────────────────────────────────────
echo "[run] Writing output log to ${LOG_FILE}..."

cat > "${LOG_FILE}" << LOGEOF
Source Name: ${SOURCE_NAME}
Connection ID: ${CONNECTION_ID}
Event ID: ${EVENT_ID}
Retry Response Event ID: ${RETRY_EVENT_ID}
Final Status: ${FINAL_STATUS}
Final Attempts: ${FINAL_ATTEMPTS}
LOGEOF

echo "[run] Log file contents:"
cat "${LOG_FILE}"

echo "[run] Done! Cleaning up..."
kill "${LISTEN_PID}" 2>/dev/null || true
kill "${SERVER_PID}" 2>/dev/null || true

echo "[run] SUCCESS"
