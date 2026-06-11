# Forward Stripe Webhooks to Mock Destination

## Background
Hookdeck acts as an Event Gateway to receive, process, and deliver webhooks. In this task, you will configure a Connection to receive webhooks from Stripe and forward them to a Mock API destination using the Hookdeck CLI.

## Requirements
- Create a bash script `setup.sh` that authenticates with Hookdeck in a headless environment.
- The script must create a new Hookdeck Connection with a Source named `stripe-${run-id}` (type `STRIPE`) and a Destination named `mock-dest-${run-id}` (type `MOCK`).
- The connection itself must be named `stripe-to-mock-${run-id}`.
- Save the resulting connection creation output to a log file.

## Implementation Hints
- The evaluation environment is headless. Use `hookdeck ci --api-key $HOOKDECK_API_KEY` to authenticate.
- Use the `ZEALT_RUN_ID` environment variable to append the `run-id` to your resource names to avoid collisions.
- Use the `hookdeck gateway connection create` command to create the connection with a Mock destination.
- Write the output of the creation command to the required log file.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the real connection creation action is executed and the log artifact exists.
- Log file: /home/user/hookdeck-task/output.log
- Required Test Criteria:
  1. A Connection named `stripe-to-mock-${run-id}` must exist in Hookdeck.
  2. The Connection's Source must be named `stripe-${run-id}` and have the type `STRIPE`.
  3. The Connection's Destination must be named `mock-dest-${run-id}` and have the type `MOCK`.
  4. The `/home/user/hookdeck-task/output.log` file must exist.

