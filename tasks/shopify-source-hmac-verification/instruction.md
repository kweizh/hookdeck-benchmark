# Hookdeck Source Signature Verification (Shopify HMAC)

## Background
Hookdeck can verify incoming webhooks at the Source level. When a Source is configured with the `SHOPIFY` verification integration, Hookdeck computes a base64-encoded HMAC SHA-256 of the **raw request body** using the configured `webhook_secret_key` and compares it against the `X-Shopify-Hmac-Sha256` header (case-insensitive). Each ingested request is then exposed via the Inspect API with a `verified` flag and, when applicable, a `rejection_cause`.

Your task is to create a `SHOPIFY` Source with HMAC verification enabled, then exercise the verification by sending two HTTP requests to its public URL: one signed correctly with the secret, and one that is NOT signed correctly. Hookdeck must record the first request as `verified: true` and the second as `verified: false` with `rejection_cause` set to `VERIFICATION_FAILED`.

## Requirements
- Read `run-id` from the `ZEALT_RUN_ID` environment variable.
- Read the Hookdeck API key from `HOOKDECK_API_KEY`.
- Read the webhook secret from the `SHOPIFY_WEBHOOK_SECRET` environment variable. Use this exact value as the source's webhook secret.
- Create a Hookdeck Source named `shopify-verify-${run-id}` of type `SHOPIFY` with Shopify HMAC verification enabled using `SHOPIFY_WEBHOOK_SECRET`.
- Capture the Source's public ingestion URL from the API response.
- Send **two** HTTP `POST` requests to the Source URL with identical JSON bodies (`Content-Type: application/json`):
  1. **Correctly signed**: include an `X-Shopify-Hmac-Sha256` header whose value is the base64-encoded HMAC SHA-256 of the **raw request body** using the secret.
  2. **Tampered/unsigned**: send the same body but with either no `X-Shopify-Hmac-Sha256` header or one containing an obviously wrong value.
- Write the resulting Source ID to a log file so the verifier can locate the requests.

## Implementation Hints
- The Shopify-style HMAC contract Hookdeck expects: `base64(HMAC_SHA256(secret, raw_request_body))` placed in the `X-Shopify-Hmac-Sha256` header.
- Always check the official Hookdeck REST API documentation for the exact Source `verification` schema (`https://hookdeck.com/docs/api`) and the Inspect API endpoints.
- The hookdeck CLI is pre-installed; you may use either the REST API directly or the CLI for source creation, but the verification configuration must be set programmatically.
- Login the CLI with `hookdeck ci --api-key "$HOOKDECK_API_KEY"` if you choose the CLI path, since the environment is headless.
- The signature MUST be computed over the exact byte sequence of the HTTP body you actually send; canonicalize JSON before hashing.
- Allow a few seconds between sending the requests and verification so Hookdeck has time to ingest them.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The log file must contain a line in the format: `Source ID: <source_id>` where `<source_id>` is the ID returned by Hookdeck.
- A Source named `shopify-verify-${run-id}` of type `SHOPIFY` must exist in the Hookdeck project, with Shopify signature verification configured.
- The Inspect API (`GET https://api.hookdeck.com/2025-07-01/requests?source_id=<source_id>`) must return at least two requests for this Source.
- Exactly one of the requests must have `verified` equal to `true`.
- At least one other request must have `verified` equal to `false` AND `rejection_cause` equal to `VERIFICATION_FAILED`.

