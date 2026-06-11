# Filter Webhooks by Payload Property

## Background
You need to route webhooks using Hookdeck, but only forward events that match a specific payload property.

## Requirements
- Authenticate the Hookdeck CLI in a headless environment.
- Create a new Hookdeck connection that links a webhook source to a mock destination.
- Apply a filter rule to the connection so that only events where `body.type` is `order.created` are allowed through.
- The connection, source, and destination names must be suffixed with the current `run-id`.
- Output the resulting Connection ID to a log file.

## Implementation Hints
- Use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate.
- Use the `hookdeck gateway connection create` command to set up the connection, source, destination, and rules in one step.
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the created Connection ID in the format: `Connection ID: <connection_id>`.
- The connection must have the following configuration:
  - Connection Name: `order-filter-${run-id}`
  - Source Name: `stripe-source-${run-id}`
  - Source Type: `WEBHOOK`
  - Destination Name: `mock-dest-${run-id}`
  - Destination Type: `MOCK`
  - Rules: Must include a filter rule that requires `body.type` to be `order.created`.

