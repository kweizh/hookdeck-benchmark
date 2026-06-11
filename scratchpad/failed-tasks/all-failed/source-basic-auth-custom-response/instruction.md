# Secure Hookdeck Source with Basic Auth and Custom JSON Response

## Background
You are protecting a public webhook endpoint with Hookdeck. The endpoint must reject anonymous traffic, accept only requests authenticated with HTTP Basic Auth, and answer authorized callers with a tailored JSON payload that downstream callers depend on. Events received from authorized callers must be queued for delivery to a Mock API destination.

## Requirements
- Create a Hookdeck Source of type `WEBHOOK`.
- Configure the source so that incoming requests must authenticate with HTTP Basic Auth using username `eval-user` and password `eval-pass`.
- Configure a custom response on the source: the response `content_type` must be `json` and the response body must equal `{"ok": true, "id": "abc"}`.
- Create a Mock API destination and link it to the source via a connection so authorized events are routed to the mock.
- Persist the created source identifier and source URL to `/home/user/hookdeck-project/source.json` so the verifier can probe the live endpoint.

## Implementation Hints
- The Hookdeck CLI may not expose every source configuration field; the REST API at `https://api.hookdeck.com/2025-07-01/sources` is authoritative for `config.auth_type`, `config.auth`, and `config.custom_response`.
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable and append it to every resource name to keep concurrent runs isolated.
- The Hookdeck source `url` field returned from the API is the public ingest URL clients must call.
- The Hookdeck API key is provided in the `HOOKDECK_API_KEY` environment variable.

## Acceptance Criteria
- Project path: /home/user/hookdeck-project
- Ensure the real Hookdeck resources (source, destination, connection) are created in the workspace.
- All resource names must be suffixed with the value of `ZEALT_RUN_ID` (referred to as `${run-id}`).
- The source `config.auth_type` must be exactly `BASIC_AUTH` with the specified username and password.
- The source `config.custom_response.content_type` must be `json` and `config.custom_response.body` must encode the exact JSON object `{"ok": true, "id": "abc"}`.
- The destination must be of type `MOCK_API` (or a Hookdeck destination whose behavior is functionally a mock API).
- A connection must link the source to the mock destination.
- Log file: /home/user/hookdeck-project/source.json
- The log file must contain valid JSON with at least the fields `source_id` and `source_url` populated from the created source.
- The live source URL must respond with HTTP 200 and the configured custom JSON body when called with the correct Basic Auth credentials, and must reject calls with wrong credentials.

