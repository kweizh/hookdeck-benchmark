Automating the validation of a webhook ingestion pipeline requires programmatic event generation and subsequent delivery status verification.

You need to write a bash script containing two `curl` commands to first trigger an outbound mock event using the Publish API (`https://hkdk.events/v1/publish`) with the payload `{"event": "test.created", "data": {"id": 123}}`, and then query the Inspect API (`/events`) to retrieve events for `source_id=src_123` with a `SUCCESSFUL` status in an automated CI environment.

**Constraints:**
- Both commands MUST use the `$API_KEY` environment variable for Bearer token Authorization headers.
- The Publish API request MUST include the `X-Hookdeck-Source-Name: my-source` header and set the content type to JSON.