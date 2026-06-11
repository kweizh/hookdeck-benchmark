# Hookdeck Delay Rule: Deferred Delivery

## Background
You must configure a Hookdeck Connection that defers every inbound event by exactly 5 seconds before forwarding it to a Mock API destination, then prove the delay is actually being applied to real events.

## Requirements
- Configure a Hookdeck workspace such that events ingested by your Source are held for 5000ms by a delay rule and then delivered to a Mock API destination.
- Publish exactly 3 events through that Source.
- Each event's delivery must occur no sooner than 5 seconds after Hookdeck received it.

## Implementation Hints
- Authenticate the Hookdeck CLI in a headless way before doing anything else.
- A delay rule is one of the supported connection rule types; consult the Hookdeck connection rules reference to confirm its exact JSON schema and time unit.
- A `MOCK_API` destination accepts events without requiring inbound network access.
- Publish events via the Hookdeck Publish API or by POSTing directly to your Source URL.
- Hookdeck event objects expose both an ingestion timestamp (`created_at`) and a delivery timestamp (`successful_at`); the gap between them is the observable delay.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the connection is really created in Hookdeck and the 3 events are actually published and delivered.
- Log file: /home/user/hookdeck-task/output.log
- Read `run-id` from the `ZEALT_RUN_ID` environment variable. Use these exact names:
  - Source name: `delay-src-${run-id}`
  - Destination name: `delay-dst-${run-id}`
  - Connection name: `delay-conn-${run-id}`
- The connection must include a rule of type `delay` with delay value `5000` (in the unit expected by the Hookdeck API).
- The destination type must be `MOCK_API`.
- The log file must contain exactly 3 lines, one per published event, each in the format:
  `Event ID: <event_id>`
- All 3 events must reach status `SUCCESSFUL` in Hookdeck, and for each event `successful_at - created_at` must be at least 5000ms and less than 10000ms.

