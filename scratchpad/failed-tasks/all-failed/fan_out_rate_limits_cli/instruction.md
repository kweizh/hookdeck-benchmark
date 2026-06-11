# Configure Fan-out with Rate Limits via Hookdeck CLI

## Background
Hookdeck can route a single source to multiple destinations (a fan-out architecture). This is useful when you want to send the same event to different services, but each service might have different throughput capacities.

## Requirements
- Create a bash script `setup_fan_out.sh` that uses the Hookdeck CLI to create a fan-out architecture.
- The architecture must use a single Source named `fan-out-source-${run-id}`.
- The Source must be routed to two different Mock API Destinations:
  1. `mock-dest-1-${run-id}` with a rate limit of 10 events per second.
  2. `mock-dest-2-${run-id}` with a rate limit of 50 events per second.
- Both destinations should use the `MOCK` destination type.
- You must create two Connections to link the single Source to the two Destinations.
- After creating the resources, the script must output the Source URL to a log file.

## Implementation Hints
1. Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
2. Use the `hookdeck gateway connection create` or `upsert` commands to create the connections with inline sources and destinations.
3. Make sure to use the exact same source for both connections so it fans out from one URL.
4. Use the `--destination-rate-limit` and `--destination-rate-limit-period` flags to set the required limits.
5. Write the resulting Source URL to `/home/user/hookdeck-task/output.log`.

## Acceptance Criteria
- Project path: `/home/user/hookdeck-task`
- Ensure the bash script `setup_fan_out.sh` is executed and the Hookdeck infrastructure is created.
- Log file: `/home/user/hookdeck-task/output.log`
- The script must create a Source named `fan-out-source-${run-id}` where `run-id` is read from `ZEALT_RUN_ID`.
- The script must create two Mock Destinations named `mock-dest-1-${run-id}` and `mock-dest-2-${run-id}`.
- The connection to `mock-dest-1-${run-id}` must have a rate limit of 10 requests per second.
- The connection to `mock-dest-2-${run-id}` must have a rate limit of 50 requests per second.
- The log file must contain the Source URL in the format: `Source URL: <url>`.

