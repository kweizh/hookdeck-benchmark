#!/bin/bash
# Script to set up the Fan-out Architecture in Hookdeck

# Read run-id from ZEALT_RUN_ID
RUN_ID="${ZEALT_RUN_ID:-zr-n79pg7b}"

echo "Configuring Hookdeck Fan-out Architecture for run-id: ${RUN_ID}"

# 1. Create Source
echo "Creating source fanout-source-${RUN_ID}..."
hookdeck gateway source create \
  --name "fanout-source-${RUN_ID}" \
  --type "WEBHOOK"

# 2. Create Destinations
echo "Creating destination mock-dest-1-${RUN_ID}..."
hookdeck gateway destination create \
  --name "mock-dest-1-${RUN_ID}" \
  --type "MOCK_API" \
  --rate-limit 10 \
  --rate-limit-period "second"

echo "Creating destination mock-dest-2-${RUN_ID}..."
hookdeck gateway destination create \
  --name "mock-dest-2-${RUN_ID}" \
  --type "MOCK_API" \
  --rate-limit 5 \
  --rate-limit-period "minute"

echo "Creating destination cli-dest-${RUN_ID}..."
hookdeck gateway destination create \
  --name "cli-dest-${RUN_ID}" \
  --type "CLI"

# 3. Create Connections
echo "Creating connections linking source to destinations..."
hookdeck gateway connection create \
  --name "conn-mock-1-${RUN_ID}" \
  --source-name "fanout-source-${RUN_ID}" \
  --destination-name "mock-dest-1-${RUN_ID}"

hookdeck gateway connection create \
  --name "conn-mock-2-${RUN_ID}" \
  --source-name "fanout-source-${RUN_ID}" \
  --destination-name "mock-dest-2-${RUN_ID}"

hookdeck gateway connection create \
  --name "conn-cli-${RUN_ID}" \
  --source-name "fanout-source-${RUN_ID}" \
  --destination-name "cli-dest-${RUN_ID}"

echo "Fan-out Architecture set up successfully!"
