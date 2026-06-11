# Configure Fan-out Architecture in Hookdeck

## Background
You need to set up a fan-out architecture in Hookdeck where a single event source broadcasts to multiple destinations.

## Requirements
- Create one Hookdeck Source.
- Create two Hookdeck Destinations.
- Create two Connections to route events from the single Source to both Destinations.
- Record the Source URL in a log file.

## Implementation Hints
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- Append `-${run-id}` to all resource names (Source, Destinations, Connections) to avoid conflicts.
- Use the Hookdeck CLI or API to create the resources.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The Source name must be exactly `fan-out-source-${run-id}`.
- The two Destinations must be named exactly `mock-dest-1-${run-id}` and `mock-dest-2-${run-id}`. They must act as Mock API destinations (e.g., using `MOCK_API` type).
- Two connections must exist linking the Source to each of the two Destinations.
- The log file must contain the Source URL in the format: `Source URL: <source_url>`.
- When an event is published to the Source URL, it must be successfully delivered to both destinations.
