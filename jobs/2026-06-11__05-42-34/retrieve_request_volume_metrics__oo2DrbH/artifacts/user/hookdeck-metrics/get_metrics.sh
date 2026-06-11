#!/bin/bash

curl -s -g -X GET \
  "https://api.hookdeck.com/2025-07-01/metrics/requests?date_range[start]=2025-01-01T00:00:00Z&date_range[end]=2025-12-31T23:59:59Z&measures[]=count" \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -o metrics.json
