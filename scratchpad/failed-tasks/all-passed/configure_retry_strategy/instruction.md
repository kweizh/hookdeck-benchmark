# Configure a Retry Strategy with Hookdeck

## Background
Hookdeck provides a robust event gateway that can automatically retry failed webhook deliveries. By default, it might retry on various failures, but you can configure custom retry rules to control exactly which HTTP status codes trigger a retry.

## Requirements
- Create a Hookdeck Connection that links a Webhook source to a Mock API destination.
- Configure a retry rule on this connection so that it **only** retries on 5xx server errors (e.g., 500-599) and **ignores** 4xx client errors.
- The Connection name must be `retry-test-${run-id}`.
- The Source name must be `src-${run-id}` (type: `WEBHOOK`).
- The Destination name must be `dest-${run-id}` (type: `MOCK_API`).
- Save the resulting Connection ID to a log file.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- Use the `hookdeck connection upsert` command to create the connection and define the rules inline via the `--rules` flag.
- The retry rule needs a `response_status_codes` array. You can use ranges like `500-599` or operators like `>=500` to match 5xx errors.
- Write the created Connection ID to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The Connection name must be `retry-test-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The Source must be named `src-${run-id}` of type `WEBHOOK`.
- The Destination must be named `dest-${run-id}` of type `MOCK_API`.
- The Connection must have a Retry rule configured. The `response_status_codes` of the retry rule must match 5xx errors (e.g., contains `500-599` or `>=500`) and must not match 4xx errors.
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.

