# Implement a JS Transformation to Rename Keys

## Background
Webhooks often contain payload structures that do not match the expected schema of the receiving system. Hookdeck allows you to write JavaScript Transformations to mutate payloads in-flight before they are delivered to their destination.

## Requirements
- Create a Hookdeck Source named `transform-source-${run-id}` of type `WEBHOOK`.
- Create a Hookdeck Destination named `transform-dest-${run-id}` of type `MOCK_API`.
- Create a Hookdeck Connection named `transform-conn-${run-id}` linking the above source and destination.
- Apply a JavaScript Transformation rule to the connection.
- The transformation must mutate the JSON payload by renaming the root-level key `customer_id` to `userId`. The original `customer_id` key must be removed. All other payload data must remain intact.
- The transformation must also add a new header `x-custom-transformed` with the value `true` to the request.
- You must execute the necessary API calls or CLI commands to fully configure this in Hookdeck.

## Implementation Hints
- Read the `ZEALT_RUN_ID` environment variable to apply the `${run-id}` suffix to your resource names.
- You will need to use the Hookdeck API to create the transformation and attach it to the connection, as the CLI might not support inline JS transformation creation directly.
- Transformations in Hookdeck use a specific JavaScript function signature (e.g., `addHandler('transform', (request, context) => { ... })`).
- Ensure your code properly checks for the existence of `customer_id` in the body before attempting to rename it.

## Acceptance Criteria
- Project path: /home/user/project
- Ensure the real configuration actions are executed against the Hookdeck API.
- The Source `transform-source-${run-id}` must exist.
- The Destination `transform-dest-${run-id}` must exist.
- The Connection `transform-conn-${run-id}` must exist and link the source to the destination.
- The Connection must have a transformation rule applied.
- When a webhook with `{"customer_id": "12345", "other": "data"}` is sent to the source, the destination must receive a payload of `{"userId": "12345", "other": "data"}`.
- The delivered webhook must contain the header `x-custom-transformed: true`.

