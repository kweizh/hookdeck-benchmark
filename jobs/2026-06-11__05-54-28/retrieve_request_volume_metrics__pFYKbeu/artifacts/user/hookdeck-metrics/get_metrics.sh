#!/bin/bash

curl -s -X GET "https://api.hookdeck.com/2025-07-01/metrics/requests" \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -o metrics.json
