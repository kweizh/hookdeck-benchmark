# Hookdeck Source Custom XML Response

## Background
Some webhook providers (e.g., legacy SOAP/XML callers) inspect the synchronous HTTP response returned by the receiver and refuse to consider an event acknowledged unless the response body is a specific XML document with a matching content-type header. Hookdeck supports this through the source `custom_response` configuration. Configure a Hookdeck Source that returns a fixed XML acknowledgement to every caller while still forwarding the underlying event to a downstream destination.

## Requirements
- Read the value of `run-id` from the `ZEALT_RUN_ID` environment variable and use it as the suffix for every resource you create.
- Create a Hookdeck Source named `custom-xml-source-${run-id}`. Configure its `custom_response` so that synchronous callers receive the XML body `<ack><status>received</status></ack>` with an XML content-type response header.
- Create a Hookdeck Destination named `mock-dest-${run-id}` of type `MOCK_API` so events can be delivered without an external endpoint.
- Link the Source and Destination with a Connection named `custom-xml-conn-${run-id}`. The connection MUST NOT drop or filter events — every request posted to the source URL must produce one event that is queued and delivered to the mock destination.
- Record the resulting Source URL and Connection ID in the log file `/home/user/hookdeck-task/output.log`.

## Implementation Hints
- The Hookdeck CLI is already installed and `HOOKDECK_API_KEY` is exported. You can authenticate non-interactively if needed.
- Use the Hookdeck REST API (`https://api.hookdeck.com/2025-07-01`) or the CLI to provision the resources.
- The `custom_response` field lives inside the source `config` object and accepts an enum-valued `content_type`. Consult the Hookdeck Sources documentation if you are unsure which enum value selects XML.
- The Source response body must match the required XML verbatim. Do not add or strip whitespace, newlines, or XML declarations.
- A `MOCK_API` destination automatically returns 200 OK to Hookdeck, so no destination URL is needed.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real Hookdeck resources are created and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file MUST contain a line in the format `Source URL: <source_url>` where `<source_url>` is the full URL of the created Hookdeck source.
- The log file MUST contain a line in the format `Connection ID: <connection_id>` where `<connection_id>` is the ID of the created connection (matching `web_[A-Za-z0-9]+`).
- All created Hookdeck resources MUST use the suffix `${run-id}` taken from the `ZEALT_RUN_ID` environment variable.
- A `POST` request to the recorded Source URL with a small JSON payload must return HTTP 200, a response `Content-Type` header that indicates XML (i.e. contains the substring `xml`), and a response body that is exactly `<ack><status>received</status></ack>`.
- The same `POST` request must additionally produce a successfully delivered Hookdeck event on the recorded Connection (visible via the Inspect API as an event with `status` `SUCCESSFUL`).

