#!/bin/bash

# Ensure HOOKDECK_API_KEY is set
if [ -z "$HOOKDECK_API_KEY" ]; then
  echo "Error: HOOKDECK_API_KEY environment variable is not set." >&2
  exit 1
fi

# Set output path
OUTPUT_PATH="/home/user/hookdeck-task/sources.json"

# Make the GET request to the Hookdeck API
curl -s -X GET "https://api.hookdeck.com/2025-07-01/sources" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Accept: application/json" > "$OUTPUT_PATH"

# Check if curl succeeded
if [ $? -eq 0 ]; then
  echo "Successfully fetched sources and saved to $OUTPUT_PATH"
else
  echo "Error: Failed to fetch sources." >&2
  exit 1
fi
