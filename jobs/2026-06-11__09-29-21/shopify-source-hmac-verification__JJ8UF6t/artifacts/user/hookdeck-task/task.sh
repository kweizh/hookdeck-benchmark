#!/usr/bin/env bash
set -euo pipefail

# Read environment variables
RUN_ID="${ZEALT_RUN_ID}"
API_KEY="${HOOKDECK_API_KEY}"
SHOPIFY_SECRET="${SHOPIFY_WEBHOOK_SECRET}"

echo "Run ID: $RUN_ID"
echo "Shopify Secret: $SHOPIFY_SECRET"

SOURCE_NAME="shopify-verify-${RUN_ID}"

# Step 1: Login the Hookdeck CLI
hookdeck ci --api-key "$API_KEY"

# Step 2: Create a Shopify Source with HMAC verification using the CLI
# This ensures verification is properly configured
echo "Creating Shopify Source with verification..."

# Create a connection with a Shopify source that has webhook secret verification
# The CLI properly configures verification on the source
CONN_OUTPUT=$(hookdeck connection create \
  --name "${SOURCE_NAME}-conn" \
  --source-type SHOPIFY \
  --source-name "$SOURCE_NAME" \
  --source-webhook-secret "$SHOPIFY_SECRET" \
  --destination-type MOCK_API \
  --destination-name "mock-dest-${RUN_ID}" \
  --output json 2>&1)

echo "Connection created: $CONN_OUTPUT"

# Extract the source ID from the connection output
SOURCE_ID=$(echo "$CONN_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['id'])")
SOURCE_URL=$(echo "$CONN_OUTPUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['url'])")

echo "Source ID: $SOURCE_ID"
echo "Source URL: $SOURCE_URL"

# Step 3: Compute HMAC SHA-256 signature for the request body
BODY='{"test":"shopify-verification","timestamp":"2026-06-11"}'

# Compute base64-encoded HMAC SHA-256 of the raw body using the secret
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SHOPIFY_SECRET" -binary | base64)

echo "Computed HMAC signature: $SIGNATURE"

# Step 4: Send correctly signed request
echo "Sending correctly signed request..."
SIGNED_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST "$SOURCE_URL" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Hmac-Sha256: $SIGNATURE" \
  -d "$BODY")
echo "Signed response: $SIGNED_RESPONSE"

# Step 5: Send tampered request (wrong signature)
echo "Sending tampered request..."
TAMPERED_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
  -X POST "$SOURCE_URL" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Hmac-Sha256: wrong_signature_value" \
  -d "$BODY")
echo "Tampered response: $TAMPERED_RESPONSE"

# Step 6: Wait for Hookdeck to process the requests
echo "Waiting for Hookdeck to process requests..."
sleep 8

# Step 7: Verify via Inspect API
echo "Checking Inspect API..."
INSPECT_RESPONSE=$(curl -s "https://api.hookdeck.com/2025-07-01/requests?source_id=${SOURCE_ID}" \
  -H "Authorization: Bearer $API_KEY")
echo "Inspect API response:"
echo "$INSPECT_RESPONSE" | python3 -m json.tool

# Step 8: Write Source ID to log file
echo "Source ID: $SOURCE_ID" > /home/user/hookdeck-task/output.log

echo "Done! Source ID written to /home/user/hookdeck-task/output.log"
cat /home/user/hookdeck-task/output.log