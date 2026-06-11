#!/usr/bin/env bash
# Retrieve the list of sources from the Hookdeck REST API
# and save the raw JSON response to sources.json

curl -s -X GET \
  -H "Authorization: Bearer $HOOKDECK_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.hookdeck.com/2025-07-01/sources" \
  -o /home/user/hookdeck-task/sources.json