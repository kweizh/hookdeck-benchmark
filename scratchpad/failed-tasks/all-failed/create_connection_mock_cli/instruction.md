# Create a Hookdeck Connection to a Mock Destination

## Background
Hookdeck acts as a reliable infrastructure layer for webhooks. In this task, you will create a new Connection linking a Source to a Mock Destination using the Hookdeck CLI.

## Requirements
- Authenticate with the Hookdeck CLI in a headless environment.
- Create a Connection linking a new Source to a new Mock Destination.
- Use the `ZEALT_RUN_ID` environment variable to name the resources uniquely:
  - Connection name: `mock-conn-${run-id}`
  - Source name: `mock-source-${run-id}`
  - Destination name: `mock-dest-${run-id}`
- Record the created Connection ID in a log file.

## Implementation Hints
- Use `hookdeck ci` for headless authentication.
- Use the Hookdeck CLI to create the connection, specifying the appropriate source and destination types.
- Remember to read `run-id` from the `ZEALT_RUN_ID` environment variable.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the connection creation is executed and the log artifact exists.
- Log file: `/home/user/hookdeck-task/output.log`
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.
- A Connection named `mock-conn-${run-id}` must exist in the Hookdeck workspace.
- The Connection must link a Source named `mock-source-${run-id}` and a Destination named `mock-dest-${run-id}`.
- The Destination type must be `MOCK`.

