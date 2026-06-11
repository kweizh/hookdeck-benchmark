#!/usr/bin/env bash
# verify_event.sh - Publish a Hookdeck event and verify successful delivery

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
SOURCE_NAME="test-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
CONN_NAME="${SOURCE_NAME}-to-${DEST_NAME}"
LOG_FILE="$(dirname "$0")/output.log"
API_BASE="https://api.hookdeck.com/v1"

echo "=== Hookdeck Event Verification ==="
echo "Run ID    : ${RUN_ID}"
echo "Source    : ${SOURCE_NAME}"
echo "Dest      : ${DEST_NAME}"
echo "Log file  : ${LOG_FILE}"
echo ""

# ── Step 1: Authenticate in headless CI mode ─────────────────────────────────
echo "[1/5] Authenticating with Hookdeck CI..."
hookdeck ci --api-key "${API_KEY}"
echo "      Authentication successful."
echo ""

# ── Step 2: Create connection (source + MOCK_API destination) ────────────────
echo "[2/5] Upserting connection '${CONN_NAME}'..."
CONN_JSON=$(hookdeck connection upsert "${CONN_NAME}" \
  --source-type WEBHOOK \
  --source-name "${SOURCE_NAME}" \
  --destination-type MOCK_API \
  --destination-name "${DEST_NAME}" \
  --output json 2>&1)

echo "      Connection JSON: ${CONN_JSON}"

# Extract source URL and source_id from connection output
SOURCE_URL=$(echo "${CONN_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# The CLI may return a single object or a list
if isinstance(data, list):
    obj = data[0]
else:
    obj = data
src = obj.get('source', {})
url = src.get('url', '') or src.get('ingest_url', '')
print(url)
" 2>/dev/null || echo "")

SOURCE_ID=$(echo "${CONN_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if isinstance(data, list):
    obj = data[0]
else:
    obj = data
src = obj.get('source', {})
print(src.get('id', ''))
" 2>/dev/null || echo "")

echo "      Source URL : ${SOURCE_URL}"
echo "      Source ID  : ${SOURCE_ID}"
echo ""

# ── Step 3: Retrieve source details if not yet obtained ──────────────────────
if [ -z "${SOURCE_ID}" ] || [ -z "${SOURCE_URL}" ]; then
  echo "[3/5] Fetching source details from REST API..."
  SOURCE_JSON=$(curl -s -X GET \
    "${API_BASE}/sources?name=${SOURCE_NAME}" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json")
  echo "      Source JSON: ${SOURCE_JSON}"

  SOURCE_ID=$(echo "${SOURCE_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', data) if isinstance(data, dict) else data
if isinstance(models, list) and models:
    print(models[0].get('id', ''))
" 2>/dev/null || echo "")

  SOURCE_URL=$(echo "${SOURCE_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', data) if isinstance(data, dict) else data
if isinstance(models, list) and models:
    src = models[0]
    print(src.get('url', '') or src.get('ingest_url', ''))
" 2>/dev/null || echo "")

  echo "      Source URL : ${SOURCE_URL}"
  echo "      Source ID  : ${SOURCE_ID}"
else
  echo "[3/5] Source details obtained from connection creation output."
fi
echo ""

# ── Step 4: Publish an event via the Publish API ─────────────────────────────
echo "[4/5] Publishing event to source '${SOURCE_NAME}'..."

# The Hookdeck Publish API endpoint is the source ingest URL
PUBLISH_RESP=$(curl -s -X POST \
  "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -d "{\"run_id\":\"${RUN_ID}\",\"message\":\"verify_event test\"}" \
  -w "\n%{http_code}")

HTTP_BODY=$(echo "${PUBLISH_RESP}" | head -n -1)
HTTP_CODE=$(echo "${PUBLISH_RESP}" | tail -n 1)

echo "      Publish response [${HTTP_CODE}]: ${HTTP_BODY}"

if [ "${HTTP_CODE}" -lt 200 ] || [ "${HTTP_CODE}" -ge 300 ]; then
  echo "ERROR: Event publish failed with HTTP ${HTTP_CODE}" >&2
  exit 1
fi
echo ""

# ── Step 5: Poll the Inspect/Events API until status is SUCCESSFUL ───────────
echo "[5/5] Polling events for source '${SOURCE_ID}' (status=SUCCESSFUL)..."

MAX_ATTEMPTS=20
SLEEP_SEC=3
EVENT_ID=""

for attempt in $(seq 1 ${MAX_ATTEMPTS}); do
  echo "      Attempt ${attempt}/${MAX_ATTEMPTS}..."

  EVENT_JSON=$(hookdeck gateway event list \
    --source-id "${SOURCE_ID}" \
    --status SUCCESSFUL \
    --limit 10 \
    --output json 2>/dev/null || echo "[]")

  echo "      Event JSON: ${EVENT_JSON}"

  EVENT_ID=$(echo "${EVENT_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
# Could be a list or {'models': [...]}
if isinstance(data, dict):
    items = data.get('models', [])
else:
    items = data
if items:
    print(items[0].get('id', ''))
" 2>/dev/null || echo "")

  if [ -n "${EVENT_ID}" ]; then
    echo "      Found SUCCESSFUL event: ${EVENT_ID}"
    break
  fi

  echo "      No successful event yet, waiting ${SLEEP_SEC}s..."
  sleep ${SLEEP_SEC}
done

if [ -z "${EVENT_ID}" ]; then
  echo "ERROR: Timed out waiting for a SUCCESSFUL event after $((MAX_ATTEMPTS * SLEEP_SEC))s" >&2
  exit 1
fi

# ── Write result to log file ─────────────────────────────────────────────────
echo "Event ID: ${EVENT_ID}" > "${LOG_FILE}"
echo ""
echo "=== Verification complete ==="
echo "Event ID: ${EVENT_ID}"
echo "Log written to: ${LOG_FILE}"
