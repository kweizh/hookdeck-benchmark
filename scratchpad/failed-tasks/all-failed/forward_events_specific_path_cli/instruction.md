# Create a CLI Forwarding Connection

## Background
Use the Hookdeck CLI to create a connection that forwards events to a local CLI destination with a specific path.

## Requirements
- Create a bash script `setup.sh` that creates a Hookdeck connection.
- The connection must link a new source to a new CLI destination.
- You must use `run-id` from the `ZEALT_RUN_ID` environment variable for naming.
- Execute the script so the connection is actually created in Hookdeck.

## Implementation Hints
- You are running in a headless CI environment; ensure you authenticate using `hookdeck ci --api-key $HOOKDECK_API_KEY` before running commands.
- Use `hookdeck gateway connection create` to create the connection, source, and destination in one command.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed.
- Script file: /home/user/hookdeck-task/setup.sh
- The connection name must be `cli-forward-conn-${run-id}` where `run-id` is read from `ZEALT_RUN_ID`.
- The source name must be `my-source-${run-id}` with source type `API`.
- The destination name must be `my-cli-dest-${run-id}` with destination type `CLI`.
- The destination CLI path must be `/api/webhooks`.
