# Configure Source Basic Authentication with Hookdeck CLI

## Background
Configure basic authentication for a Hookdeck Source using the Hookdeck CLI to secure incoming webhooks.

## Requirements
- Create a Hookdeck connection named `auth-conn-${run-id}`.
- The connection must have a Source named `auth-source-${run-id}` of type `WEBHOOK`.
- The connection must have a Destination named `auth-dest-${run-id}` of type `MOCK`.
- Configure Basic Authentication on the Source with the username `admin` and password `secret-password-${run-id}`.

## Implementation Hints
- Use the Hookdeck CLI to create the connection with inline source and destination.
- Apply the appropriate CLI flags for configuring source basic authentication.
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed.
- The connection name must be `auth-conn-${run-id}`.
- The source name must be `auth-source-${run-id}`.
- The destination name must be `auth-dest-${run-id}`.
- The source must have Basic Authentication configured with username `admin` and password `secret-password-${run-id}`.

