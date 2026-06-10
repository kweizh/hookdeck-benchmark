# Hookdeck Evaluation Dataset Research Report

Hookdeck is an Event Gateway designed to receive, process, and deliver webhooks and events. It acts as a reliable infrastructure layer between event producers (e.g., Stripe, Shopify) and consumers (e.g., your local server, production API).

## 1. Library Overview

*   **Description**: Hookdeck provides a unified platform for managing the entire lifecycle of a webhook: ingestion, queuing, filtering, transformation, and delivery. It ensures reliability with automatic retries, rate limiting, and full observability.
*   **Ecosystem Role**: It sits between third-party SaaS webhooks and your application, replacing the need for custom ingestion logic, manual retry systems, and tunneling tools like ngrok.
*   **Project Setup**:
    1.  **CLI Installation**: `npm install -g hookdeck-cli` or `brew install hookdeck/hookdeck/hookdeck`.
    2.  **Authentication**: `hookdeck login` (opens browser) or `hookdeck login --api-key <key>`.
    3.  **Initialization**: Typically involves creating a **Source** (where events come in) and a **Destination** (where events go), then linking them with a **Connection**.

## 2. Core Primitives & APIs

### Connections
A Connection links a Source to a Destination and can include Rules (Filters, Transformations, etc.).
*   **CLI Creation**:
    ```bash
    hookdeck gateway connection create \
      --name "stripe-to-local" \
      --source-name "stripe" --source-type STRIPE \
      --destination-name "local-api" --destination-type CLI --destination-cli-path "/webhooks/stripe"
    ```
*   **API Creation**: `POST https://api.hookdeck.com/2025-07-01/connections`
*   **Documentation**: [Connections](https://hookdeck.com/docs/connections.md)

### Mock API & Publish API
Hookdeck allows you to simulate destinations and manually trigger events.
*   **Mock Destination**: Set `--destination-type MOCK` to have Hookdeck accept events and return 200 OK without forwarding.
*   **Publish API (Outbound Mocking)**: Send events directly to a source via API.
    ```bash
    curl -X POST "https://hkdk.events/v1/publish" \
      -H "Authorization: Bearer $API_KEY" \
      -H "X-Hookdeck-Source-Name: my-source" \
      -H "Content-Type: application/json" \
      -d '{"event": "test.created", "data": {"id": 123}}'
    ```
*   **Querying Events (Inspect API)**:
    ```bash
    curl "https://api.hookdeck.com/2025-07-01/events?source_id=src_123&status=SUCCESSFUL" \
      -H "Authorization: Bearer $API_KEY"
    ```
*   **Documentation**: [Publish API](https://hookdeck.com/docs/api/publish.md), [Inspect API](https://hookdeck.com/docs/api/inspect.md)

### CLI Forwarding (Localhost Testing)
The CLI creates a secure tunnel to your local machine.
*   **Usage**:
    ```bash
    # Forward events from source 'shopify' to localhost:3000/webhooks
    hookdeck listen 3000 shopify --path /webhooks
    ```
*   **Interactive TUI**: The CLI provides a full-screen interface to inspect headers/payloads and replay events manually using the `r` key.
*   **Documentation**: [CLI Listen](https://hookdeck.com/docs/cli/listen.md)

### Transformations (JavaScript)
Modify payloads using JavaScript handlers.
*   **Example**:
    ```javascript
    addHandler("transform", (request, context) => {
      // Flatten nested structure
      if (request.body.data && request.body.data.object) {
        request.body = request.body.data.object;
      }
      request.headers["x-hookdeck-transformed"] = "true";
      return request;
    });
    ```
*   **Documentation**: [Transformations](https://hookdeck.com/docs/transformations.md)

## 3. Real-World Use Cases & Templates

*   **SaaS Integration**: Routing Stripe webhooks to a local Express server while filtering for only `charge.succeeded` events.
*   **Fan-out Pattern**: One Source (e.g., GitHub) sending events to multiple Destinations (e.g., Slack for notifications, AWS Lambda for processing).
*   **Legacy System Integration**: Using Transformations to convert modern JSON webhooks into XML for an older backend.
*   **Async API Gateway**: Decoupling a high-volume event producer from a slow consumer using Hookdeck's per-destination rate limiting.

## 4. Developer Friction Points

1.  **Transformation Sandbox Limits**: Transformations run in V8 isolates. They **cannot** perform network requests (no `fetch`), use `async/await`, or access the file system. Developers often try to fetch external data during transformation, which fails. [Discussion](https://hookdeck.com/docs/transformations#limitations).
2.  **HMAC Verification**: Setting up manual signature verification for providers not natively supported by "Source Types" can be tricky. It requires correctly configuring the `source.config` with the right algorithm and secret.
3.  **CLI Profile Management**: When working across multiple Hookdeck projects, managing CLI profiles (`--profile`) and ensuring the correct API key is used can lead to configuration errors.

## 5. Evaluation Ideas

*   **Simple**: Set up a Hookdeck Connection that forwards Stripe webhooks to a local port 3000 using the CLI.
*   **Intermediate**: Create a Connection with a Filter rule that only allows events where `body.type` is `order.created`.
*   **Intermediate**: Use the Publish API to programmatically trigger a mock event and then use the Inspect API to verify its delivery status.
*   **Complex**: Implement a JavaScript Transformation that renames keys in a JSON payload and adds a custom HMAC signature header based on an environment variable.
*   **Complex**: Configure a "Fan-out" architecture where a single Source routes to two Destinations: one Mock API and one local CLI destination, each with different rate limits.
*   **Edge Case**: Set up a Connection that retries on 5xx errors but ignores 4xx errors, using a custom retry strategy.

## 6. Sources

1.  [Hookdeck Documentation Index (llms.txt)](https://hookdeck.com/docs/llms.txt) - Lightweight map of all documentation.
2.  [Hookdeck Basics](https://hookdeck.com/docs/hookdeck-basics.md) - Core concepts and terminology.
3.  [CLI Connection Reference](https://hookdeck.com/docs/cli/connection.md) - Detailed commands for managing connections via CLI.
4.  [Transformations Guide](https://hookdeck.com/docs/transformations.md) - Syntax and limitations for JS-based transformations.
5.  [Publish API Reference](https://hookdeck.com/docs/api/publish.md) - Sending events to Hookdeck via API.
6.  [TypeScript SDK (JSR)](https://jsr.io/@hookdeck/sdk) - Official SDK documentation and usage patterns.
7.  [Hookdeck GitHub](https://github.com/hookdeck) - Source for CLI and SDK repositories.