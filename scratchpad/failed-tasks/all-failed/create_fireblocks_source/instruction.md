# Create a Fireblocks Source

## Background
You need to create a new source in Hookdeck to receive events from Fireblocks.

## Requirements
- Create a Hookdeck Source of type `FIREBLOCKS`.
- The source name must be `fireblocks-source-${run-id}`.
- The source must be configured with `config.auth.environment` set to `sandbox`.
- Save the created Source ID to a log file.

## Implementation Hints
- Read the current `run-id` from the `ZEALT_RUN_ID` environment variable.
- Ensure you check the Hookdeck API documentation to understand how to create a Source, especially the required payload structure for a FIREBLOCKS source.

## Acceptance Criteria
- Project path: /home/user/project
- Ensure the real source creation action is executed and the log artifact exists.
- Log file: /home/user/project/source.log
- The Hookdeck Source name must be exactly `fireblocks-source-${run-id}` where `run-id` is read from the `ZEALT_RUN_ID` environment variable.
- The Hookdeck Source type must be `FIREBLOCKS` and its `config.auth.environment` must be `sandbox`.
- The log file must contain the Source ID in the format: `Source ID: <source_id>`.
