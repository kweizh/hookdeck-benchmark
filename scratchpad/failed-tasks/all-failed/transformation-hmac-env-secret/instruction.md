# Sign Hookdeck-Delivered Events with HMAC-SHA256 via a Transformation

## Background
You are operating against a real Hookdeck project (Event Gateway). Configure a pipeline that receives JSON webhooks on a Hookdeck source, runs them through a Transformation that signs every request with a secret stored **in the transformation environment**, and delivers them to a Hookdeck Mock destination. The Hookdeck CLI (`hookdeck`) and the REST API (Bearer token in `HOOKDECK_API_KEY`) are available; the project is headless so you must use `hookdeck ci --api-key $HOOKDECK_API_KEY` if you rely on CLI commands that need login.

## Requirements
- Create a Hookdeck source of type `WEBHOOK`.
- Create a Hookdeck destination that points at the Hookdeck Mock API (`https://mock.hookdeck.com/<any-path>`); a destination of type `MOCK_API` is also acceptable.
- Create a Transformation whose **environment variables** contain `MY_SECRET`. The secret value lives only inside the transformation env – the connection, source, and destination must not contain the secret.
- Create a Connection that wires the source to the destination and applies the transformation as a rule.

## Signature contract
The transformation MUST attach the following two headers to every outgoing request:

- `x-hd-signature`: lowercase hexadecimal HMAC-SHA256 digest computed as `HMAC_SHA256(key = process.env.MY_SECRET, message = JSON.stringify(request.body))`. The `request.body` is the parsed JSON object the transformation receives; the message is its standard `JSON.stringify` serialization (no extra spaces, keys in received order).
- `x-hd-signed-at`: an ISO-8601 timestamp produced at signing time (e.g. `new Date().toISOString()`). The verifier checks the value is within the last 60 seconds of when the event is inspected.

The transformation must continue to forward the original body unchanged.

## Implementation Hints
- Read `ZEALT_RUN_ID` from the environment and append it as a suffix to every Hookdeck resource you create (see Acceptance Criteria for exact names) so that concurrent runs do not collide.
- The transformation runtime is a V8 isolate: no `fetch`, no `async/await`, no `crypto` module, no Node built-ins. You will need a pure-JavaScript HMAC-SHA256 implementation embedded in the transformation `code`.
- Transformation env vars are sent through the Hookdeck REST API on the transformation object (`env` field, key/value pairs) – they are not the same thing as connection-level secrets.
- Use the Hookdeck Publish API or any other supported mechanism if you want to send a smoke-test event during development.
- Persist the IDs of the resources you create to the log file so the verifier can find them.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the real Hookdeck resources are created on the target Hookdeck account, and the log artifact exists.
- Log file: `/home/user/myproject/output.log` and it must contain the following lines, each on its own line:
  - `Source Name: hmac-src-${ZEALT_RUN_ID}`
  - `Destination Name: hmac-dst-${ZEALT_RUN_ID}`
  - `Connection ID: <connection_id>`
  - `Transformation ID: <transformation_id>`
- Resource naming (each name uses the literal value of `ZEALT_RUN_ID`):
  - Source name: `hmac-src-${ZEALT_RUN_ID}`, type `WEBHOOK`.
  - Destination name: `hmac-dst-${ZEALT_RUN_ID}` (either `MOCK_API` or `HTTP` with a `https://mock.hookdeck.com/...` URL).
  - Transformation name: `hmac-trf-${ZEALT_RUN_ID}`.
  - Connection name: `hmac-conn-${ZEALT_RUN_ID}`, wired source → destination, with the transformation applied via `rules`.
- Transformation environment must contain exactly the key `MY_SECRET` with value `s3cr3t-${ZEALT_RUN_ID}`.
- For any JSON event published to the source, the corresponding delivered event (as returned by the Inspect API) must contain:
  - Header `x-hd-signature` equal to the lowercase hex HMAC-SHA256 of `JSON.stringify(<delivered body>)` keyed by `s3cr3t-${ZEALT_RUN_ID}`.
  - Header `x-hd-signed-at` parseable as ISO-8601 and within 60 seconds of the time it is read.

