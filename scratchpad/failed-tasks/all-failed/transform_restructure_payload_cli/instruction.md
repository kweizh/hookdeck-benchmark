# Restructure JSON Payload with Hookdeck Transformation

## Background
You need to configure a Hookdeck connection to receive webhooks from a legacy system, transform the payload, and forward it to a Mock API destination. The transformation must restructure the JSON payload and inject a secret token into the headers.

## Requirements
- Create a Hookdeck connection that links a new source to a Mock API destination.
- The connection name must be `legacy-to-mock-${run-id}`.
- The source name must be `legacy-source-${run-id}`.
- The destination name must be `mock-dest-${run-id}`.
- Add a JavaScript Transformation to the connection that does the following:
  - Extracts the `data.object` field from the incoming JSON payload and sets it as the new body.
  - Adds a custom header `x-hookdeck-transformed` with the value `true`.
  - Adds a custom header `x-secret-token` with a value read from the transformation's environment variable `SECRET_TOKEN`.
- The transformation's environment must have `SECRET_TOKEN` set to `super_secret_value_${run-id}`.
- Save the created Connection ID to a log file.

## Implementation Hints
- Use the `hookdeck ci --api-key $HOOKDECK_API_KEY` command to authenticate in the headless environment.
- Use the Hookdeck CLI or API to create the connection, source, destination, and transformation.
- You can read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- A transformation handler receives `request` and `context`. You can modify `request.body` and `request.headers`.
- Transformation environment variables can be accessed via `context.env`.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the configuration script is executed and the artifacts exist.
- Log file: `/home/user/hookdeck-task/output.log`
- The log file must contain the connection ID in the format: `Connection ID: <connection_id>`.
- A connection named `legacy-to-mock-${run-id}` must exist.
- The connection must use a Mock API destination named `mock-dest-${run-id}`.
- The connection must have a transformation that correctly extracts `data.object` to the body.
- The transformation must set the `x-hookdeck-transformed` header to `true`.
- The transformation must set the `x-secret-token` header to `super_secret_value_${run-id}`.

