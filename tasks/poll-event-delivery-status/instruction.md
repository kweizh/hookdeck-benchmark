# Await Hookdeck Event Delivery

## Background
Hookdeck delivers webhook events asynchronously. After a webhook is ingested, the delivery to the destination may go through several attempts before reaching a terminal state. Build a small command-line utility that polls the Hookdeck Inspect API and waits for an event to reach a terminal state.

## Requirements
- Provide an executable script at `/workspace/await_delivery.py`.
- The script reads a single event id from the `EVENT_ID` environment variable.
- The script polls Hookdeck for that event's current state using the Inspect API and exits according to the outcome.
- Use exponential backoff between polls. The script must give up after at most 30 seconds of total wait time.

## Implementation Hints
- Authenticate to the Inspect API with the `HOOKDECK_API_KEY` environment variable.
- The Inspect API exposes an event resource that includes a `status` field. Some status values are terminal; others indicate the event is still in flight.
- Treat any non-terminal status as a signal to wait and poll again.
- Print the final outcome to stdout so a caller can capture it. Use stable key=value pairs separated by newlines.

## Acceptance Criteria
- Project path: /workspace
- Command: `python3 /workspace/await_delivery.py`
- Input: The script reads the event id from the `EVENT_ID` environment variable. No CLI arguments.
- Behaviour:
  - When the event ultimately reaches the SUCCESSFUL terminal state, the script exits with code `0`.
  - When the event ultimately reaches the FAILED terminal state, the script exits with a non-zero code.
  - When the cumulative wait exceeds 30 seconds without reaching a terminal state, the script exits with a non-zero code.
- Output: On exit, stdout must contain two lines of the form:
  - `attempt_count=<int>` — the number of polling iterations the script performed against the Inspect API.
  - `response_status=<int_or_none>` — the latest HTTP response status recorded for the event by Hookdeck (use `none` when Hookdeck has not yet reported one).
- The script must use exponential backoff between polls (each wait at least doubles the previous one, starting from a sub-second value) and must respect the 30s overall budget.

