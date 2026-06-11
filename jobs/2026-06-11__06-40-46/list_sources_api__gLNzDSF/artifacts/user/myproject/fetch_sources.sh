#!/usr/bin/env bash
set -euo pipefail

API_KEY="${HOOKDECK_API_KEY:-}"
if [ -z "$API_KEY" ]; then
    echo "Error: HOOKDECK_API_KEY environment variable is not set" >&2
    exit 1
fi

# Fetch sources from Hookdeck API and extract names using Python
curl -s -H "Authorization: Bearer $API_KEY" \
     -H "Content-Type: application/json" \
     "https://api.hookdeck.com/2024-09-01/sources" | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('models', [])
for m in models:
    name = m.get('name')
    if name:
        print(name)
" > /home/user/myproject/sources.txt

echo "Sources written to /home/user/myproject/sources.txt"
