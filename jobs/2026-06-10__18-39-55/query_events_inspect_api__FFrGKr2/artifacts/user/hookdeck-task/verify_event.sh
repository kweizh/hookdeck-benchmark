#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
PROJECT_DIR="/home/user/hookdeck-task"
LOG_FILE="${PROJECT_DIR}/output.log"
RUN_ID="${ZEALT_RUN_ID:-unknown-run}"
SOURCE_NAME="test-source-${RUN_ID}"
DEST_NAME="mock-dest-${RUN_ID}"
CONNECTION_NAME="test-conn-${RUN_ID}"

# Ensure the log file is fresh
: > "$LOG_FILE"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Starting event verification for run ID: ${RUN_ID}"

# ── Step 1: Authenticate in headless CI mode ─────────────────────────────────
log "Authenticating with Hookdeck CI..."
hookdeck ci --api-key "${HOOKDECK_API_KEY}" --local 2>&1 | tee -a "$LOG_FILE"
log "Authentication complete."

# ── Step 2: Create the connection (source + mock destination) ─────────────────
log "Creating connection '${CONNECTION_NAME}' with source '${SOURCE_NAME}' and mock destination '${DEST_NAME}'..."

CONN_JSON=$(hookdeck connection create \
  --name "${CONNECTION_NAME}" \
  --source-type WEBHOOK \
  --source-name "${SOURCE_NAME}" \
  --destination-type MOCK_API \
  --destination-name "${DEST_NAME}" \
  --output json 2>&1)

log "Connection created. Parsing response..."

# Extract the source ID from the connection JSON
SOURCE_ID=$(echo "$CONN_JSON" | jq -r '.source.id // .source_id // empty')

if [[ -z "$SOURCE_ID" ]]; then
  log "ERROR: Could not extract source ID from connection response."
  log "Raw response: $CONN_JSON"
  exit 1
fi

log "Source ID: ${SOURCE_ID}"

# ── Step 3: Get the source URL for publishing ────────────────────────────────
log "Retrieving source URL..."

SOURCE_JSON=$(hookdeck gateway source get "${SOURCE_ID}" --output json 2>&1)
SOURCE_URL=$(echo "$SOURCE_JSON" | jq -r '.url // empty')

if [[ -z "$SOURCE_URL" ]]; then
  log "ERROR: Could not extract source URL."
  log "Raw response: $SOURCE_JSON"
  exit 1
fi

log "Source URL: ${SOURCE_URL}"

# ── Step 4: Publish a mock event to the source ───────────────────────────────
log "Publishing mock event to source..."

PUBLISH_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "test.event",
    "data": {
      "message": "Hello from CI test",
      "run_id": "'"${RUN_ID}"'",
      "timestamp": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
    }
  }' 2>&1)

HTTP_CODE=$(echo "$PUBLISH_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$PUBLISH_RESPONSE" | sed '$d')

log "Publish response HTTP status: ${HTTP_CODE}"
log "Publish response body: ${RESPONSE_BODY}"

if [[ "$HTTP_CODE" -lt 200 || "$HTTP_CODE" -ge 300 ]]; then
  log "WARNING: Publish returned non-2xx status, but proceeding to check events..."
fi

# ── Step 5: Wait and poll for the event to be delivered ──────────────────────
log "Waiting for event delivery..."

MAX_RETRIES=20
RETRY_INTERVAL=3
EVENT_ID=""

for i in $(seq 1 $MAX_RETRIES); do
  log "Polling attempt ${i}/${MAX_RETRIES}..."

  EVENTS_JSON=$(hookdeck gateway event list \
    --source-id "${SOURCE_ID}" \
    --status SUCCESSFUL \
    --limit 5 \
    --output json 2>&1)

  # Try to extract the first successful event ID
  EVENT_ID=$(echo "$EVENTS_JSON" | jq -r '.data[0].id // .[0].id // empty' 2>/dev/null)

  if [[ -n "$EVENT_ID" && "$EVENT_ID" != "null" ]]; then
    log "Found successful event: ${EVENT_ID}"
    break
  fi

  log "No successful event yet. Retrying in ${RETRY_INTERVAL}s..."
  sleep "$RETRY_INTERVAL"
done

if [[ -z "$EVENT_ID" || "$EVENT_ID" == "null" ]]; then
  log "ERROR: No SUCCESSFUL event found after ${MAX_RETRIES} retries."
  log "Last events response: $EVENTS_JSON"
  exit 1
fi

# ── Step 6: Verify the event status is SUCCESSFUL ────────────────────────────
log "Verifying event status..."

EVENT_DETAIL=$(hookdeck gateway event get "${EVENT_ID}" --output json 2>&1)
EVENT_STATUS=$(echo "$EVENT_DETAIL" | jq -r '.status // empty')

log "Event ${EVENT_ID} status: ${EVENT_STATUS}"

if [[ "$EVENT_STATUS" != "SUCCESSFUL" ]]; then
  log "ERROR: Event status is '${EVENT_STATUS}', expected 'SUCCESSFUL'."
  exit 1
fi

# ── Step 7: Write the successful event ID to the log file ────────────────────
echo "Event ID: ${EVENT_ID}" >> "$LOG_FILE"
log "Event ID written to log file. Done!"

log "Verification complete. Event ${EVENT_ID} delivered successfully."
