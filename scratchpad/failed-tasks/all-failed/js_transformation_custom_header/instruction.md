# Hookdeck JS Transformation with Env Var

## Background
Hookdeck allows you to apply JavaScript transformations to incoming webhooks before they reach their destination. You need to configure a connection with a transformation that modifies the payload and adds a custom header using an environment variable.

## Requirements
- Create a Hookdeck connection named `transform-connection-${run-id}`.
- The connection must link a source named `webhook-source-${run-id}` (type `WEBHOOK`) to a destination named `mock-dest-${run-id}` (type `MOCK_API`).
- Attach a JavaScript transformation to the connection.
- The transformation must:
  1. Rename the key `old_key` to `new_key` in the JSON payload body (keeping the same value). If `old_key` does not exist, do nothing to the body.
  2. Add a custom header `x-custom-secret` to the request. The value of this header must be read from the transformation's environment variable `MY_SECRET_ENV`.
- The transformation's environment variable `MY_SECRET_ENV` must be set to `secret-val-${run-id}`.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck CLI or API to create the source, destination, connection, and transformation.
- In Hookdeck transformations, environment variables are accessible via the `context.env` object.
- Make sure to authenticate using the `HOOKDECK_API_KEY` provided in the environment.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection and transformation creation actions are executed in Hookdeck.
- A connection named `transform-connection-${run-id}` must exist, linking `webhook-source-${run-id}` to `mock-dest-${run-id}`.
- The connection must have a transformation rule applied.
- The transformation must have an environment variable `MY_SECRET_ENV` set to `secret-val-${run-id}`.
- When a test event with the JSON body `{"old_key": "test_value"}` is published to the source, the delivered event must have the JSON body containing `"new_key": "test_value"` and the header `x-custom-secret: secret-val-${run-id}`.

