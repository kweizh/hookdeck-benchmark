Processing unnecessary webhooks consumes backend resources and increases costs, requiring gateways to drop irrelevant events before delivery.

You need to write a JSON configuration payload for the Hookdeck API (`POST /connections`) to create a Connection with a Filter rule that strictly allows events to pass only if `body.type` is exactly `order.created` in a production environment.

**Constraints:**
- The output MUST be a valid JSON object representing the connection creation request body.
- Do NOT include `curl` commands or HTTP headers in the output; only provide the JSON payload.