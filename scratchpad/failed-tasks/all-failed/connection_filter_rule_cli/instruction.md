# Create a Filtered Connection in Hookdeck

## Background
You need to route webhooks through Hookdeck but filter out low-value events before they reach your destination.

## Requirements
- Create a Hookdeck Connection linking a new Source (type: WEBHOOK) to a new Destination (type: MOCK_API).
- The connection name must be exactly `filtered-conn-${run-id}`.
- Add a Filter rule to this connection that only allows events where `body.amount` is strictly greater than 100.
- Save the resulting Connection ID to a log file.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- You may use the Hookdeck CLI, REST API, or SDK. If using the API, authenticate using the `HOOKDECK_API_KEY` environment variable.
- If you are missing API details for rule creation, consult the official Hookdeck documentation.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.
- The Connection must exist in the Hookdeck workspace with the name `filtered-conn-${run-id}`.
- The Connection must have a Filter rule that enforces `body.amount > 100`.
- The Source must be of type `WEBHOOK`.
- The Destination must be of type `MOCK_API`.

