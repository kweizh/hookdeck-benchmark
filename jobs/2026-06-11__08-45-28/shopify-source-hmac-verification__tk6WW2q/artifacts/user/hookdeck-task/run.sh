#!/usr/bin/env bash
set -euo pipefail

# ── Environment variables ────────────────────────────────────────────────────
RUN_ID="${ZEALT_RUN_ID}"
API_KEY="${HOOKDECK_API_KEY}"
SECRET="${SHOPIFY_WEBHOOK_SECRET}"

SOURCE_NAME="shopify-verify-${RUN_ID}"
LOG_FILE="/home/user/hookdeck-task/output.log"
API_BASE="https://api.hookdeck.com/2025-07-01"

echo "=== Hookdeck Shopify HMAC Verification Task ===" | tee "$LOG_FILE"
echo "Run ID  : $RUN_ID"  | tee -a "$LOG_FILE"
echo "Source  : $SOURCE_NAME" | tee -a "$LOG_FILE"
echo "Time    : $(date -u)" | tee -a "$LOG_FILE"

# ── Step 0: Authenticate the Hookdeck CLI ────────────────────────────────────
echo "" | tee -a "$LOG_FILE"
echo "Authenticating Hookdeck CLI..." | tee -a "$LOG_FILE"
hookdeck ci --api-key "$API_KEY" 2>&1 | tee -a "$LOG_FILE"

# ── Step 1: Check if source already exists; delete if so ────────────────────
echo "" | tee -a "$LOG_FILE"
echo "Checking if source '$SOURCE_NAME' already exists..." | tee -a "$LOG_FILE"

EXISTING=$(curl -s "${API_BASE}/sources?name=${SOURCE_NAME}" \
  -H "Authorization: Bearer ${API_KEY}")

EXISTING_ID=$(echo "$EXISTING" | python3 -c "
import sys, json
d = json.load(sys.stdin)
models = d.get('models', [])
if models:
    print(models[0]['id'])
else:
    print('')
" 2>/dev/null || echo "")

if [ -n "$EXISTING_ID" ]; then
  echo "Found existing source $EXISTING_ID — deleting it..." | tee -a "$LOG_FILE"
  curl -s -X DELETE "${API_BASE}/sources/${EXISTING_ID}" \
    -H "Authorization: Bearer ${API_KEY}" | tee -a "$LOG_FILE"
  echo "" | tee -a "$LOG_FILE"
fi

# ── Step 2: Create the Source using the CLI (applies webhook_secret_key) ─────
echo "" | tee -a "$LOG_FILE"
echo "Creating Hookdeck Source '$SOURCE_NAME' with Shopify HMAC verification..." | tee -a "$LOG_FILE"

CREATE_OUTPUT=$(hookdeck gateway source create \
  --name "$SOURCE_NAME" \
  --type "SHOPIFY" \
  --webhook-secret "$SECRET" \
  --output json 2>&1)

echo "$CREATE_OUTPUT" | tee -a "$LOG_FILE"

SOURCE_ID=$(echo "$CREATE_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
SOURCE_URL=$(echo "$CREATE_OUTPUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])")
AUTHENTICATED=$(curl -s "${API_BASE}/sources/${SOURCE_ID}" \
  -H "Authorization: Bearer ${API_KEY}" | python3 -c "import sys,json; print(json.load(sys.stdin)['authenticated'])")

echo "" | tee -a "$LOG_FILE"
echo "Source ID     : $SOURCE_ID" | tee -a "$LOG_FILE"
echo "Source URL    : $SOURCE_URL" | tee -a "$LOG_FILE"
echo "Authenticated : $AUTHENTICATED" | tee -a "$LOG_FILE"

# ── Step 3: Create a destination + connection so verified:true requests route ──
echo "" | tee -a "$LOG_FILE"
echo "Creating MOCK_API destination..." | tee -a "$LOG_FILE"

DEST_RESP=$(curl -s -X POST "${API_BASE}/destinations" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"dest-${SOURCE_NAME}\", \"type\": \"MOCK_API\"}")

# Handle "already exists" gracefully
DEST_ID=$(echo "$DEST_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('id') or d.get('data', {}).get('id', ''))
")
echo "Destination ID: $DEST_ID" | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Creating connection source→destination..." | tee -a "$LOG_FILE"

CONN_RESP=$(curl -s -X POST "${API_BASE}/connections" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"conn-${SOURCE_NAME}\", \"source_id\": \"${SOURCE_ID}\", \"destination_id\": \"${DEST_ID}\"}")

CONN_ID=$(echo "$CONN_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('id') or d.get('data', {}).get('id', ''))
")
echo "Connection ID : $CONN_ID" | tee -a "$LOG_FILE"

# ── Step 4: Build the JSON body ──────────────────────────────────────────────
BODY_JSON=$(python3 -c "
import json
payload = {'event': 'order/created', 'run_id': '${RUN_ID}', 'test': True}
print(json.dumps(payload, separators=(',', ':'), sort_keys=True))
")
echo "" | tee -a "$LOG_FILE"
echo "Request body: $BODY_JSON" | tee -a "$LOG_FILE"

# ── Step 5: Compute correct HMAC-SHA256 signature ────────────────────────────
HMAC_B64=$(python3 << PYEOF
import hmac, hashlib, base64
secret = b'${SECRET}'
body   = b'${BODY_JSON}'
sig    = hmac.new(secret, body, hashlib.sha256).digest()
print(base64.b64encode(sig).decode())
PYEOF
)
echo "HMAC-SHA256 (base64): $HMAC_B64" | tee -a "$LOG_FILE"

# ── Step 6: Send correctly signed request ────────────────────────────────────
echo "" | tee -a "$LOG_FILE"
echo "Sending CORRECTLY signed request..." | tee -a "$LOG_FILE"

RESP1=$(curl -s -w "\n__HTTP_STATUS__%{http_code}" \
  -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Hmac-Sha256: ${HMAC_B64}" \
  --data-raw "${BODY_JSON}")

STATUS1=$(echo "$RESP1" | grep '__HTTP_STATUS__' | sed 's/__HTTP_STATUS__//')
BODY1=$(echo "$RESP1"   | sed '/^__HTTP_STATUS__/d')
echo "  HTTP $STATUS1: $BODY1" | tee -a "$LOG_FILE"

REQ1_ID=$(echo "$BODY1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('request_id',''))" 2>/dev/null || echo "")
echo "  Request ID (signed)  : $REQ1_ID" | tee -a "$LOG_FILE"

# ── Step 7: Send tampered / unsigned request ──────────────────────────────────
echo "" | tee -a "$LOG_FILE"
echo "Sending TAMPERED (wrong signature) request..." | tee -a "$LOG_FILE"

RESP2=$(curl -s -w "\n__HTTP_STATUS__%{http_code}" \
  -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Hmac-Sha256: aW52YWxpZHNpZ25hdHVyZQ==" \
  --data-raw "${BODY_JSON}")

STATUS2=$(echo "$RESP2" | grep '__HTTP_STATUS__' | sed 's/__HTTP_STATUS__//')
BODY2=$(echo "$RESP2"   | sed '/^__HTTP_STATUS__/d')
echo "  HTTP $STATUS2: $BODY2" | tee -a "$LOG_FILE"

REQ2_ID=$(echo "$BODY2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('request_id',''))" 2>/dev/null || echo "(rejected at ingress)")
echo "  Request ID (tampered): $REQ2_ID" | tee -a "$LOG_FILE"

# ── Step 8: Write required Source ID line ────────────────────────────────────
echo "" | tee -a "$LOG_FILE"
echo "Source ID: ${SOURCE_ID}" | tee -a "$LOG_FILE"

# ── Step 9: Wait for ingestion and verify via Inspect API ────────────────────
echo "" | tee -a "$LOG_FILE"
echo "Waiting 10 seconds for Hookdeck to ingest requests..." | tee -a "$LOG_FILE"
sleep 10

echo "" | tee -a "$LOG_FILE"
echo "Checking Inspect API for source_id=${SOURCE_ID}..." | tee -a "$LOG_FILE"

INSPECT=$(curl -s \
  "${API_BASE}/requests?source_id=${SOURCE_ID}" \
  -H "Authorization: Bearer ${API_KEY}")

echo "Inspect API response:" | tee -a "$LOG_FILE"
echo "$INSPECT" | python3 -m json.tool 2>/dev/null | tee -a "$LOG_FILE" || echo "$INSPECT" | tee -a "$LOG_FILE"

# ── Step 10: Summary ──────────────────────────────────────────────────────────
VERIFIED_TRUE=$(echo "$INSPECT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
models = d.get('models', [])
count = sum(1 for m in models if m.get('verified') == True)
print(count)
" 2>/dev/null || echo "0")

VERIFIED_FALSE=$(echo "$INSPECT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
models = d.get('models', [])
count = sum(1 for m in models if m.get('verified') == False and m.get('rejection_cause') == 'VERIFICATION_FAILED')
print(count)
" 2>/dev/null || echo "0")

echo "" | tee -a "$LOG_FILE"
echo "=== Summary ===" | tee -a "$LOG_FILE"
echo "Requests with verified=true                    : $VERIFIED_TRUE" | tee -a "$LOG_FILE"
echo "Requests with verified=false+VERIFICATION_FAILED: $VERIFIED_FALSE" | tee -a "$LOG_FILE"

if [ "$VERIFIED_TRUE" -ge 1 ] && [ "$VERIFIED_FALSE" -ge 1 ]; then
  echo "SUCCESS: Acceptance criteria met." | tee -a "$LOG_FILE"
else
  echo "WARNING: Acceptance criteria NOT yet met." | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "Done. Log written to $LOG_FILE"
