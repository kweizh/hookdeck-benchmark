# Drop Request on Missing Field Transformation

## Background
Create a Hookdeck transformation that validates incoming webhooks. If a specific required field is missing, the transformation should intentionally fail, dropping the request and preventing it from being forwarded.

## Requirements
- Create a Hookdeck Source named `source-${run-id}` of type `WEBHOOK`.
- Create a Hookdeck Destination named `dest-${run-id}` of type `MOCK_API`.
- Create a Connection named `conn-${run-id}` linking the source and destination.
- Create a Transformation named `drop-missing-field-${run-id}` and attach it to the connection.
- The transformation must inspect the JSON payload. If the field `required_field` is missing or undefined in the request body, the transformation must throw an error to drop the request.
- If `required_field` is present, the transformation must allow the request to pass unmodified.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck CLI or API to create the Source, Destination, Connection, and Transformation.
- In Hookdeck transformations, throwing a JavaScript `Error` results in a `FATAL` execution, which causes the request to be ignored (dropped) instead of being forwarded as an event.
- Write the resulting Source ID to a log file so it can be used for verification.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the real action is executed and the artifacts exist.
- Log file: `/home/user/hookdeck-task/output.log`
- The log file must contain the Source ID in the format: `Source ID: <source_id>`
- A Source, Destination, Connection, and Transformation with the `${run-id}` suffix must be created in the Hookdeck workspace.
- The Transformation must correctly drop requests missing `required_field` and allow requests containing `required_field`.

