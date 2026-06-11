# Safe Payload Transformation

## Background
Webhook payloads often have inconsistent schemas. You need to configure Hookdeck to receive webhooks, safely extract a deeply nested field, and forward the transformed payload to a mock destination.

## Requirements
- Authenticate with Hookdeck in a headless environment.
- Create a Source named `safe-transform-src-${run-id}`.
- Create a Mock Destination named `safe-transform-dest-${run-id}`.
- Create a Connection between them.
- Add a JavaScript Transformation to the Connection that extracts `request.body.data.user.id` and assigns it to `request.body.user_id`. If any part of the path (`data`, `user`, or `id`) is missing, it must safely assign `null` to `request.body.user_id` without throwing an error.
- Write the Connection ID to a log file.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- Since this is a headless environment, use the `hookdeck ci` command for authentication.
- You can use the Hookdeck CLI or REST API to provision the resources.
- Transformations run in a V8 isolate; ensure your JavaScript uses safe property access (e.g., optional chaining) to prevent TypeErrors on missing fields.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the setup script is executed and the artifacts exist.
- Log file: `/home/user/hookdeck-task/output.log`
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.
- The Source and Destination must be named using the `run-id` as specified.
- The Destination type must be `MOCK`.
- The Transformation must correctly set `user_id` to the value of `data.user.id` if present, or `null` if missing, and must not fail (the event must be processed successfully).

