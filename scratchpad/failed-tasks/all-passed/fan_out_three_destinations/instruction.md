# Configure a Fan-out Architecture in Hookdeck

## Background
Hookdeck can route a single incoming webhook to multiple destinations. This is known as a Fan-out architecture.

## Requirements
- Create a single Source in Hookdeck.
- Create three different Destinations with different configurations.
- Create Connections linking the Source to all three Destinations.
- Append the current `run-id` to all resource names to avoid collisions.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- Create a Source named `fanout-source-${run-id}`.
- Create three Destinations:
  - `mock-dest-1-${run-id}`: Type MOCK_API with a rate limit of 10 per second.
  - `mock-dest-2-${run-id}`: Type MOCK_API with a rate limit of 5 per minute.
  - `cli-dest-${run-id}`: Type CLI.
- Create three Connections linking the Source to each Destination.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real resource creation action is executed and the resources exist in the Hookdeck workspace.
- Source name must be exactly `fanout-source-${run-id}` where `run-id` is read from `ZEALT_RUN_ID`.
- Destinations must include:
  - `mock-dest-1-${run-id}` with type `MOCK_API`, rate limit 10, and rate limit period `second`.
  - `mock-dest-2-${run-id}` with type `MOCK_API`, rate limit 5, and rate limit period `minute`.
  - `cli-dest-${run-id}` with type `CLI`.
- Connections must exist linking `fanout-source-${run-id}` to each of the three destinations.

