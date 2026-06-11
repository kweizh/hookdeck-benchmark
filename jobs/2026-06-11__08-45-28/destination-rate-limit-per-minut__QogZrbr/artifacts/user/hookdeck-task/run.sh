#!/usr/bin/env bash
# Hookdeck rate-limit pacing demo
# Requires: HOOKDECK_API_KEY, ZEALT_RUN_ID

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
API_BASE="https://api.hookdeck.com/2025-07-01"
LOG_FILE="$(dirname "$0")/output.log"

: "${HOOKDECK_API_KEY:?Environment variable HOOKDECK_API_KEY is required}"
: "${ZEALT_RUN_ID:?Environment variable ZEALT_RUN_ID is required}"

RUN_ID="${ZEALT_RUN_ID}"
SRC_NAME="rl-src-${RUN_ID}"
DEST_NAME="rl-dest-${RUN_ID}"
CONN_NAME="rl-conn-${RUN_ID}"

AUTH_HEADER="Authorization: Bearer ${HOOKDECK_API_KEY}"
JSON_HEADER="Content-Type: application/json"

echo "=== Hookdeck Rate-Limit Demo | run-id: ${RUN_ID} ==="

# ── Helper: curl wrappers ─────────────────────────────────────────────────────
api_put() {
  local path="$1"; shift
  curl -sS -X PUT \
    -H "${AUTH_HEADER}" \
    -H "${JSON_HEADER}" \
    "${API_BASE}${path}" "$@"
}

api_get() {
  local path="$1"; shift
  curl -sS \
    -H "${AUTH_HEADER}" \
    "${API_BASE}${path}" "$@"
}

check_error() {
  local label="$1"
  local body="$2"
  local status
  status=$(echo "${body}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','ok'))" 2>/dev/null || echo "ok")
  if [[ "${status}" != "ok" ]]; then
    echo "ERROR in ${label}: ${body}" >&2
    exit 1
  fi
}

# ── 1. Create / upsert source ─────────────────────────────────────────────────
echo ""
echo ">>> Creating source: ${SRC_NAME}"
SOURCE_RESP=$(api_put "/sources" \
  -d "{\"name\":\"${SRC_NAME}\",\"type\":\"WEBHOOK\"}")
echo "Source response: ${SOURCE_RESP}"
check_error "source creation" "${SOURCE_RESP}"

SOURCE_ID=$(echo "${SOURCE_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
SOURCE_URL=$(echo "${SOURCE_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['url'])")
echo "Source ID : ${SOURCE_ID}"
echo "Source URL: ${SOURCE_URL}"

# ── 2. Create / upsert destination ────────────────────────────────────────────
echo ""
echo ">>> Creating destination: ${DEST_NAME}"
DEST_RESP=$(api_put "/destinations" \
  -d "{\"name\":\"${DEST_NAME}\",\"type\":\"MOCK_API\",\"config\":{\"rate_limit\":2,\"rate_limit_period\":\"minute\"}}")
echo "Destination response: ${DEST_RESP}"
check_error "destination creation" "${DEST_RESP}"

DEST_ID=$(echo "${DEST_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
echo "Destination ID: ${DEST_ID}"

# ── 3. Create / upsert connection ─────────────────────────────────────────────
echo ""
echo ">>> Creating connection: ${CONN_NAME}"
CONN_RESP=$(api_put "/connections" \
  -d "{\"name\":\"${CONN_NAME}\",\"source\":{\"id\":\"${SOURCE_ID}\",\"name\":\"${SRC_NAME}\"},\"destination\":{\"id\":\"${DEST_ID}\",\"name\":\"${DEST_NAME}\"}}")
echo "Connection response: ${CONN_RESP}"
check_error "connection creation" "${CONN_RESP}"

CONN_ID=$(echo "${CONN_RESP}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
echo "Connection ID: ${CONN_ID}"

# ── 4. Publish 5 events quickly ───────────────────────────────────────────────
echo ""
echo ">>> Publishing 5 events to: ${SOURCE_URL}"

for i in 1 2 3 4 5; do
  echo "  Publishing event ${i}..."
  PUB_RESP=$(curl -sS -X POST \
    -H "${JSON_HEADER}" \
    "${SOURCE_URL}" \
    -d "{\"event_index\":${i},\"run_id\":\"${RUN_ID}\"}")
  echo "  Response: ${PUB_RESP}"
  sleep 0.3
done

echo ""
echo ">>> 5 events submitted. Waiting for rate-limited delivery..."
echo "    (rate_limit=2/min → ~30 s gap per delivery → ~2 min to drain all 5)"

# ── 5. Poll until all 5 events are SUCCESSFUL ────────────────────────────────
MAX_WAIT=420   # 7 minutes safety ceiling
POLL_INTERVAL=15
ELAPSED=0

while true; do
  sleep ${POLL_INTERVAL}
  ELAPSED=$((ELAPSED + POLL_INTERVAL))

  EVENTS_RESP=$(api_get "/events?destination_id=${DEST_ID}&status=SUCCESSFUL&limit=10")
  COUNT=$(echo "${EVENTS_RESP}" | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(len(d.get('models',[])))")
  echo "  [${ELAPSED}s] Successful events: ${COUNT}/5"

  if [[ "${COUNT}" -ge 5 ]]; then
    echo "  ✓ All 5 events are SUCCESSFUL"
    break
  fi

  if [[ "${ELAPSED}" -ge "${MAX_WAIT}" ]]; then
    echo "ERROR: Timed out after ${MAX_WAIT}s — only ${COUNT}/5 events succeeded." >&2
    exit 1
  fi
done

# ── 6. Collect event IDs ──────────────────────────────────────────────────────
echo ""
echo ">>> Collecting final event IDs..."
FINAL_RESP=$(api_get "/events?destination_id=${DEST_ID}&status=SUCCESSFUL&limit=10")
EVENT_IDS=$(echo "${FINAL_RESP}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
ids = [m['id'] for m in d.get('models', [])][:5]
print(','.join(ids))
")
echo "Event IDs: ${EVENT_IDS}"

# ── 7. Write output.log ───────────────────────────────────────────────────────
{
  echo "Destination ID: ${DEST_ID}"
  echo "Source ID: ${SOURCE_ID}"
  echo "Connection ID: ${CONN_ID}"
  echo "Event IDs: ${EVENT_IDS}"
} > "${LOG_FILE}"

echo ""
echo "=== Done. Contents of ${LOG_FILE} ==="
cat "${LOG_FILE}"
