#!/usr/bin/env bash

curl -s \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -H "Accept: application/json" \
  -G "https://api.hookdeck.com/2025-07-01/metrics/requests" \
  --data-urlencode "date_range[start]=2025-06-01" \
  --data-urlencode "date_range[end]=2026-06-11" \
  --data-urlencode "measures[]=count" \
  -o metrics.json