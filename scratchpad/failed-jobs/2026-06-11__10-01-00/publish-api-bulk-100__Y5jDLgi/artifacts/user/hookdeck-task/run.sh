#!/bin/bash
set -euo pipefail

API_BASE="https://api.hookdeck.com/2025-07-01"
PUBLISH_URL="https://hkdk.events/v1/publish"
RUN_ID="${ZEALT_RUN_ID}"
API_KEY="${HOOKDECK_API_KEY}"
SOURCE_NAME="bulk-source-${RUN_ID}"
DEST_NAME="bulk-dest-${RUN_ID}"
CONN_NAME="bulk-conn-${RUN_ID}"
LOG_FILE="/home/user/hookdeck-task/output.log"
BATCH_ID="BATCH-001"

echo "=== Step 1: Create Connection with inline Source and Destination ==="
CREATE_RESP=$(curl -s -w "\n%{http_code}" \
  --location "${API_BASE}/connections" \
  --header "Content-Type: application/json" \
  --header "Authorization: Bearer ${API_KEY}" \
  --data "$(cat <<EOF
{
  "name": "${CONN_NAME}",
  "source": {
    "name": "${SOURCE_NAME}"
  },
  "destination": {
    "name": "${DEST_NAME}",
    "type": "MOCK_API"
  }
}
EOF
)")

HTTP_CODE=$(echo "$CREATE_RESP" | tail -1)
BODY=$(echo "$CREATE_RESP" | sed '$d')

echo "HTTP Status: ${HTTP_CODE}"
echo "Response: ${BODY}"

if [[ "$HTTP_CODE" != "200" && "$HTTP_CODE" != "201" ]]; then
  echo "ERROR: Failed to create connection. Response: ${BODY}"
  exit 1
fi

# Extract source ID and connection ID
SOURCE_ID=$(echo "${BODY}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('source_id',''))" 2>/dev/null || echo "")
CONNECTION_ID=$(echo "${BODY}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id',''))" 2>/dev/null || echo "")

echo "Source ID: ${SOURCE_ID}"
echo "Connection ID: ${CONNECTION_ID}"

# Sometimes the connection creation returns the source ID differently
if [[ -z "${SOURCE_ID}" ]]; then
  # Try to get source by name
  SOURCE_ID=$(curl -s "${API_BASE}/sources?name=${SOURCE_NAME}" \
    --header "Authorization: Bearer ${API_KEY}" | \
    python3 -c "import sys,json; d=json.load(sys.stdin); models=d.get('models',[]); print(models[0]['id'] if models else '')" 2>/dev/null || echo "")
  echo "Source ID (looked up): ${SOURCE_ID}"
fi

echo ""
echo "=== Step 2: Publish 100 events ==="
PUBLISHED=0
FAILED=0

for i in $(seq 0 99); do
  RESP=$(curl -s -w "\n%{http_code}" \
    --location "${PUBLISH_URL}" \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer ${API_KEY}" \
    --header "X-Hookdeck-Source-Name: ${SOURCE_NAME}" \
    --header "x-batch-id: ${BATCH_ID}" \
    --data "{\"i\": ${i}}")

  CODE=$(echo "$RESP" | tail -1)
  if [[ "$CODE" == "200" || "$CODE" == "201" || "$CODE" == "202" ]]; then
    PUBLISHED=$((PUBLISHED + 1))
  else
    FAILED=$((FAILED + 1))
    echo "FAILED publish for i=${i}, HTTP ${CODE}: $(echo "$RESP" | sed '$d')"
  fi
done

echo "Published: ${PUBLISHED}, Failed: ${FAILED}"

if [[ ${PUBLISHED} -ne 100 ]]; then
  echo "ERROR: Expected 100 published, got ${PUBLISHED}"
  exit 1
fi

echo ""
echo "=== Step 3: Wait for ingestion and delivery ==="
sleep 5

echo ""
echo "=== Step 4: Verify via Inspect API ==="

# Poll for requests
MAX_POLLS=30
POLL_INTERVAL=2
poll=0
request_count=0
event_count=0
successful_event_count=0

while [[ $poll -lt $MAX_POLLS ]]; do
  # Get requests for this source
  REQUESTS_RESP=$(curl -s "${API_BASE}/requests?source_id=${SOURCE_ID}" \
    --header "Authorization: Bearer ${API_KEY}")

  request_count=$(echo "${REQUESTS_RESP}" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  # The API wraps results in 'models' array
  if 'models' in d:
    print(len(d['models']))
  elif isinstance(d, list):
    print(len(d))
  else:
    print(0)
except:
  print(0)
" 2>/dev/null || echo "0")

  # Get events for this source (via connection)
  EVENTS_RESP=$(curl -s "${API_BASE}/events?source_id=${SOURCE_ID}" \
    --header "Authorization: Bearer ${API_KEY}")

  event_count=$(echo "${EVENTS_RESP}" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  if 'models' in d:
    print(len(d['models']))
  elif isinstance(d, list):
    print(len(d))
  else:
    print(0)
except:
  print(0)
" 2>/dev/null || echo "0")

  # Count successful events
  successful_event_count=$(echo "${EVENTS_RESP}" | python3 -c "
import sys,json
try:
  d=json.load(sys.stdin)
  models = d.get('models', d if isinstance(d, list) else [])
  count = sum(1 for m in models if m.get('status') == 'SUCCESSFUL')
  print(count)
except:
  print(0)
" 2>/dev/null || echo "0")

  echo "Poll ${poll}: requests=${request_count}, events=${event_count}, successful=${successful_event_count}"

  if [[ "${request_count}" -eq 100 && "${successful_event_count}" -eq 100 ]]; then
    echo "All 100 requests ingested and 100 events delivered successfully!"
    break
  fi

  poll=$((poll + 1))
  sleep ${POLL_INTERVAL}
done

echo ""
echo "=== Step 5: Verify request bodies and headers ==="

# Verify all request bodies are {"i": 0} through {"i": 99}
# We need to fetch all requests with pagination to verify body content
BODY_CHECK=$(curl -s "${API_BASE}/requests?source_id=${SOURCE_ID}&per_page=100" \
  --header "Authorization: Bearer ${API_KEY}" | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  models = d.get('models', d if isinstance(d, list) else [])
  bodies = []
  for m in models:
    data = m.get('data', {})
    body = data.get('body', '')
    if isinstance(body, str):
      try:
        body = json.loads(body)
      except:
        pass
    bodies.append(body)
  
  # Check we have exactly i=0 through i=99
  i_values = set()
  for b in bodies:
    if isinstance(b, dict) and 'i' in b:
      i_values.add(b['i'])
  
  expected = set(range(100))
  missing = expected - i_values
  extra = i_values - expected
  
  if missing:
    print(f'MISSING: {sorted(missing)}')
  if extra:
    print(f'EXTRA: {sorted(extra)}')
  if not missing and not extra:
    print('OK: All 100 bodies verified ({\"i\": 0} through {\"i\": 99})')
  print(f'TOTAL_BODIES_CHECKED: {len(bodies)}')
except Exception as e:
  print(f'ERROR: {e}')
")

echo "${BODY_CHECK}"

# Verify x-batch-id header on all requests
HEADER_CHECK=$(curl -s "${API_BASE}/requests?source_id=${SOURCE_ID}&per_page=100" \
  --header "Authorization: Bearer ${API_KEY}" | python3 -c "
import sys, json
try:
  d = json.load(sys.stdin)
  models = d.get('models', d if isinstance(d, list) else [])
  batch_count = 0
  for m in models:
    data = m.get('data', {})
    headers = data.get('headers', {})
    if headers.get('x-batch-id') == 'BATCH-001':
      batch_count += 1
  
  if batch_count == 100:
    print('OK: All 100 requests carry x-batch-id: BATCH-001')
  else:
    print(f'WARN: {batch_count}/100 requests carry x-batch-id: BATCH-001')
  print(f'HEADER_COUNT: {batch_count}')
except Exception as e:
  print(f'ERROR: {e}')
")

echo "${HEADER_CHECK}"

echo ""
echo "=== Step 6: Write summary log ==="

cat > "${LOG_FILE}" <<EOF
Source Name: ${SOURCE_NAME}
Destination Name: ${DEST_NAME}
Published Count: ${PUBLISHED}
Batch ID: ${BATCH_ID}
EOF

echo "Log file written to ${LOG_FILE}"
echo ""
echo "=== Final Summary ==="
echo "Source Name: ${SOURCE_NAME}"
echo "Destination Name: ${DEST_NAME}"
echo "Published Count: ${PUBLISHED}"
echo "Batch ID: ${BATCH_ID}"
echo "Requests ingested: ${request_count}"
echo "Events delivered (SUCCESSFUL): ${successful_event_count}"
