# Validate-and-Drop Transformation with Structured Logging

## Background
Build a Hookdeck pipeline whose transformation enforces a payload contract: events that do not match the contract must be dropped (no Event created, nothing delivered) AND must leave a structured log entry on the transformation execution so an operator can later identify which field was offending.

## Requirements
- Create a Hookdeck Source named `src-${run-id}` of type `WEBHOOK`.
- Create a Hookdeck Destination named `dst-${run-id}` of type `MOCK_API`.
- Create a Hookdeck Connection named `conn-${run-id}` linking that Source to that Destination.
- Create a Hookdeck Transformation named `validate-${run-id}` and attach it as a transformation rule on the Connection.
- The transformation must enforce the following payload contract on `request.body`:
  - `user_id` MUST be a non-empty string.
  - `amount` MUST be a number (`typeof === "number"` and finite).
- If the payload is valid, the transformation must return the request unchanged.
- If the payload is invalid, the transformation must:
  - Emit a structured log entry on the transformation execution via `console.log` that includes the literal token `validation_failed` and the name of the FIRST offending field (`user_id` or `amount`).
  - Drop the event so that no Event is created and nothing is forwarded to the Destination.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- You may use the Hookdeck CLI or the Hookdeck REST API to provision the Source, Destination, Connection, and Transformation.
- In Hookdeck transformations, returning `null` from the `transform` handler causes Hookdeck to log the execution and skip event creation (the request is ignored). Any lines written with `console.log` during execution are persisted on the transformation execution record and can be retrieved via the transformation executions endpoint of the Hookdeck API.
- The transformation runtime is a V8 isolate without network/IO/async support; keep the code synchronous.
- After creating the resources, write the resulting Source ID and Transformation ID to the log file so they can be used for verification.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the real Hookdeck resources are created and the artifacts exist.
- Log file: `/home/user/hookdeck-task/output.log`
- The log file must contain two lines in these exact formats:
  - `Source ID: <source_id>`
  - `Transformation ID: <transformation_id>`
- A Source, Destination, Connection, and Transformation with the `${run-id}` suffix must exist in the Hookdeck workspace.
- Valid events (containing a non-empty string `user_id` and a numeric `amount`) must be delivered unchanged to the Mock API Destination.
- Invalid events (missing/wrong-typed `user_id` or `amount`) must NOT produce a delivered event, and the corresponding transformation execution must contain a `console.log` line whose message contains the token `validation_failed` and the name of the offending field.

