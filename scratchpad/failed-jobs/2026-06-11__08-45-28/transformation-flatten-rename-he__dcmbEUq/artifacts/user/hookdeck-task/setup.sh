#!/usr/bin/env bash
set -euo pipefail

API_KEY="${HOOKDECK_API_KEY}"
RUN_ID="${ZEALT_RUN_ID}"
BASE_URL="https://api.hookdeck.com/2025-07-01"
LOG_FILE="/home/user/hookdeck-task/output.log"

SOURCE_NAME="flatten-src-${RUN_ID}"
DEST_NAME="flatten-dest-${RUN_ID}"
CONN_NAME="flatten-conn-${RUN_ID}"
TRANS_NAME="flatten-rename-${RUN_ID}"

echo "=== Hookdeck Pipeline Setup ==="
echo "Run ID: ${RUN_ID}"
echo "Source: ${SOURCE_NAME}"
echo "Destination: ${DEST_NAME}"
echo "Connection: ${CONN_NAME}"
echo "Transformation: ${TRANS_NAME}"

# Helper: call Hookdeck API
api() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  if [ -n "$data" ]; then
    curl -s -X "$method" "${BASE_URL}${path}" \
      -H "Authorization: Bearer ${API_KEY}" \
      -H "Content-Type: application/json" \
      -d "$data"
  else
    curl -s -X "$method" "${BASE_URL}${path}" \
      -H "Authorization: Bearer ${API_KEY}" \
      -H "Content-Type: application/json"
  fi
}

# ─── 1. Create Source ────────────────────────────────────────────────────────
echo ""
echo "--- Creating Source ---"
SOURCE_RESP=$(api POST "/sources" "{\"name\": \"${SOURCE_NAME}\", \"type\": \"WEBHOOK\"}")
echo "$SOURCE_RESP" | python3 -m json.tool 2>/dev/null || echo "$SOURCE_RESP"

SOURCE_ID=$(echo "$SOURCE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
SOURCE_URL=$(echo "$SOURCE_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('url', d.get('ingest_url', '')))")

echo "Source ID: ${SOURCE_ID}"
echo "Source URL: ${SOURCE_URL}"

# ─── 2. Create Destination ───────────────────────────────────────────────────
echo ""
echo "--- Creating Destination ---"
DEST_RESP=$(api POST "/destinations" "{\"name\": \"${DEST_NAME}\", \"type\": \"MOCK_API\"}")
echo "$DEST_RESP" | python3 -m json.tool 2>/dev/null || echo "$DEST_RESP"

DEST_ID=$(echo "$DEST_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
echo "Destination ID: ${DEST_ID}"

# ─── 3. Create Transformation ────────────────────────────────────────────────
echo ""
echo "--- Creating Transformation ---"

TRANSFORM_CODE='addHandler("transform", (request, context) => {
  const obj = request.body && request.body.data && request.body.data.object;
  if (!obj) return null;
  if (obj.amount < 100) return null;
  request.body = {
    id: obj.id,
    amount: obj.amount,
    currency: obj.currency,
    email: obj.customer_email
  };
  request.headers["x-hookdeck-transformed"] = "true";
  return request;
});'

# Escape the code for JSON
TRANSFORM_CODE_ESCAPED=$(python3 -c "
import json, sys
code = sys.stdin.read()
print(json.dumps(code))
" <<'PYEOF'
addHandler("transform", (request, context) => {
  const obj = request.body && request.body.data && request.body.data.object;
  if (!obj) return null;
  if (obj.amount < 100) return null;
  request.body = {
    id: obj.id,
    amount: obj.amount,
    currency: obj.currency,
    email: obj.customer_email
  };
  request.headers["x-hookdeck-transformed"] = "true";
  return request;
});
PYEOF
)

TRANS_PAYLOAD=$(python3 -c "
import json
name = '${TRANS_NAME}'
code = '''addHandler(\"transform\", (request, context) => {
  const obj = request.body && request.body.data && request.body.data.object;
  if (!obj) return null;
  if (obj.amount < 100) return null;
  request.body = {
    id: obj.id,
    amount: obj.amount,
    currency: obj.currency,
    email: obj.customer_email
  };
  request.headers[\"x-hookdeck-transformed\"] = \"true\";
  return request;
});'''
print(json.dumps({'name': name, 'code': code}))
")

echo "Transformation payload: $TRANS_PAYLOAD"

TRANS_RESP=$(api POST "/transformations" "$TRANS_PAYLOAD")
echo "$TRANS_RESP" | python3 -m json.tool 2>/dev/null || echo "$TRANS_RESP"

TRANS_ID=$(echo "$TRANS_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
echo "Transformation ID: ${TRANS_ID}"

# ─── 4. Create Connection ────────────────────────────────────────────────────
echo ""
echo "--- Creating Connection ---"

CONN_PAYLOAD=$(python3 -c "
import json
payload = {
  'name': '${CONN_NAME}',
  'source_id': '${SOURCE_ID}',
  'destination_id': '${DEST_ID}',
  'rules': [
    {
      'type': 'transformation',
      'transformation_id': '${TRANS_ID}'
    }
  ]
}
print(json.dumps(payload))
")

echo "Connection payload: $CONN_PAYLOAD"

CONN_RESP=$(api POST "/connections" "$CONN_PAYLOAD")
echo "$CONN_RESP" | python3 -m json.tool 2>/dev/null || echo "$CONN_RESP"

CONN_ID=$(echo "$CONN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['id'])")
echo "Connection ID: ${CONN_ID}"

# ─── 5. Publish Test Events ──────────────────────────────────────────────────
echo ""
echo "--- Publishing Test Events ---"

# Event 1: amount=50 (should be dropped)
EVENT1_PAYLOAD=$(python3 -c "
import json
payload = {
  'data': {
    'object': {
      'id': 'evt_001_${RUN_ID}',
      'amount': 50,
      'currency': 'usd',
      'customer_email': 'alice_${RUN_ID}@example.com'
    }
  }
}
print(json.dumps(payload))
")

echo "Publishing event 1 (amount=50, should be dropped)..."
EVT1_RESP=$(curl -s -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -d "$EVENT1_PAYLOAD")
echo "$EVT1_RESP"

sleep 1

# Event 2: amount=200 (should be delivered)
EVENT2_PAYLOAD=$(python3 -c "
import json
payload = {
  'data': {
    'object': {
      'id': 'evt_002_${RUN_ID}',
      'amount': 200,
      'currency': 'usd',
      'customer_email': 'bob_${RUN_ID}@example.com'
    }
  }
}
print(json.dumps(payload))
")

echo "Publishing event 2 (amount=200, should be delivered)..."
EVT2_RESP=$(curl -s -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -d "$EVENT2_PAYLOAD")
echo "$EVT2_RESP"

sleep 1

# Event 3: amount=200 (should be delivered)
EVENT3_PAYLOAD=$(python3 -c "
import json
payload = {
  'data': {
    'object': {
      'id': 'evt_003_${RUN_ID}',
      'amount': 200,
      'currency': 'eur',
      'customer_email': 'carol_${RUN_ID}@example.com'
    }
  }
}
print(json.dumps(payload))
")

echo "Publishing event 3 (amount=200, should be delivered)..."
EVT3_RESP=$(curl -s -X POST "${SOURCE_URL}" \
  -H "Content-Type: application/json" \
  -d "$EVENT3_PAYLOAD")
echo "$EVT3_RESP"

# ─── 6. Poll for Event Processing ────────────────────────────────────────────
echo ""
echo "--- Polling for Event Processing ---"

python3 - <<PYEOF
import time
import urllib.request
import urllib.error
import json

api_key = "${API_KEY}"
base_url = "${BASE_URL}"
source_id = "${SOURCE_ID}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def api_get(path):
    req = urllib.request.Request(f"{base_url}{path}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

max_attempts = 30
attempt = 0
while attempt < max_attempts:
    attempt += 1
    print(f"Poll attempt {attempt}/{max_attempts}...")
    try:
        # Get events for our source
        result = api_get(f"/events?source_id={source_id}&limit=20")
        events = result.get("models", [])
        print(f"  Found {len(events)} events")
        
        # Count events by status
        status_counts = {}
        for evt in events:
            status = evt.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        print(f"  Status counts: {status_counts}")
        
        # Check if we have at least 3 events total and none are pending
        if len(events) >= 3:
            pending_count = status_counts.get("pending", 0)
            if pending_count == 0:
                print("  All events processed!")
                break
    except Exception as e:
        print(f"  Error polling: {e}")
    
    time.sleep(3)

print("Polling complete.")
PYEOF

# ─── 7. Final status check and write log ─────────────────────────────────────
echo ""
echo "--- Final Status ---"
echo "Transformation ID: ${TRANS_ID}"
echo "Source ID: ${SOURCE_ID}"
echo "Destination ID: ${DEST_ID}"
echo "Connection ID: ${CONN_ID}"

# Write log file
RESULT_JSON=$(python3 -c "
import json
result = {
    'transformation_id': '${TRANS_ID}',
    'source_id': '${SOURCE_ID}',
    'destination_id': '${DEST_ID}',
    'connection_id': '${CONN_ID}'
}
print('RESULT: ' + json.dumps(result))
")

echo "$RESULT_JSON" > "${LOG_FILE}"
echo ""
echo "Log file written: ${LOG_FILE}"
cat "${LOG_FILE}"

echo ""
echo "=== Setup Complete ==="
