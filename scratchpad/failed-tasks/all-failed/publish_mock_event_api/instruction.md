# Publish Mock Event via API

## Background
Hookdeck provides a Publish API to send events directly to a source, which is useful for outbound mocking and testing.

## Requirements
- Create a Hookdeck connection linking a new source `mock-source-${run-id}` to a mock destination `mock-dest-${run-id}`.
- Use the Publish API to send an event to `mock-source-${run-id}` with the JSON payload: `{"event": "test.created", "data": {"run_id": "${run-id}"}}`.
- Write a log file containing the name of the source.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- The API key is available in the `HOOKDECK_API_KEY` environment variable.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real actions are executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the source name in the format: `Source Name: mock-source-<run-id>`.
- A connection must exist in Hookdeck linking `mock-source-<run-id>` to `mock-dest-<run-id>`.
- The destination must be of type `MOCK_API`.
- An event with the payload `{"event": "test.created", "data": {"run_id": "<run-id>"}}` must have been successfully published to the source and processed by Hookdeck.
