# Hookdeck: Ordered Filter-then-Transform Rule Chain

## Background
You are wiring up a Hookdeck Connection that must enforce a strict, ORDERED processing chain for incoming webhooks: events are first filtered by type, and then the surviving events are enriched by a JavaScript transformation. The CLI is already installed in the environment.

## Requirements
- Use the Hookdeck API key from the `HOOKDECK_API_KEY` environment variable to authenticate the CLI/API/SDK.
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable and use it to suffix every Hookdeck resource you create.
- Create the following Hookdeck resources:
  - A Source named `chain-src-${run-id}` of type `WEBHOOK`.
  - A Destination named `chain-dest-${run-id}` of type `MOCK_API`.
  - A Connection named `chain-conn-${run-id}` linking the Source to the Destination.
- Attach an ORDERED `rules` array to the Connection containing exactly two rules, in this order:
  1. A `filter` rule that only allows events where the request `body.type` equals `"order.created"`.
  2. A `transformation` rule whose JavaScript code adds an ISO 8601 timestamp at `body.processed_at` (a string like `2026-01-14T13:36:06.365Z` representing roughly the current time) and adds an HTTP header `x-processed: true` to every event that reaches it.
- After the Connection is fully wired up, send 4 events to the source using Hookdeck's Publish API (`POST https://hkdk.events/v1/publish` with header `X-Hookdeck-Source-Name: chain-src-${run-id}`):
  - 2 events with body `{"type": "order.created", ...}` (any other fields allowed)
  - 2 events with body `{"type": ...}` where the type is something OTHER than `order.created` (for example `order.updated`, `customer.created`)
- Persist the Connection ID to a log file so the verifier can locate it.

## Implementation Hints
- You may use the Hookdeck CLI, REST API, or TypeScript SDK; the API base URL is `https://api.hookdeck.com/2025-07-01`.
- Order matters: the `rules` array index 0 must be the filter, index 1 must be the transformation. Confirm against the official docs how to express ordering and how to wire a created transformation into a connection.
- Transformations execute inside a V8 isolate without network or async I/O. A short pure-JS handler is sufficient; consult the docs if you are unsure of the handler signature.
- After publishing, give Hookdeck a few seconds to process events before exiting; the verifier waits independently as well.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real Hookdeck resources are created and events are published; do not mock the API.
- Log file: /home/user/hookdeck-task/output.log
  - Must contain a line `Connection ID: <connection_id>` where `<connection_id>` is the ID of the created Connection (starts with `web_`).
- The Connection named `chain-conn-${run-id}` exists in the Hookdeck workspace and links a `WEBHOOK` source named `chain-src-${run-id}` to a `MOCK_API` destination named `chain-dest-${run-id}`.
- The Connection's `rules` array has length 2, with `rules[0]` being the filter rule and `rules[1]` being the transformation rule, as observable via `GET /connections/:id`.
- The filter rule restricts events to those whose request `body.type` equals `order.created`.
- Exactly 2 events have been delivered through the Connection (verifiable via the Inspect API for the destination), and for each delivered event:
  - The event's request body contains a `processed_at` field whose value parses as an ISO 8601 timestamp dated within the last hour.
  - The event's headers contain `x-processed: true` (case-insensitive header name).

