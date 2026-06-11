# Setup Manual Signature Verification in Source Config

## Background
Configure a Hookdeck Source to perform manual HMAC signature verification. This ensures that incoming webhooks are authentic and have not been tampered with.

## Requirements
- Create a new Hookdeck Source named `secure-source-${run-id}`.
- Configure the source to use HMAC signature verification.
- The HMAC algorithm must be `SHA256`.
- The encoding must be `base64`.
- The signature must be expected in the `x-custom-signature` header.
- The secret key must be `my_super_secret_key`.
- Save the resulting Source ID to a log file.

## Implementation Hints
- Read the `run-id` from the `ZEALT_RUN_ID` environment variable.
- You can use the Hookdeck API (`POST https://api.hookdeck.com/2025-07-01/sources`) to create the source with the required `verification` configuration.
- Write the Source ID to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real source creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The source name must be `secure-source-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The source must have HMAC signature verification configured with `SHA256`, `base64`, header `x-custom-signature`, and secret `my_super_secret_key`.
- The log file must contain the Source ID in the format: `Source ID: <source_id>`.

