# List Hookdeck Sources

## Background
Retrieve a list of all configured sources in the Hookdeck workspace.

## Requirements
- Fetch the list of sources from the Hookdeck API.
- Extract the names of all sources and save them to a file.

## Implementation Hints
- Use the `HOOKDECK_API_KEY` environment variable for authentication.

## Acceptance Criteria
- Project path: /home/user/myproject
- Ensure the script is executed and the artifacts exist.
- Log file: /home/user/myproject/sources.txt
- The file must contain exactly the names of all sources in the workspace, with each name on a separate line. Order does not matter. Extraneous whitespace or empty lines are ignored.

