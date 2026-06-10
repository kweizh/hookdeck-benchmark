Testing third-party webhooks locally requires establishing a secure tunnel and routing configuration without relying on tools like ngrok.

You need to write the exact `hookdeck gateway connection create` CLI command to create a connection named "stripe-to-local" from a STRIPE source named "stripe" to a CLI destination named "local-api" with the path `/webhooks/stripe` in a local development environment.

**Constraints:**
- Do NOT use interactive mode prompts; all configuration must be passed directly as command-line flags.
- Ensure the `source-type` and `destination-type` arguments strictly match Hookdeck's CLI specifications.