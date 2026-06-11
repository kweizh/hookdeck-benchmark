# Bulk-Retry Failed Events on a Hookdeck Connection

## Background
Hookdeck stores every webhook event it processes and supports replaying failed deliveries via single-event retries or bulk-retry operations. In this task a connection has already been seeded with several events that failed delivery because the destination was unhealthy. The destination has since been repaired. Your job is to recover the events by bulk-retrying every FAILED event on that connection until all of them transition to SUCCESSFUL.

## Requirements
- Use the Hookdeck REST API to find every event with `status=FAILED` on the seeded connection.
- Trigger a bulk retry that covers all of those FAILED events.
- Wait until every previously-FAILED event on the seeded connection has reached `status=SUCCESSFUL`.
- Write the seeded Connection ID to a log file when you are done.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable and use it to discover the seeded connection (its name follows the `bulk-conn-${run-id}` pattern).
- The API key is available in the `HOOKDECK_API_KEY` environment variable. Authenticate with `Authorization: Bearer $HOOKDECK_API_KEY`.
- Read the official API docs at https://hookdeck.com/docs/api and https://hookdeck.com/docs/api/inspect.md to find the exact list-events endpoint, the bulk-retry endpoint, and the supported query filters.
- After triggering the bulk retry the operation is asynchronous; you will need to poll the Events API until every previously-FAILED event has converged to `SUCCESSFUL`.
- The bulk-retry endpoint accepts a `query` object that should restrict the operation to the seeded connection only — do not retry events from other connections.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real bulk-retry action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- The seeded connection name follows the pattern `bulk-conn-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The log file must contain the seeded Connection ID in the format: `Connection ID: <connection_id>`.
- After the task finishes, the Hookdeck Events API must report 0 events with `status=FAILED` on the seeded connection.
- After the task finishes, the seeded connection must have at least one event whose final `status` is `SUCCESSFUL` and whose `attempts` count is `>= 2` (i.e., the event was redelivered at least once on top of its original failed attempt).
- After the task finishes, the latest delivery attempt for every previously-FAILED event must have a `trigger` value of `BULK_RETRY` or `MANUAL` (i.e., it was triggered by the bulk-retry operation rather than the initial delivery).

