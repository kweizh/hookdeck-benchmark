# Hookdeck End-to-End Workflow

## Background
Set up a complete Hookdeck event pipeline in a headless environment, and verify its operation by publishing and inspecting an event.

## Requirements
- Authenticate with Hookdeck in a headless CI environment.
- Create a Source named `source-${run-id}`.
- Create a Destination named `mock-dest-${run-id}` using the Mock API destination type.
- Create a Connection named `conn-${run-id}` linking the Source and Destination.
- Publish a test event to the Source with a JSON payload containing `{"test_id": "${run-id}"}`.
- Verify the event is processed successfully.
- Write the Connection ID and the Event ID to a log file.

## Implementation Hints
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- Authenticate via `hookdeck ci --api-key $HOOKDECK_API_KEY`.
- Use the Mock API destination type to avoid needing a local server or active tunnel.
- You may use the Hookdeck CLI or REST API to provision resources, publish events, and inspect the delivery status.

## Acceptance Criteria
- Project path: /home/user/hookdeck-project
- Ensure the real resources are created in Hookdeck, the event is published, and the log artifact exists.
- Log file: /home/user/hookdeck-project/output.log
- The log file must contain exactly these two lines with the corresponding IDs:
  Connection ID: <connection_id>
  Event ID: <event_id>
- The Hookdeck Connection `conn-${run-id}` must exist and link `source-${run-id}` to `mock-dest-${run-id}`.
- The Event with the logged Event ID must have a `SUCCESSFUL` status and its payload must match `{"test_id": "${run-id}"}`.
