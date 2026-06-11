#!/bin/bash

# Ensure HOOKDECK_API_KEY is set
if [ -z "$HOOKDECK_API_KEY" ]; then
  echo "Error: HOOKDECK_API_KEY environment variable is not set." >&2
  exit 1
fi

# Calculate start and end dates
# end_date is current time
end_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
# start_date is 30 days ago
start_date=$(date -u -d "30 days ago" +"%Y-%m-%dT%H:%M:%SZ")

# Fetch request volume metrics and save to metrics.json
curl -g -s -X GET "https://api.hookdeck.com/2025-07-01/metrics/requests?date_range[start]=${start_date}&date_range[end]=${end_date}&measures[]=count" \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Accept: application/json" > metrics.json

# Check if curl succeeded
if [ $? -ne 0 ]; then
  echo "Error: Failed to fetch metrics from Hookdeck API." >&2
  exit 1
fi

echo "Successfully retrieved request volume metrics and saved to metrics.json"
