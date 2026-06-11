#!/bin/bash
set -e

# Retrieve run-id from ZEALT_RUN_ID environment variable
run_id="${ZEALT_RUN_ID}"

if [ -z "$run_id" ]; then
  echo "Error: ZEALT_RUN_ID is not set or empty." >&2
  exit 1
fi

if [ -z "$HOOKDECK_API_KEY" ]; then
  echo "Error: HOOKDECK_API_KEY is not set or empty." >&2
  exit 1
fi

# Hookdeck CLI wrapper to map source-type "API" to "PUBLISH_API"
# since Hookdeck's underlying API uses "PUBLISH_API" for the "API" source type.
hookdeck() {
  local args=()
  for arg in "$@"; do
    if [ "$arg" = "API" ]; then
      args+=("PUBLISH_API")
    else
      args+=("$arg")
    fi
  done
  command hookdeck "${args[@]}"
}

echo "Authenticating Hookdeck CLI..."
hookdeck ci --api-key "$HOOKDECK_API_KEY"

echo "Creating Hookdeck connection..."
hookdeck gateway connection create \
  --name "cli-forward-conn-${run_id}" \
  --source-type "API" \
  --source-name "my-source-${run_id}" \
  --destination-type "CLI" \
  --destination-name "my-cli-dest-${run_id}" \
  --destination-cli-path "/api/webhooks"
