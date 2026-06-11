#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${ZEALT_RUN_ID}"
API_BASE="https://api.hookdeck.com/2025-07-01"
AUTH_HEADER="Authorization: Bearer ${HOOKDECK_API_KEY}"

echo "Using run-id: ${RUN_ID}"

# Authenticate with Hookdeck CLI (with retry for transient errors)
for i in 1 2 3; do
  if hookdeck ci --api-key "${HOOKDECK_API_KEY}" 2>/dev/null; then
    break
  fi
  echo "Hookdeck CI auth attempt ${i} failed, retrying..."
  sleep 2
done

# Helper: get resource ID by name, or empty string if not found
get_resource_id_by_name() {
  local resource_type="$1"
  local name="$2"
  local result
  result=$(curl -s -X GET "${API_BASE}/${resource_type}?name=${name}" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json")
  echo "${result}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
for m in models:
    if m.get('name') == '${name}':
        print(m['id'])
        sys.exit(0)
print('')
"
}

# --- Create Source ---
SOURCE_ID=$(get_resource_id_by_name "sources" "source-${RUN_ID}")
if [ -z "${SOURCE_ID}" ]; then
  echo "Creating source-${RUN_ID}..."
  SOURCE_OUTPUT=$(curl -s -X POST "${API_BASE}/sources" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"source-${RUN_ID}\", \"type\": \"WEBHOOK\"}")
  echo "Source created: ${SOURCE_OUTPUT}"
  SOURCE_ID=$(echo "${SOURCE_OUTPUT}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
else
  echo "Source source-${RUN_ID} already exists with ID: ${SOURCE_ID}"
fi

# --- Create Destination ---
DEST_ID=$(get_resource_id_by_name "destinations" "dest-${RUN_ID}")
if [ -z "${DEST_ID}" ]; then
  echo "Creating dest-${RUN_ID}..."
  DEST_OUTPUT=$(curl -s -X POST "${API_BASE}/destinations" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"dest-${RUN_ID}\", \"type\": \"MOCK_API\"}")
  echo "Destination created: ${DEST_OUTPUT}"
  DEST_ID=$(echo "${DEST_OUTPUT}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
else
  echo "Destination dest-${RUN_ID} already exists with ID: ${DEST_ID}"
fi

# --- Create Transformation ---
TRANSFORM_ID=$(get_resource_id_by_name "transformations" "flatten-${RUN_ID}")
if [ -z "${TRANSFORM_ID}" ]; then
  echo "Creating transformation flatten-${RUN_ID}..."
  TRANSFORMATION_CODE='addHandler("transform", (request, context) => { if (request.body && request.body.data && request.body.data.object) { request.body = request.body.data.object; } return request; });'
  TRANSFORM_OUTPUT=$(curl -s -X POST "${API_BASE}/transformations" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"flatten-${RUN_ID}\", \"code\": $(echo "${TRANSFORMATION_CODE}" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}")
  echo "Transformation created: ${TRANSFORM_OUTPUT}"
  TRANSFORM_ID=$(echo "${TRANSFORM_OUTPUT}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
else
  echo "Transformation flatten-${RUN_ID} already exists with ID: ${TRANSFORM_ID}"
fi

# --- Create Connection ---
CONN_ID=$(get_resource_id_by_name "connections" "conn-${RUN_ID}")
if [ -z "${CONN_ID}" ]; then
  echo "Creating connection conn-${RUN_ID}..."
  CONNECTION_OUTPUT=$(curl -s -X POST "${API_BASE}/connections" \
    -H "${AUTH_HEADER}" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"conn-${RUN_ID}\",
      \"source\": {\"id\": \"${SOURCE_ID}\", \"name\": \"source-${RUN_ID}\"},
      \"destination\": {\"id\": \"${DEST_ID}\", \"name\": \"dest-${RUN_ID}\"},
      \"rules\": [{\"transformation_id\": \"${TRANSFORM_ID}\", \"type\": \"transform\"}]
    }")
  echo "Connection created: ${CONNECTION_OUTPUT}"
  CONN_ID=$(echo "${CONNECTION_OUTPUT}" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
else
  echo "Connection conn-${RUN_ID} already exists with ID: ${CONN_ID}"
fi

echo "All resources created successfully!"
echo "Source ID: ${SOURCE_ID}"
echo "Destination ID: ${DEST_ID}"
echo "Transformation ID: ${TRANSFORM_ID}"
echo "Connection ID: ${CONN_ID}"