#!/bin/bash

# Authenticate if needed
if [ -n "$HOOKDECK_API_KEY" ]; then
  hookdeck ci > /dev/null 2>&1
fi

run_id="${ZEALT_RUN_ID}"

# Create the first connection
res1=$(hookdeck gateway connection create \
  --name "conn-1-${run_id}" \
  --source-name "fan-out-source-${run_id}" \
  --source-type WEBHOOK \
  --destination-name "mock-dest-1-${run_id}" \
  --destination-type MOCK_API \
  --destination-rate-limit 10 \
  --destination-rate-limit-period second \
  --output json)

# Create the second connection
res2=$(hookdeck gateway connection create \
  --name "conn-2-${run_id}" \
  --source-name "fan-out-source-${run_id}" \
  --source-type WEBHOOK \
  --destination-name "mock-dest-2-${run_id}" \
  --destination-type MOCK_API \
  --destination-rate-limit 50 \
  --destination-rate-limit-period second \
  --output json)

# Extract the Source URL from the JSON output
source_url=$(echo "$res1" | python3 -c "import sys, json; print(json.load(sys.stdin)['source']['url'])")

# Output the Source URL to the log file
echo "Source URL: $source_url" > /home/user/hookdeck-task/output.log
