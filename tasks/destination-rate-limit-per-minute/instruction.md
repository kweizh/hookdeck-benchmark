# Pace Webhook Deliveries with a Per-Minute Destination Rate Limit

## Background
Hookdeck can throttle event delivery to a destination by configuring a maximum delivery rate. When the rate limit period is `minute`, Hookdeck spreads deliveries evenly across that minute. Your task is to wire up a Hookdeck pipeline that proves this behavior end-to-end against the public Hookdeck API and the built-in Mock API destination, and then trigger enough traffic to observe the pacing.

## Requirements
- Use the Hookdeck REST API (`https://api.hookdeck.com/2025-07-01`) with the API key from the `HOOKDECK_API_KEY` environment variable for all resource management.
- Read `run-id` from the `ZEALT_RUN_ID` environment variable and use it as a suffix for every resource you create so concurrent trials never collide.
- Create a `WEBHOOK` source named `rl-src-${run-id}`.
- Create a `MOCK_API` destination named `rl-dest-${run-id}` configured with `rate_limit = 2` and `rate_limit_period = minute`.
- Create a connection named `rl-conn-${run-id}` that links the source to the destination.
- Publish exactly 5 events through the connection in quick succession (well within a few seconds of each other) using the Hookdeck Publish API (`https://hkdk.events/v1/publish`) or the source URL.
- Wait until all 5 events have reached the `SUCCESSFUL` status on Hookdeck, then save the IDs to the log file.
- Save the destination ID, source ID, connection ID and event IDs to the log file in the formats described in Acceptance Criteria.

## Implementation Hints
- The Hookdeck REST API uses Bearer authentication. Mock API destinations require no inbound network — Hookdeck accepts the deliveries on your behalf.
- A rate limit of 2 per minute paces deliveries to one every 30 seconds, so all 5 events take roughly two minutes to drain. Make sure your polling logic waits long enough for the last event to flip to `SUCCESSFUL`.
- The `GET /events` endpoint accepts filters such as `destination_id` and `status`. You can poll it until 5 events with status `SUCCESSFUL` are returned for your destination.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/output.log
- The Mock API destination must exist in Hookdeck with the exact name `rl-dest-${run-id}`, `type = MOCK_API`, `config.rate_limit = 2`, and `config.rate_limit_period = minute` (where `run-id` is read from the `ZEALT_RUN_ID` environment variable).
- The Webhook source must exist with the exact name `rl-src-${run-id}` and `type = WEBHOOK`.
- The connection must exist with the exact name `rl-conn-${run-id}` and link the source and destination above.
- Exactly 5 events must have been delivered to the destination with status `SUCCESSFUL`.
- The 5 successful deliveries must be paced by the rate limit: the spread between the earliest and latest `successful_at` timestamps must be at least 60 seconds, and at least one consecutive gap between sorted `successful_at` values must be greater than 25 seconds.
- The log file must contain the following lines (one per identifier):
  - `Destination ID: <destination_id>`
  - `Source ID: <source_id>`
  - `Connection ID: <connection_id>`
  - `Event IDs: <evt_id_1>,<evt_id_2>,<evt_id_3>,<evt_id_4>,<evt_id_5>` (exactly 5 comma-separated IDs, no spaces required)

