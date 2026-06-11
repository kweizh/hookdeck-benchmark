# Hookdeck HMAC Signature Transformation

## Background
Hookdeck allows you to write JavaScript transformations to modify event payloads and headers before they are delivered to a destination. In this task, you will create a connection that computes an HMAC signature of the payload and adds it as a header.

## Requirements
- Create a Hookdeck connection named `hmac-connection-${run-id}`.
- The connection must link a new source named `hmac-source-${run-id}` to a new MOCK destination named `hmac-dest-${run-id}`.
- Attach a transformation to this connection. The transformation must:
  1. Read a secret key from the environment variable `HMAC_SECRET`.
  2. Compute the HMAC SHA-256 signature of the stringified request body.
  3. Add the computed signature to the `x-hmac-signature` header of the request.
- You must write and execute a script (e.g., `setup.sh` or `setup.js`) to provision these resources on Hookdeck.
- You are operating in a headless environment.

## Implementation Hints
- Use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate the CLI in a headless environment, or use the Hookdeck REST API directly.
- Hookdeck transformations run in a V8 isolate and have access to built-in crypto modules. You can use standard Node.js `crypto` functions like `crypto.createHmac('sha256', env.HMAC_SECRET).update(JSON.stringify(request.body)).digest('hex')`.
- Ensure you read the `run-id` from the `ZEALT_RUN_ID` environment variable to name your resources correctly and avoid conflicts.
- Remember to configure the transformation environment variable `HMAC_SECRET` on Hookdeck so the transformation script can access it.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the setup script is executed and the Hookdeck resources are created.
- Log file: /home/user/hookdeck-task/output.log
- In the log file, output the created Source ID in the format: `Source ID: <source_id>`.
- In the log file, output the created Connection ID in the format: `Connection ID: <connection_id>`.
- The connection must be correctly configured to route events from `hmac-source-${run-id}` to `hmac-dest-${run-id}` (a Mock API destination).
- The transformation must correctly compute the HMAC SHA-256 signature and attach it as the `x-hmac-signature` header on the outgoing request.

