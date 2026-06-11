# Query Events using Inspect API

## Background
Hookdeck provides a Publish API to programmatically trigger events and an Inspect API to query their status. This task requires you to set up a connection, publish an event, and verify its delivery status using these APIs.

## Requirements
- Write a shell script `verify_event.sh` that automates the following steps.
- Authenticate with Hookdeck in a headless CI environment.
- Create a Hookdeck connection linking a new source to a Mock API destination.
- The source name must be `test-source-${run-id}` and the destination name must be `mock-dest-${run-id}`, where `${run-id}` is read from the `ZEALT_RUN_ID` environment variable.
- Trigger a mock event to the source using the Publish API.
- Query the events for the source using the Inspect API to verify the event delivery status is `SUCCESSFUL`.
- Write the successful event ID to a log file.

## Implementation Hints
- Use `hookdeck ci` for headless authentication.
- Use the CLI to create the connection with a `MOCK` destination type.
- You may need to use the Hookdeck REST API to retrieve the `source_id` for the Inspect API.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script `verify_event.sh` is executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the successful event ID in the format: `Event ID: <event_id>`

