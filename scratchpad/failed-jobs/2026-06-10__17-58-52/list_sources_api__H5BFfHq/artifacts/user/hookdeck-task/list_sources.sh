#!/bin/bash

# Retrieve list of sources from the Hookdeck REST API
# Requires HOOKDECK_API_KEY environment variable to be set

if [ -z "$HOOKDECK_API_KEY" ]; then
  echo "Error: HOOKDECK_API_KEY environment variable is not set." >&2
  exit 1
fi

curl -s -X GET "https://api.hookdeck.com/2025-07-01/sources" \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -H "Content-Type: application/json" \
  -o sources.json

echo "Response saved to sources.json"
