#!/bin/bash

curl -s -X GET "https://api.hookdeck.com/2025-07-01/sources" \
  -H "Authorization: Bearer ${HOOKDECK_API_KEY}" \
  -o /home/user/hookdeck-task/sources.json
