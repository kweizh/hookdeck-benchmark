High-volume event producers (e.g., GitHub) often need to broadcast single events to multiple downstream consumers (e.g., Slack and AWS Lambda) with varying capacity limits.

You need to write a JSON payload configuration that establishes a Fan-out architecture where a single Source routes to two distinct Destinations (one `MOCK` type and one `CLI` type), defining a strict rate limit for the CLI destination in a Hookdeck project environment.

**Constraints:**
- Both defined connections MUST be linked to the exact same Source definition.
- Provide only the JSON configuration representing the connections and the specific rate limit definitions.