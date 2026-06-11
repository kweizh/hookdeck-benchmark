# Create a Hookdeck Connection with Header Filter

## Background
You need to configure Hookdeck to receive webhooks and route them to a Mock API destination, but only if they contain a specific HTTP header. You are in a headless environment.

## Requirements
- Authenticate with Hookdeck in a headless CI environment.
- Create a new Connection named `header-filter-conn-${run-id}`.
- The Connection must use a Source named `header-source-${run-id}`.
- The Connection must route to a Mock API Destination named `mock-dest-${run-id}`.
- The Connection must include a Filter rule that only allows events where the HTTP header `x-target-event` equals exactly `process`.
- Output the resulting Connection ID to a log file.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- Ensure you login to Hookdeck CLI properly for a headless environment.
- You can use the Hookdeck CLI or the Hookdeck REST API to create the resources.
- Write the Connection ID to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the script is executed and the artifacts exist.
- Log file: `/home/user/hookdeck-task/output.log`
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.
- The connection must exist in Hookdeck with the exact name `header-filter-conn-${run-id}`.
- The connection must be linked to a source named `header-source-${run-id}` and a destination named `mock-dest-${run-id}`.
- The connection must have a filter rule configured to allow only events where the header `x-target-event` equals `process`.

