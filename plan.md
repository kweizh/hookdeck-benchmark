# Hookdeck Evaluation Dataset Research Report

Hookdeck is an Event Gateway designed to receive, process, and deliver webhooks and events. It acts as a reliable infrastructure layer between event producers (e.g., Stripe, Shopify) and consumers (e.g., your local server, production API).

## 1. Library Overview

*   **Description**: Hookdeck provides a unified platform for managing the entire lifecycle of a webhook: ingestion, queuing, filtering, transformation, and delivery. It ensures reliability with automatic retries, rate limiting, and full observability.
*   **Ecosystem Role**: It sits between third-party SaaS webhooks and your application, replacing the need for custom ingestion logic, manual retry systems, and tunneling tools like ngrok.
*   **Project Setup**:
    1.  **CLI Installation**: `npm install -g hookdeck-cli` or `brew install hookdeck/hookdeck/hookdeck`.
    2.  **Authentication**: `hookdeck ci --api-key <key>`, or `hookdeck ci` directly while having `HOOKDECK_API_KEY` set in your environment.
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

### Models & Object Representations

Based on the REST API, here are the core object models represented by their JSON responses:

#### Connection Object
A connection links a source to a destination and contains rules for processing events.
```json
{
  "id": "web_nbbweTiOtzsm",
  "team_id": "tm_lbhzBKgFOUnB",
  "updated_at": "2026-01-14T13:36:41.582Z",
  "created_at": "2026-01-14T13:36:41.595Z",
  "paused_at": null,
  "name": "shopify-my-api",
  "rules": [],
  "description": null,
  "destination": { /* Destination Object */ },
  "source": { /* Source Object */ },
  "disabled_at": null,
  "full_name": "shopify -> shopify-my-api"
}
```

#### Source Object
A source represents the origin of the webhooks. It supports various types (e.g., `WEBHOOK`, `STRIPE`, `SHOPIFY`, `FIREBLOCKS`, `BRIDGE_XYZ`) and contains type-specific configurations.
*Note: For `FIREBLOCKS` sources, `config.auth.environment` is required and `public_key` is not used. The `BRIDGE` type was split into `BRIDGE_XYZ` and `BRIDGE_API`.*
```json
{
  "id": "src_qa5626p6y5o79b",
  "team_id": "tm_lbhzBKgFOUnB",
  "updated_at": "2026-01-14T13:36:41.583Z",
  "created_at": "2026-01-14T13:35:55.226Z",
  "name": "shopify",
  "description": null,
  "type": "WEBHOOK",
  "config": {
    "allowed_http_methods": [
      "POST",
      "PUT",
      "PATCH",
      "DELETE"
    ],
    "custom_response": null
  },
  "url": "http://localhost:8787/qa5626p6y5o79b",
  "disabled_at": null,
  "authenticated": false
}
```

#### Destination Object
A destination represents where Hookdeck forwards the webhooks. Types include `HTTP`, `CLI`, `MOCK_API`, etc.
```json
{
  "id": "des_TU9ioCk5EHUU",
  "team_id": "tm_lbhzBKgFOUnB",
  "updated_at": "2026-01-14T13:36:41.584Z",
  "created_at": "2026-01-14T13:35:55.263Z",
  "name": "my-api",
  "description": null,
  "type": "HTTP",
  "config": {
    "url": "https://mock.hookdeck.com/example",
    "rate_limit": null,
    "rate_limit_period": "second",
    "http_method": null,
    "path_forwarding_disabled": false,
    "auth": {},
    "auth_type": "HOOKDECK_SIGNATURE"
  },
  "disabled_at": null
}
```

#### Rules Object (Deduplicate Rule Example)
Rules like filters, transformations, delays, retries, and deduplication can be applied to connections. Transformations and filters are ordered via the `rules` array.
```json
{
  "type": "deduplicate",
  "window": 300,
  "include_fields": ["id", "type", "user_id"]
}
```

#### Error Object
Hookdeck uses standard HTTP response codes. Errors are returned in this format:
```json
{
  "handled": true,
  "status": 422,
  "message": "Connection does not exist or is disabled",
  "data": {
    "id": "web_xxxxxxxxxxx"
  }
}
```

#### Pagination Object
All `GET` endpoints that retrieve a list of resources are paged using cursor (keyset) pagination.
```json
{
  "pagination": {
    "order_by": "created_at",
    "dir": "desc",
    "limit": 100,
    "next": "web_2urj7h9puxk6obro3x",
    "prev": "web_2urj7h9puxk6obuf6i"
  }
}
```

#### Query Formatting
*   **Arrays**: Appended with `[]` (e.g., `?item[1]=hello&item[2]=world`).
*   **Operators**: Supported operators include `gte`, `gt`, `lte`, `lt`, `any`, and `contains` (e.g., `?number[gte]=1&number[lte]=10`).

### APIs

Hookdeck provides a robust REST API for managing resources programmatically.

*   **List Sources API (`GET /sources`)**:
    Retrieves a list of sources.
    ```json
    // Example Response
    {
      "pagination": {
        "order_by": "created_at",
        "dir": "desc",
        "limit": 100
      },
      "count": 1,
      "models": [
      {
        "id": "src_5b3mzbxk83dciim",
        "name": "my-api",
        "type": "WEBHOOK",
        "url": "https://hkdk.events/5b3mzbxk83dciim",
        "config": {
          "auth_type": "BASIC_AUTH",
          "auth": {
            "username": "user@hookdeck.com",
            "password": "my-password"
          },
          "custom_response": {
            "content_type": "json",
            "body": "{ \"prop\": \"value\"}"
          },
          "allowed_http_methods": [
            "POST",
            "PUT",
            "PATCH",
            "DELETE"
          ]
        },
        "team_id": "tm_5b3mzbxk83c0k7i",
        "disabled_at": null,
        "updated_at": "2025-01-26T17:15:31.079Z",
        "created_at": "2025-01-22T18:22:38.015Z"
      }
      ]
    }
    ```

*   **Retrieve Transformation API (`GET /transformations/:id`)**:
    Retrieves a specific transformation, including its JavaScript code.
    ```json
    // Example Response
    {
      "id": "trf_123",
      "name": "flatten-payload",
      "code": "addHandler('transform', (request, context) => {\n  if (request.body.data) {\n    request.body = request.body.data;\n  }\n  return request;\n});",
      "env": {
        "MY_SECRET": "secret_value"
      },
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-01T00:00:00.000Z"
    }
    ```

*   **Retrieve Request**:
    A request represent a webhook received by Hookdeck.

    ```bash
    curl -X GET \
      "https://api.hookdeck.com/2025-07-01/requests/<id>" \
      -H "Authorization: Bearer $API_KEY"
    ```

    Response

    ```json
    {
      "id": "req_fpSzYE7G0Op42UkKvFOB",
      "team_id": "tm_lbhzBKgFOUnB",
      "verified": false,
      "rejection_cause": null,
      "service_tier": "level1",
      "ingested_at": "2026-01-14T13:36:06.368Z",
      "source_id": "src_qa5626p6y5o79b",
      "original_event_data_id": "edt_zjQsVjdTqSMI0cNIPPXE",
      "ignored_count": 0,
      "events_count": 1,
      "cli_events_count": 0,
      "created_at": "2026-01-14T13:36:06.415515Z",
      "updated_at": "2026-01-14T13:36:06.415515Z",
      "data": {
        "body": {
          "headers": {
            "content-type": "application/json"
          },
          "body": {
            "type": "order.created",
            "customer": {
              "id": "cust_123",
              "email": "customer@example.com"
            },
            "total": 99.99,
            "timestamp": "2026-01-14T13:36:06.365Z"
          }
        },
        "headers": {
          "content-length": "192",
          "content-type": "application/json",
          "user-agent": "axios/1.11.0",
          "x-hookdeck-original-ip": "::1"
        },
        "parsed_query": {},
        "path": "",
        "query": "",
        "is_large_payload": false
      }
    }
    ```

Hookdeck allows you to simulate destinations and manually trigger events.
*   **Mock Destination**: Set destination-type to MOCK_API to have Hookdeck accept events and return 200 OK without forwarding.
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
    curl "https://api.hookdeck.com/2025-07-01/events/<id>" \
      -H "Authorization: Bearer $API_KEY"
    ```
    *Note: The `/events/:id/retry` endpoint returns only the Event object in the root of the response. The `/attempts` endpoint only returns attempts with status `SUCCESSFUL` or `FAILED`.*

    Response:

    ```
    {
      "webhook_id": "web_FMKlTwAoGFRu",
      "team_id": "tm_lbhzBKgFOUnB",
      "source_id": "src_qa5626p6y5o79b",
      "destination_id": "des_TU9ioCk5EHUU",
      "event_data_id": "edt_zjQsVjdTqSMI0cNIPPXE",
      "request_id": "req_fpSzYE7G0Op42UkKvFOB",
      "cli_id": null,
      "attempts": 2,
      "status": "SUCCESSFUL",
      "id": "evt_EKbUbpGzNMIdfqnXzA",
      "last_attempt_at": "2026-01-14T13:36:31.820Z",
      "next_attempt_at": null,
      "response_status": 200,
      "error_code": null,
      "successful_at": "2026-01-14T13:36:06.675Z",
      "created_at": "2026-01-14T13:36:06.415Z",
      "updated_at": "2026-01-14T13:36:32.172Z",
      "data": {
        "method": "POST",
        "url": "https://mock.hookdeck.com/e/example",
        "headers": {
          "Accept": "application/json, text/plain, */*",
          "Idempotency-Key": "evt_EKbUbpGzNMIdfqnXzA",
          "content-length": "192",
          "content-type": "application/json",
          "user-agent": "axios/1.11.0",
          "X-Hookdeck-Signature": "Mpto1l/p+tdzO/85huGU3lwbl7xPHr/m+13qA9PeKUQ=",
          "X-Hookdeck-EventID": "evt_EKbUbpGzNMIdfqnXzA",
          "X-Hookdeck-RequestID": "req_fpSzYE7G0Op42UkKvFOB",
          "X-Hookdeck-Original-IP": "::1",
          "X-Hookdeck-Verified": "false",
          "X-Hookdeck-Event-URL": "http://localhost:3000/events/evt_EKbUbpGzNMIdfqnXzA",
          "X-Hookdeck-Source-Name": "shopify",
          "X-Hookdeck-Connection-Name": "shopify-orders",
          "X-Hookdeck-Destination-Name": "my-api",
          "X-Hookdeck-Attempt-Count": "3",
          "X-Hookdeck-Attempt-Trigger": "MANUAL",
          "X-Hookdeck-Will-Retry-After": ""
        },
        "body": {
          "headers": {
            "content-type": "application/json"
          },
          "body": {
            "type": "order.created",
            "customer": {
              "id": "cust_123",
              "email": "customer@example.com"
            },
            "total": 99.99,
            "timestamp": "2026-01-14T13:36:06.365Z"
          }
        },
        "appended_headers": [
          "Accept",
          "Idempotency-Key",
          "X-Hookdeck-Signature",
          "X-Hookdeck-EventID",
          "X-Hookdeck-RequestID",
          "X-Hookdeck-Original-IP",
          "X-Hookdeck-Verified",
          "X-Hookdeck-Event-URL",
          "X-Hookdeck-Source-Name",
          "X-Hookdeck-Connection-Name",
          "X-Hookdeck-Destination-Name",
          "X-Hookdeck-Attempt-Count",
          "X-Hookdeck-Attempt-Trigger",
          "X-Hookdeck-Will-Retry-After"
        ],
        "path": "/e/example",
        "query": "",
        "parsed_query": {}
      }
    }
    ```

*   **Metrics API Endpoints**:
    Provides analytics and monitoring for webhook infrastructure.
    *   `GET /metrics/requests` - Request volume metrics
    *   `GET /metrics/events` - Event processing stats
    *   `GET /metrics/attempts` - Delivery attempt metrics
    *   `GET /metrics/events-by-issue` - Event failures grouped by issue type
    *   `GET /metrics/queue-depth` - Queue depth metrics
    *   `GET /metrics/transformations` - Transformation execution performance
    *   `GET /metrics/events-pending-timeseries` - Time-series data for pending events

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
4.  **Evaluation Limits**: The tasks would be implemented and evaluated in a container environment without public inbound network access, so all the tasks should be done using the CLI and Mock API Destination (A Mock API endpoint that accepts all API requests sent to it, https://mock.hookdeck.com) in Hookdeck.
5.  **Login**: since we were in headless env, should use `hookdeck ci --api-key TOKEN` to login before start the evaluation.

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