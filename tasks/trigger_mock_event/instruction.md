# Trigger Mock Event via Publish API

## Background
Hookdeck provides a Publish API to directly send events to a source, which is useful for testing without a real third-party provider. In this task, you will create a connection to a Mock destination and use the Publish API to trigger an event.

## Requirements
- Write a bash script `run.sh` that uses the Hookdeck CLI and/or API to accomplish the following.
- Create a Hookdeck connection named `mock-conn-${run-id}` from a source named `mock-source-${run-id}` to a destination named `mock-dest-${run-id}`. The destination MUST be a Mock API destination.
- Trigger an event to the source `mock-source-${run-id}` using the Hookdeck Publish API.
- Retrieve the ID of the triggered event and append it to a log file.

## Implementation Hints
- Use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate in the headless environment.
- Use the Hookdeck CLI or REST API to create the connection with a MOCK destination.
- Use the Publish API (`https://hkdk.events/v1/publish`) to trigger the event.
- Use the Inspect API (`https://api.hookdeck.com/2025-07-01/events`) to find the triggered event ID.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script `run.sh` is executed and the required actions are performed.
- Log file: /home/user/hookdeck-task/output.log
- A connection named `mock-conn-${run-id}` linking source `mock-source-${run-id}` to destination `mock-dest-${run-id}` must be created in the Hookdeck workspace.
- The destination `mock-dest-${run-id}` must be of type MOCK.
- At least one event must be successfully published to `mock-source-${run-id}`.
- The log file must contain the triggered event ID in the exact format: `Event ID: <event_id>`.

