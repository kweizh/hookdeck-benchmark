# Create a Connection with Hookdeck CLI

## Background
Create a Hookdeck connection to route Stripe webhooks to a Mock API destination using the Hookdeck CLI.

## Requirements
- Create a connection using the Hookdeck CLI.
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- The connection name must be `stripe-connection-${run-id}`.
- The source name must be `stripe-source-${run-id}` and source type must be `STRIPE`.
- The destination name must be `mock-dest-${run-id}` and destination type must be `MOCK_API`.
- Save the connection name to a log file after creation.

## Implementation Hints
- Ensure you are authenticated with Hookdeck CLI using the `HOOKDECK_API_KEY` environment variable (e.g. `hookdeck ci --api-key $HOOKDECK_API_KEY`).
- Use the `hookdeck gateway connection create` command with the appropriate flags for name, source, and destination.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the connection name in the exact format: `Connection Name: stripe-connection-<run-id>` (where `<run-id>` is the value of `ZEALT_RUN_ID`).
- The connection named `stripe-connection-<run-id>` must be successfully created in the Hookdeck workspace.
- The connection must use a source named `stripe-source-<run-id>` of type `STRIPE`.
- The connection must use a destination named `mock-dest-<run-id>` of type `MOCK_API`.

