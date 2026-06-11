#!/usr/bin/env bash
set -euo pipefail

API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
API_BASE="https://api.hookdeck.com/2025-07-01"
PUBLISH_URL="https://hkdk.events/v1/publish"
LOG_FILE="/home/user/hookdeck-task/output.log"

SRC_NAME="rl-src-${RUN_ID}"
DEST_NAME="rl-dest-${RUN_ID}"
CONN_NAME="rl-conn-${RUN_ID}"

echo "=== Hookdeck Rate Limit Task ==="
echo "RUN_ID: $RUN_ID"
echo "Source: $SRC_NAME"
echo "Destination: $DEST_NAME"
echo "Connection: $CONN_NAME"

# ---- 1. Create Source ----
echo "Creating source..."
SRC_RESPONSE=$(curl -s -X POST "${API_BASE}/sources" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${SRC_NAME}\"}")

SRC_ID=$(echo "$SRC_RESPONSE" | jq -r '.id')
echo "Source ID: $SRC_ID"

# ---- 2. Create Destination ----
echo "Creating destination..."
DEST_RESPONSE=$(curl -s -X POST "${API_BASE}/destinations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${DEST_NAME}\",
    \"type\": \"MOCK_API\",
    \"config\": {
      \"rate_limit\": 2,
      \"rate_limit_period\": \"minute\"
    }
  }")

DEST_ID=$(echo "$DEST_RESPONSE" | jq -r '.id')
echo "Destination ID: $DEST_ID"

# ---- 3. Create Connection ----
echo "Creating connection..."
CONN_RESPONSE=$(curl -s -X POST "${API_BASE}/connections" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${CONN_NAME}\",
    \"source_id\": \"${SRC_ID}\",
    \"destination_id\": \"${DEST_ID}\"
  }")

CONN_ID=$(echo "$CONN_RESPONSE" | jq -r '.id')
echo "Connection ID: $CONN_ID"

# Get the source URL for publishing
SRC_URL=$(echo "$SRC_RESPONSE" | jq -r '.url')
echo "Source URL: $SRC_URL"

# ---- 4. Publish 5 events ----
echo "Publishing 5 events..."
EVENT_PUBLISH_IDS=()
for i in $(seq 1 5); do
  PUB_RESPONSE=$(curl -s -X POST "${PUBLISH_URL}" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d "{
      \"source_id\": \"${SRC_ID}\",
      \"data\": {\"event_number\": ${i}, \"test\": \"rate-limit\"}
    }")
  PUB_ID=$(echo "$PUB_RESPONSE" | jq -r '.id // .event_id // empty')
  echo "Published event $i: $PUB_ID"
  if [ -n "$PUB_ID" ] && [ "$PUB_ID" != "null" ]; then
    EVENT_PUBLISH_IDS+=("$PUB_ID")
  fi
done

# ---- 5. Poll for SUCCESSFUL events ----
echo "Waiting for all 5 events to reach SUCCESSFUL status..."
MAX_WAIT=300  # 5 minutes max
ELAPSED=0
INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
  SUCCESSFUL=$(curl -s "${API_BASE}/events?destination_id=${DEST_ID}&status=SUCCESSFUL" \
    -H "Authorization: Bearer ${API_KEY}")
  
  SUCCESSFUL_COUNT=$(echo "$SUCCESSFUL" | jq '.data | length')
  echo "  [$ELAPSED s] Successful events: $SUCCESSFUL_COUNT / 5"
  
  if [ "$SUCCESSFUL_COUNT" -ge 5 ]; then
    break
  fi
  
  sleep $INTERVAL
  ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo "ERROR: Timed out waiting for events to become SUCCESSFUL"
  exit 1
fi

# ---- 6. Extract event IDs and timestamps ----
EVENT_IDS=$(echo "$SUCCESSFUL" | jq -r '.data | sort_by(.successful_at) | .[].id' | tr '\n' ',' | sed 's/,$//')
echo "Event IDs: $EVENT_IDS"

# Extract successful_at timestamps and verify pacing
TIMESTAMPS=$(echo "$SUCCESSFUL" | jq -r '.data | sort_by(.successful_at) | .[].successful_at')
echo "Successful_at timestamps:"
echo "$TIMESTAMPS"

# Calculate spread
FIRST_TS=$(echo "$TIMESTAMPS" | head -1)
LAST_TS=$(echo "$TIMESTAMPS" | tail -1)

# Convert to epoch seconds for comparison
FIRST_EPOCH=$(date -d "$FIRST_TS" +%s 2>/dev/null || python3 -c "from datetime import datetime; dt=datetime.fromisoformat('$FIRST_TS'.replace('Z','+00:00')); print(int(dt.timestamp()))")
LAST_EPOCH=$(date -d "$LAST_TS" +%s 2>/dev/null || python3 -c "from datetime import datetime; dt=datetime.fromisoformat('$LAST_TS'.replace('Z','+00:00')); print(int(dt.timestamp()))")

SPREAD=$((LAST_EPOCH - FIRST_EPOCH))
echo "Spread between first and last: ${SPREAD} seconds"

# Check consecutive gaps
echo "Checking consecutive gaps..."
PREV_EPOCH=""
MAX_GAP=0
MIN_GAP=99999
GAP_GT_25=false
for TS in $TIMESTAMPS; do
  EPOCH=$(date -d "$TS" +%s 2>/dev/null || python3 -c "from datetime import datetime; dt=datetime.fromisoformat('$TS'.replace('Z','+00:00')); print(int(dt.timestamp()))")
  if [ -n "$PREV_EPOCH" ]; then
    GAP=$((EPOCH - PREV_EPOCH))
    echo "  Gap: ${GAP} seconds"
    if [ $GAP -gt $MAX_GAP ]; then
      MAX_GAP=$GAP
    fi
    if [ $GAP -gt 25 ]; then
      GAP_GT_25=true
    fi
  fi
  PREV_EPOCH=$EPOCH
done

echo "Max consecutive gap: ${MAX_GAP} seconds"
echo "Any gap > 25s: $GAP_GT_25"

# ---- 7. Write log file ----
cat > "$LOG_FILE" <<EOF
Destination ID: ${DEST_ID}
Source ID: ${SRC_ID}
Connection ID: ${CONN_ID}
Event IDs: ${EVENT_IDS}
EOF

echo ""
echo "=== Log file written to $LOG_FILE ==="
cat "$LOG_FILE"
echo ""
echo "=== Verification ==="
echo "Spread >= 60s: $([ $SPREAD -ge 60 ] && echo 'PASS' || echo 'FAIL') ($SPREAD seconds)"
echo "Consecutive gap > 25s: $([ "$GAP_GT_25" = true ] && echo 'PASS' || echo 'FAIL')"