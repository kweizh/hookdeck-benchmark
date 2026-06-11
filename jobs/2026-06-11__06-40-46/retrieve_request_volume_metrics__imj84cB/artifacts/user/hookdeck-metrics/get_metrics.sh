#!/usr/bin/env bash
set -euo pipefail

API_BASE="https://api.hookdeck.com/2025-07-01"
ENDPOINT="/metrics/requests"

if [ -z "${HOOKDECK_API_KEY:-}" ]; then
    echo "Error: HOOKDECK_API_KEY environment variable is not set." >&2
    exit 1
fi

curl -s -X GET "${API_BASE}${ENDPOINT}" \
    -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
    -H "Accept: application/json" \
    -o metrics.json

echo "Metrics saved to metrics.json"
