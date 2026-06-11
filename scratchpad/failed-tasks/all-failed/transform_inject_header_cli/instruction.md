# Hookdeck Transformation to Inject Headers

## Background
Configure a Hookdeck connection that receives events and forwards them to a Mock API destination. Before forwarding, it must inject a custom header using a JavaScript transformation.

## Requirements
- Create a Hookdeck connection named `header-conn-${run-id}`.
- The source must be named `source-${run-id}`.
- The destination must be named `mock-dest-${run-id}` and configured as a MOCK destination.
- Create and attach a JavaScript transformation named `inject-header-${run-id}` to the connection.
- The transformation must inject a custom header `x-custom-run-id` with the value of the current `run-id` into the request.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck CLI (`hookdeck ci`) or the Hookdeck REST API to create the resources.
- The environment provides `HOOKDECK_API_KEY`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real resources are created in the Hookdeck workspace.
- A Connection named `header-conn-${run-id}` must exist.
- The Connection must link a Source named `source-${run-id}` to a Destination named `mock-dest-${run-id}`.
- The Destination `mock-dest-${run-id}` must be of type `MOCK`.
- A Transformation named `inject-header-${run-id}` must be attached to the connection.
- The Transformation code must successfully add the header `x-custom-run-id` with the value of `${run-id}` to the request headers.

