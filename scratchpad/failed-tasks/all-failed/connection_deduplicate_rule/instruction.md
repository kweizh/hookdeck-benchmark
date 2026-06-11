# Set up a Hookdeck Connection with a Deduplicate Rule

## Background
Hookdeck provides rules to process events before delivery. You need to create a connection that deduplicates incoming events based on a custom time window and specific fields.

## Requirements
- Create a Hookdeck Source of type `WEBHOOK` named `source-${run-id}`.
- Create a Hookdeck Destination of type `MOCK_API` named `mock-api-${run-id}`.
- Create a Connection named `conn-${run-id}` that links the source to the destination.
- Add a `deduplicate` rule to the connection. The rule must have a window of `600` seconds and include the field `id` in the deduplication logic.
- Extract the created Connection ID and save it to a log file.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck CLI or the Hookdeck REST API to create the resources and apply the rule.
- Remember that you are in a headless environment, so ensure you authenticate appropriately with Hookdeck using the API key.
- Write the resulting Connection ID to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.
- The connection must exist in the Hookdeck workspace.
- The connection must be named `conn-${run-id}`.
- The connection must have a deduplicate rule with `window` set to 600 and `include_fields` containing `id`.
- The source must be named `source-${run-id}` and have type `WEBHOOK`.
- The destination must be named `mock-api-${run-id}` and have type `MOCK_API`.

