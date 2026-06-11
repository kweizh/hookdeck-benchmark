# Hookdeck Fan-out with Per-Destination Rate Limits

## Background
Hookdeck is an Event Gateway that ingests webhooks at a Source and delivers them to one or more Destinations through Connections. A common pattern is to fan out a single Source to multiple Destinations, each with its own delivery rate limit so that downstream services with different throughput budgets receive the same events at safe paces.

In this task you will provision such a fan-out using the Hookdeck REST API (or CLI), then trigger traffic through the Source and verify that Hookdeck's per-Destination rate limiting actually paces delivery on the slow destination while leaving the fast destination uncapped.

You must read the `run-id` from the `ZEALT_RUN_ID` environment variable and embed it in every Source, Destination, and Connection name to avoid collisions when this task runs concurrently. The Hookdeck API key is available in the `HOOKDECK_API_KEY` environment variable.

## Requirements
- Provision the following topology in your Hookdeck project (all names must be suffixed with `-${ZEALT_RUN_ID}`):
  - One Source of type `WEBHOOK` named `fanout-src-${ZEALT_RUN_ID}`.
  - Two Destinations of type `MOCK_API`:
    - `fanout-fast-${ZEALT_RUN_ID}` with NO rate limit (uncapped).
    - `fanout-slow-${ZEALT_RUN_ID}` with `rate_limit = 2` and `rate_limit_period = "second"`.
  - Two Connections, each linking the single Source to one of the Destinations:
    - `fanout-fast-conn-${ZEALT_RUN_ID}`: Source → Fast Destination.
    - `fanout-slow-conn-${ZEALT_RUN_ID}`: Source → Slow Destination.
- Publish exactly 12 events through the Source in a tight burst (back-to-back, with little or no client-side delay) using Hookdeck's Publish API at `https://hkdk.events/v1/publish`. Every published event must reach the Source you created above, so all 12 events must fan out to BOTH destinations (24 delivered events total).
- After publishing, wait long enough for the rate-limited destination to drain its queue before declaring the task complete.
- Write a log file at `/home/user/hookdeck-fanout/output.log` that records the resulting `source_id`, both `destination_id` values, both `connection_id` (webhook) values, and the number of events you published. This log is the audit trail the verifier uses to locate the resources.

## Implementation Hints
- The Mock API destination type accepts every request and returns HTTP 200, so you do not need to host any HTTP server.
- The Publish API requires `Authorization: Bearer $HOOKDECK_API_KEY` plus either `X-Hookdeck-Source-Name` or `X-Hookdeck-Source-Id` to identify which Source receives the event.
- Destination delivery rate is configured on the Destination's `config` object (`rate_limit` integer + `rate_limit_period` of `"second"`, `"minute"`, `"hour"`, or `"concurrent"`); leaving `rate_limit` unset / `null` means no pacing.
- Use the Hookdeck REST API base URL `https://api.hookdeck.com/2025-07-01` (e.g. `POST /connections`, `GET /connections`, `GET /events`).
- 12 events fanned out to a destination capped at 2/second will take roughly 5–6 seconds to fully drain; plan your wait accordingly.
- Always consult the official Hookdeck API docs when in doubt: https://hookdeck.com/docs/api , https://hookdeck.com/docs/api/publish.md , https://hookdeck.com/docs/connections.md

## Acceptance Criteria
- Project path: /home/user/hookdeck-fanout
- Ensure the real publish action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-fanout/output.log
- The log file MUST contain, each on its own line, in the following exact formats (values are the IDs returned by Hookdeck):
  - `Source ID: <source_id>`
  - `Fast Destination ID: <fast_destination_id>`
  - `Slow Destination ID: <slow_destination_id>`
  - `Fast Connection ID: <fast_connection_id>`
  - `Slow Connection ID: <slow_connection_id>`
  - `Published Events: 12`
- Naming: every Source, Destination, and Connection name MUST end with `-${ZEALT_RUN_ID}` using the exact base names listed in Requirements.
- Rate-limit configuration (verified via `GET /destinations` and `GET /connections`):
  - The fast destination has `rate_limit` of `null`/unset.
  - The slow destination has `rate_limit = 2` AND `rate_limit_period = "second"`.
- Delivery outcome (verified via `GET /events?destination_id=...`):
  - Both destinations show exactly 12 events with `status = "SUCCESSFUL"`.
  - For the fast destination, `max(successful_at) - min(successful_at) < 2` seconds.
  - For the slow destination, `max(successful_at) - min(successful_at) >= 5` seconds (evidence that the 2/second cap actually paced delivery).

