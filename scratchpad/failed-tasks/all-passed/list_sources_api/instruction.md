# Retrieve Hookdeck Sources via REST API

## Background
Hookdeck provides a REST API to manage resources programmatically. You need to retrieve the list of sources using this API.

## Requirements
- Create a bash script `list_sources.sh` that retrieves the list of sources from the Hookdeck REST API.
- The script must save the raw JSON response to `sources.json`.

## Implementation Hints
- Use `curl` to make a GET request to the Hookdeck API (`https://api.hookdeck.com/2025-07-01/sources`).
- Authenticate using the `HOOKDECK_API_KEY` environment variable as a Bearer token.
- Remember the evaluation environment is headless (`hookdeck ci --api-key $HOOKDECK_API_KEY`) and uses Mock API destinations if you need to use the CLI for testing.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/sources.json
- The file `sources.json` must be a valid JSON object returned by the Hookdeck API containing a `models` array.
