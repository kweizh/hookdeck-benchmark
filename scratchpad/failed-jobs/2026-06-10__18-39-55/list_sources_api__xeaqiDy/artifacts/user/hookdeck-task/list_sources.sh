#!/usr/bin/env bash
set -euo pipefail

# Retrieve Hookdeck sources via REST API
# Requires HOOKDECK_API_KEY environment variable

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${HOOKDECK_API_KEY:-}" ]; then
    echo "Error: HOOKDECK_API_KEY environment variable is not set" >&2
    exit 1
fi

curl -s -X GET "https://api.hookdeck.com/2025-07-01/sources" \
    -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
    -H "Content-Type: application/json" \
    -o "${SCRIPT_DIR}/sources.json"

echo "Sources retrieved and saved to ${SCRIPT_DIR}/sources.json"
