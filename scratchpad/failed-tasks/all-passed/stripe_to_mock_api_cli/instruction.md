# Stripe to Mock API Connection

## Background
Hookdeck can route incoming webhooks from external providers to a destination. In this task, you will create a connection from a Stripe source to a Mock API destination using the Hookdeck CLI.

## Requirements
- Create a Hookdeck connection that links a new Stripe source to a new Mock API destination.
- The connection name must be `stripe-to-mock-${run-id}`.
- The source name must be `stripe-${run-id}` and its type must be `STRIPE`.
- The destination name must be `mock-api-${run-id}` and its type must be `MOCK_API`.
- Save the created connection's ID to a log file.

## Implementation Hints
- Read the `ZEALT_RUN_ID` environment variable to get the `run-id`.
- Output the connection ID to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/output.log
- The Hookdeck connection named `stripe-to-mock-${run-id}` must exist in the system.
- The connection must link a source named `stripe-${run-id}` (type `STRIPE`) to a destination named `mock-api-${run-id}` (type `MOCK_API`).
- The log file must contain the connection ID in the format: `Connection ID: <connection_id>`.
