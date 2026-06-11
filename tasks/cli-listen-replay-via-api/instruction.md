# Hookdeck: CLI Destination + Programmatic Replay

## Background
You are wiring a local development workflow on top of Hookdeck. A webhook producer pushes one event into a Hookdeck `WEBHOOK` source. Hookdeck must forward the event to a local HTTP server through a `CLI` destination created by `hookdeck listen`. The local server is flaky on first contact (returns `500` once, then `200`). Your job is to drive the recovery using the Hookdeck REST API: detect the failed event and replay it programmatically — not through the interactive TUI.

## Requirements
- Authenticate the Hookdeck CLI using `HOOKDECK_API_KEY` (headless, no browser).
- Run a tiny local HTTP server on port `3000` whose `POST /hooks` handler returns HTTP `500` on the first request and HTTP `200` on every subsequent request (in-memory toggle, one process).
- Use `hookdeck listen` to forward a `WEBHOOK` source to `http://localhost:3000/hooks`. The destination created by `hookdeck listen` must be of type `CLI` with `cli_path` equal to `/hooks`.
- Publish exactly one event to the source via the Hookdeck Publish API (`POST https://hkdk.events/v1/publish`).
- After the first delivery attempt FAILS, replay the event by calling the Hookdeck REST API endpoint `POST /events/{id}/retry`. Do not press the `r` key in the TUI; the retry must be triggered programmatically.
- Persist enough information to a log file so the verifier can locate and inspect the artifacts in Hookdeck.

## Implementation Hints
- Read `ZEALT_RUN_ID` from the environment and append it to any externally visible resource name (source, destination, connection) to keep parallel runs isolated.
- `hookdeck listen <port> <source-name> --path <path>` will create the source, the `CLI` destination, and the connection on first run. Use `--output quiet` or `--output compact` so the process runs cleanly in a headless container.
- The CLI process is long-lived; start it in the background and wait until the connection is established before publishing.
- The Publish API requires the `Authorization: Bearer $HOOKDECK_API_KEY` header and the `X-Hookdeck-Source-Name` header.
- According to the Hookdeck docs, `POST /events/{id}/retry` returns the Event object directly at the root of the response (no wrapper). Treat the JSON body as the event itself.
- Poll `GET /events/{id}` until `status` becomes `SUCCESSFUL` and `attempts == 2` before declaring success.

## Acceptance Criteria
- Project path: /home/user/project
- Ensure the real Hookdeck actions are executed and the log artifact exists.
- Log file: /home/user/project/output.log
- The log file MUST contain the following lines, each on its own line, with these exact prefixes:
  - `Source Name: <source_name>`
  - `Connection ID: <web_...>`
  - `Event ID: <evt_...>`
  - `Retry Response Event ID: <evt_...>`
  - `Final Status: SUCCESSFUL`
  - `Final Attempts: 2`
- The resource name suffix rule:
  - The Hookdeck source name MUST be `cli-replay-${ZEALT_RUN_ID}` (lowercased).
- Connection shape (verified via the Hookdeck REST API):
  - `source.type == "WEBHOOK"`
  - `destination.type == "CLI"`
  - `destination.config.cli_path == "/hooks"`
- Event shape (verified via the Hookdeck REST API):
  - Exactly one event is created for that source during this run.
  - `attempts == 2`
  - `status == "SUCCESSFUL"`
  - The retry response logged as `Retry Response Event ID:` MUST equal the `Event ID:` (i.e. the retry endpoint returns the Event object at the root, not wrapped under a `data` or `event` key).

