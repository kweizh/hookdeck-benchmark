# Flatten Nested Payload Transformation

## Background
Hookdeck allows modifying webhooks using JavaScript transformations before delivering them to destinations.

## Requirements
- Authenticate with Hookdeck using the provided `$HOOKDECK_API_KEY` in the environment.
- Create a Hookdeck connection named `flatten-connection-${run-id}` linking a new source `flatten-source-${run-id}` to a new Mock API destination `flatten-dest-${run-id}`.
- Add a transformation to the connection that flattens a nested payload.
- The transformation must extract `id` and `email` from the `data.user` object and place them at the root level as `user_id` and `user_email`. The `data` object must be removed.

## Implementation Hints
- Use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate in the headless environment.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use Hookdeck CLI or API to provision the resources.

## Acceptance Criteria
- Project path: /home/user/project
- Ensure the connection, source, and destination are created in Hookdeck.
- The connection name must be `flatten-connection-${run-id}`.
- The source name must be `flatten-source-${run-id}`.
- The destination name must be `flatten-dest-${run-id}` and its type must be MOCK_API.
- The transformation must correctly flatten the nested payload:
  - Input JSON will contain `{"event_type": "<string>", "data": {"user": {"id": "<string>", "email": "<string>"}}}`.
  - The transformed body must be `{"event_type": "<string>", "user_id": "<string>", "user_email": "<string>"}`.
