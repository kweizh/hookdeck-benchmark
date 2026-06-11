# Configure a Custom Retry Strategy in Hookdeck

## Background
Hookdeck provides robust automatic retry mechanisms for failed events. By default, connections might retry all failures, but you can configure specific rules based on HTTP response status codes. Your task is to create a connection that only retries 5xx errors and ignores 4xx errors.

## Requirements
- Create a new Connection named `custom-retry-conn-${run-id}`.
- The Connection must link a Source named `custom-retry-source-${run-id}` to a Mock Destination named `custom-retry-dest-${run-id}`.
- Configure a retry rule on the connection to retry exactly 5 times, with a linear strategy and a 1-minute (60000ms) interval.
- The retry rule must only trigger for HTTP 5xx errors (e.g., `500-599`). It must NOT retry 4xx errors.
- Write the resulting Connection ID to a log file.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable and append it to all resource names.
- You may use the Hookdeck CLI or REST API. Remember that the evaluation environment is headless.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the connection creation is executed and the resources exist in the Hookdeck workspace.
- Output a log file at `/home/user/hookdeck-task/output.log` containing the Connection ID in the exact format: `Connection ID: <connection_id>`.
- The connection must exist with the exact name `custom-retry-conn-${run-id}`.
- The connection's rules must include a retry rule configured for 5 retries, a linear strategy, a 60000ms interval, and `response_status_codes` covering `500-599`.

