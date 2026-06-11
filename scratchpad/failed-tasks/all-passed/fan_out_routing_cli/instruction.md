# Hookdeck Fan-out Architecture

## Background
Hookdeck is an Event Gateway that can route webhooks from a single Source to multiple Destinations (Fan-out pattern). You need to configure a fan-out architecture using the Hookdeck CLI in a headless environment.

## Requirements
- Authenticate with the Hookdeck CLI in a headless environment using the provided `HOOKDECK_API_KEY` environment variable.
- Create a single Source.
- Create two separate Mock Destinations.
- Create two Connections routing the single Source to both Mock Destinations.
- Use the `ZEALT_RUN_ID` environment variable to namespace your resources to avoid collisions during concurrent evaluations.
- Save the created connection names to a JSON file.

## Implementation Hints
- Use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate the CLI in a headless environment.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- Append `-${run-id}` to the names of your Source, Destinations, and Connections.
- Use `hookdeck gateway connection create` to create the connections. The CLI will automatically create the Source and Destination if they do not exist.
- For a Mock destination, specify `--destination-type MOCK`.
- For the source, you can use a generic type like `--source-type WEBHOOK` or `--source-type API`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real CLI configuration commands are executed and the output file exists.
- Output file: /home/user/hookdeck-task/output.json
- The output file must contain a valid JSON object with a key `connections` containing an array of the two connection names created (e.g., `["conn-1-...", "conn-2-..."]`).
- The Hookdeck workspace must have exactly one Source named `fanout-source-${run-id}`.
- The Hookdeck workspace must have exactly two Destinations named `mock-dest-1-${run-id}` and `mock-dest-2-${run-id}` with type `MOCK`.
- The Hookdeck workspace must have exactly two Connections: one named `conn-1-${run-id}` linking the source to `mock-dest-1-${run-id}`, and another named `conn-2-${run-id}` linking the source to `mock-dest-2-${run-id}`.
