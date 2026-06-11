# Paginate All Hookdeck Events for a Connection

## Background
Hookdeck's `GET /events` endpoint returns paged results using cursor (keyset) pagination. Your job is to walk the full result set for a specific connection (identified by `webhook_id`) and produce a summary file.

## Requirements
- Write an executable script at `/workspace/iterate.py` that, when run, iterates through every event belonging to the target connection and writes a summary JSON to `/workspace/result.json`.
- The target connection ID is provided via the `TARGET_CONNECTION_ID` environment variable.
- The Hookdeck API key is provided via the `HOOKDECK_API_KEY` environment variable.
- The summary file must contain:
  - `total`: integer count of all events returned across every page (deduplicated by event `id`).
  - `first_id`: the `id` of the first event in the full ordered traversal (i.e. the first event of page 1).
  - `last_id`: the `id` of the very last event reached after the final page.

## Implementation Hints
- Authenticate with `Authorization: Bearer ${HOOKDECK_API_KEY}` against `https://api.hookdeck.com/2025-07-01/events`.
- Scope results to the target connection via the `webhook_id` query parameter.
- The response body contains a `pagination` object. Use the cursor it exposes — there is no page-number parameter on this API.
- Stop iterating once the cursor for the next page is no longer present.

## Acceptance Criteria
- Project path: /workspace
- Ensure the script is executed and the artifacts exist.
- Output file: /workspace/result.json
- The output file must be valid JSON with the exact keys `total` (integer), `first_id` (string), and `last_id` (string).
- `total` must equal the true count of events for the target connection as independently verified by the verifier via the Hookdeck REST API.
- `first_id` and `last_id` must each be valid Hookdeck event IDs that belong to the target connection.

