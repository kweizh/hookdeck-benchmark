# Flatten Nested Payload Transformation

## Background
Configure Hookdeck to receive webhooks, transform the payload by flattening a nested JSON structure, and forward the result to a Mock API destination.

## Requirements
- Write a script `setup.sh` that sets up the required Hookdeck resources.
- Create a Source named `source-${run-id}`.
- Create a Mock Destination named `dest-${run-id}`.
- Create a JavaScript Transformation named `flatten-${run-id}`. The transformation must modify the payload so that if `request.body.data.object` exists, its value replaces the entire `request.body`.
- Create a Connection named `conn-${run-id}` that links the created Source, Destination, and Transformation.
- The execution environment is headless. Ensure you authenticate using the `HOOKDECK_API_KEY` environment variable (e.g., `hookdeck ci`).

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck CLI (`hookdeck gateway ...`) or the Hookdeck REST API (`https://api.hookdeck.com/2025-07-01/...`) to create the resources.
- A Hookdeck Mock destination accepts all events without forwarding them to an external server.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real resource creation action is executed by running `bash setup.sh`.
- A Source named `source-${run-id}` must exist.
- A Mock Destination named `dest-${run-id}` must exist.
- A Transformation named `flatten-${run-id}` must exist, and its code must correctly flatten `request.body.data.object` to `request.body`.
- A Connection named `conn-${run-id}` must exist, linking the Source, Destination, and Transformation.
- The transformation must successfully flatten a published event where the payload has `{"data": {"object": {"id": 123, "status": "ok"}}}` into `{"id": 123, "status": "ok"}`.

