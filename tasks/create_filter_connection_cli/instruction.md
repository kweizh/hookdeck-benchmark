# Create a Hookdeck Connection with a Filter

## Background
Hookdeck is an Event Gateway that receives, processes, and delivers webhooks. You need to set up a connection that filters incoming events based on their payload.

## Requirements
- Authenticate with Hookdeck in a headless environment.
- Create a Source of type `WEBHOOK` named `source-${run-id}`.
- Create a Destination of type `MOCK_API` named `dest-${run-id}`.
- Create a Connection named `conn-${run-id}` linking the Source and Destination.
- Apply a Filter rule to the connection that only allows events where `body.type` is `order.created`.
- Write the resulting Connection ID to a log file.

## Implementation Hints
- The `HOOKDECK_API_KEY` environment variable is available. You can use it with the Hookdeck CLI or the REST API.
- Ensure you read the `ZEALT_RUN_ID` environment variable to suffix your resource names as required.
- You may need to use the Hookdeck REST API directly if the CLI lacks support for creating specific rule types.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real resource creation actions are executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The Source name must be `source-${run-id}`.
- The Destination name must be `dest-${run-id}` and its type must be `MOCK_API`.
- The Connection name must be `conn-${run-id}`.
- The Connection must have a filter rule configured to only allow events where `body.type` equals `order.created`.
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.

