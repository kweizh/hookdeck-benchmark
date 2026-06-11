# Retrieve Hookdeck Request by ID

## Background
Hookdeck provides an Inspect API to query the details of webhooks received by the platform.

## Requirements
- Write a script to retrieve a specific Hookdeck request by its ID using the REST API.
- The target request ID is provided via the `TARGET_REQUEST_ID` environment variable.
- The Hookdeck API key is provided via the `HOOKDECK_API_KEY` environment variable.
- Save the JSON response of the request to `/home/user/hookdeck-task/request.json`.

## Implementation Hints
- You can use any HTTP client (e.g., `curl`, `fetch`, `axios`) or language to make the API call.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifact exists.
- Output file: /home/user/hookdeck-task/request.json
- The output file must be valid JSON and contain the exact JSON response body returned by the Hookdeck API for the specified request ID.
