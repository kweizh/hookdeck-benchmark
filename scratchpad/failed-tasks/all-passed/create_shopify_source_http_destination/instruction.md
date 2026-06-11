# Create Hookdeck Connection

## Background
Set up a Hookdeck connection that receives events from a Shopify source and forwards them to an HTTP destination.

## Requirements
- Create a Hookdeck source of type `SHOPIFY` named `shopify-source-${run-id}`.
- Create a Hookdeck destination of type `HTTP` named `http-destination-${run-id}` pointing to `https://mock.hookdeck.com/${run-id}`.
- Create a connection linking this source and destination, named `shopify-to-http-${run-id}`.
- Write the resulting Connection ID to a log file.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck REST API or CLI to create the necessary resources.
- Write the Connection ID to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain the Connection ID in the format: `Connection ID: <connection_id>`.
- A source named `shopify-source-${run-id}` with type `SHOPIFY` must exist.
- A destination named `http-destination-${run-id}` with type `HTTP` and URL `https://mock.hookdeck.com/${run-id}` must exist.
- A connection named `shopify-to-http-${run-id}` must exist, linking the above source and destination.
