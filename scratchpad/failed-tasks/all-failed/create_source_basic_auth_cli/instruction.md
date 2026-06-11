# Create a Hookdeck Source with Basic Auth

## Background
You need to configure a webhook ingestion pipeline using Hookdeck. The incoming webhooks require Basic Authentication to ensure only authorized producers can send events. You will create the necessary Hookdeck resources to receive these events and route them to a mock destination.

## Requirements
- Create a Hookdeck Source named `secure-source-${run-id}` of type `WEBHOOK`.
- The source MUST be configured with Basic Authentication (`BASIC_AUTH`). The username must be `admin` and the password must be `secret-password-${run-id}`.
- Create a Hookdeck Destination named `mock-dest-${run-id}` of type `MOCK_API`.
- Create a Hookdeck Connection named `secure-connection-${run-id}` that links the `secure-source-${run-id}` to the `mock-dest-${run-id}`.
- Write the created Source ID to a JSON file at `/home/user/hookdeck-project/source.json`.

## Implementation Hints
- You can use the Hookdeck CLI or the Hookdeck REST API to create and configure these resources.
- Use the `ZEALT_RUN_ID` environment variable to determine the `run-id`.
- If the CLI does not fully support configuring Basic Auth during source creation, you may need to use the Hookdeck API (e.g., `PUT /sources/:id` or `POST /sources`) with your API key.

## Acceptance Criteria
- Project path: /home/user/hookdeck-project
- Ensure the real resources (Source, Destination, Connection) are created in the Hookdeck workspace.
- The Source name must be exactly `secure-source-${run-id}`.
- The Source must have `auth_type` set to `BASIC_AUTH`, with username `admin` and password `secret-password-${run-id}`.
- The Destination name must be exactly `mock-dest-${run-id}`.
- The Destination type must be `MOCK_API`.
- The Connection name must be exactly `secure-connection-${run-id}`, linking the correct source and destination.
- Log file: /home/user/hookdeck-project/source.json
- The log file must contain valid JSON in the format: `{"source_id": "<source_id>"}`.

