# Configure Allowed HTTP Methods for a Source

## Background
Hookdeck allows you to restrict the HTTP methods that a source accepts. This is useful for ensuring that only specific types of webhooks (e.g., only `PUT` or `PATCH` requests) are processed by your infrastructure.

## Requirements
- Create a new Hookdeck connection linking a new source to a new Mock API destination.
- The source name must be `custom-methods-source-${run-id}`.
- The destination name must be `mock-dest-${run-id}` and its type must be `MOCK`.
- Configure the source to ONLY accept `PUT` and `PATCH` HTTP methods.
- Write the created Source ID to `/home/user/hookdeck-task/source_id.txt`.
- Write the created Connection ID to `/home/user/hookdeck-task/connection_id.txt`.

## Implementation Hints
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- Remember the evaluation environment is headless, so use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate if you use the CLI.
- You may need to use the Hookdeck REST API (e.g., `https://api.hookdeck.com/2025-07-01/sources`) to configure `allowed_http_methods`, as the CLI might not expose this specific configuration directly.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection and source creation actions are executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/source_id.txt containing only the Source ID.
- Log file: /home/user/hookdeck-task/connection_id.txt containing only the Connection ID.
- The source name must be `custom-methods-source-${run-id}` where `run-id` is read from `ZEALT_RUN_ID`.
- The destination name must be `mock-dest-${run-id}`.
- The source configuration must have `allowed_http_methods` set to exactly `["PUT", "PATCH"]`.

