# Create a Destination with a Rate Limit

## Background
Hookdeck allows configuring a maximum delivery rate for destinations to control throughput and prevent overloading target servers.

## Requirements
- Create a new Hookdeck Destination using the Hookdeck API.
- The destination name must be `rate-limited-dest-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The destination must be of type `HTTP`.
- The destination URL must be `https://mock.hookdeck.com/rate-limited`.
- The destination must have a rate limit of 10 events per second.
- Save the created destination ID to a log file.

## Implementation Hints
- Use the Hookdeck REST API to create the destination.
- Retrieve the API key from the `HOOKDECK_API_KEY` environment variable.

## Acceptance Criteria
- Project path: /home/user/hookdeck-task
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/hookdeck-task/output.log
- The destination must be created in Hookdeck with the name `rate-limited-dest-${run-id}`.
- The destination's `config.url` must be exactly `https://mock.hookdeck.com/rate-limited`.
- The destination's `config.rate_limit` must be exactly `10`.
- The destination's `config.rate_limit_period` must be exactly `second`.
- The log file must contain the destination ID in the format: `Destination ID: <destination_id>`.

