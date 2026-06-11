#!/usr/bin/env bash
set -euo pipefail

API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
API_BASE="https://api.hookdeck.com/2025-07-01"
LOG_FILE="/home/user/hookdeck-task/output.log"

echo "=== Hookdeck Chain Setup ===" | tee "$LOG_FILE"
echo "Run ID: $RUN_ID" | tee -a "$LOG_FILE"

SRC_NAME="chain-src-${RUN_ID}"
DEST_NAME="chain-dest-${RUN_ID}"
CONN_NAME="chain-conn-${RUN_ID}"
TRANS_NAME="chain-trans-${RUN_ID}"

# ── Step 1: Create a named transformation ──────────────────────────────────────
echo ""
echo "--- Step 1: Creating transformation: $TRANS_NAME ---" | tee -a "$LOG_FILE"

TRANS_CODE='addHandler("transform", function(request, context) {
  request.body["processed_at"] = new Date().toISOString();
  request.headers["x-processed"] = "true";
  return request;
});'

TRANS_RESPONSE=$(curl -s -X POST "${API_BASE}/transformations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg name "$TRANS_NAME" --arg code "$TRANS_CODE" '{name: $name, code: $code}')")

echo "Transformation response: $TRANS_RESPONSE" | tee -a "$LOG_FILE"

TRANS_ID=$(echo "$TRANS_RESPONSE" | jq -r '.id')
if [[ -z "$TRANS_ID" || "$TRANS_ID" == "null" ]]; then
  echo "ERROR: Failed to create transformation" | tee -a "$LOG_FILE"
  exit 1
fi
echo "Transformation ID: $TRANS_ID" | tee -a "$LOG_FILE"

# ── Step 2: Create Connection (with source + destination + ordered rules) ──────
echo ""
echo "--- Step 2: Creating Connection: $CONN_NAME ---" | tee -a "$LOG_FILE"

CONN_RESPONSE=$(curl -s -X PUT "${API_BASE}/connections" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg conn_name "$CONN_NAME" \
    --arg src_name "$SRC_NAME" \
    --arg dest_name "$DEST_NAME" \
    --arg trans_id "$TRANS_ID" \
    '{
      name: $conn_name,
      source: {
        name: $src_name,
        type: "WEBHOOK"
      },
      destination: {
        name: $dest_name,
        type: "MOCK_API"
      },
      rules: [
        {
          type: "filter",
          body: {
            type: "order.created"
          }
        },
        {
          type: "transformation",
          transformation_id: $trans_id
        }
      ]
    }')")

echo "Connection response: $CONN_RESPONSE" | tee -a "$LOG_FILE"

CONN_ID=$(echo "$CONN_RESPONSE" | jq -r '.id')
if [[ -z "$CONN_ID" || "$CONN_ID" == "null" ]]; then
  echo "ERROR: Failed to create connection" | tee -a "$LOG_FILE"
  exit 1
fi

echo ""
echo "Connection ID: $CONN_ID" | tee -a "$LOG_FILE"
echo "Source:        $SRC_NAME" | tee -a "$LOG_FILE"
echo "Destination:   $DEST_NAME" | tee -a "$LOG_FILE"

# ── Step 3: Publish 4 events ───────────────────────────────────────────────────
echo ""
echo "--- Step 3: Publishing 4 events ---" | tee -a "$LOG_FILE"

PUBLISH_URL="https://hkdk.events/v1/publish"

# Event 1: matching (order.created)
echo "Publishing event 1 (order.created, matching)..." | tee -a "$LOG_FILE"
E1=$(curl -s -X POST "$PUBLISH_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hookdeck-Source-Name: $SRC_NAME" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"type":"order.created","order_id":"ord-001","amount":99.99}')
echo "Event 1 response: $E1" | tee -a "$LOG_FILE"

# Event 2: matching (order.created)
echo "Publishing event 2 (order.created, matching)..." | tee -a "$LOG_FILE"
E2=$(curl -s -X POST "$PUBLISH_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hookdeck-Source-Name: $SRC_NAME" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"type":"order.created","order_id":"ord-002","amount":149.50}')
echo "Event 2 response: $E2" | tee -a "$LOG_FILE"

# Event 3: non-matching (order.updated)
echo "Publishing event 3 (order.updated, non-matching)..." | tee -a "$LOG_FILE"
E3=$(curl -s -X POST "$PUBLISH_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hookdeck-Source-Name: $SRC_NAME" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"type":"order.updated","order_id":"ord-001","status":"shipped"}')
echo "Event 3 response: $E3" | tee -a "$LOG_FILE"

# Event 4: non-matching (customer.created)
echo "Publishing event 4 (customer.created, non-matching)..." | tee -a "$LOG_FILE"
E4=$(curl -s -X POST "$PUBLISH_URL" \
  -H "Content-Type: application/json" \
  -H "X-Hookdeck-Source-Name: $SRC_NAME" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d '{"type":"customer.created","customer_id":"cust-001","email":"test@example.com"}')
echo "Event 4 response: $E4" | tee -a "$LOG_FILE"

echo ""
echo "--- Waiting 5 seconds for Hookdeck to process events ---" | tee -a "$LOG_FILE"
sleep 5

echo ""
echo "=== Setup Complete ===" | tee -a "$LOG_FILE"
echo "Connection ID: $CONN_ID" | tee -a "$LOG_FILE"
