# Hookdeck Metrics API Aggregation Report

## Background
Hookdeck exposes a Metrics REST API that returns aggregated counters and gauges for ingested requests, processed events, executed transformations, and per-destination queue depth. Operators routinely build reports that pull from several of these endpoints at once. Your job is to produce one such report.

You are authenticated against Hookdeck via the `HOOKDECK_API_KEY` environment variable (base URL: `https://api.hookdeck.com/2025-07-01`). Some traffic has already been seeded against a dedicated source, connection, and destination that were created for this run; their IDs are recorded in `/workspace/resource_ids.json` as `{"source_id": ..., "destination_id": ..., "connection_id": ...}`. Only metrics scoped to those IDs are relevant to the report.

## Requirements
Produce a single artifact `/workspace/report.json` aggregating four pieces of data from the Hookdeck Metrics API, all scoped to the previous hour (`[now - 3600s, now]`):

- `requests_last_hour` (integer): total count of inbound requests received against the seeded source.
- `events_by_issue` (object): mapping of `issue_id` → event count for events tied to issues on the seeded connection. May be an empty object if no issues exist.
- `transformation_error_rate` (number): the `error_rate` measure for transformations executed on the seeded connection.
- `queue_depth` (integer): the `max_depth` measure reported for the seeded destination.

## Implementation Hints
- The Metrics API lives under the dated path prefix `https://api.hookdeck.com/2025-07-01/metrics/...`. Authenticate with `Authorization: Bearer $HOOKDECK_API_KEY`.
- The query string uses bracketed parameter encoding: `date_range[start]=<ISO8601>&date_range[end]=<ISO8601>`, `measures[]=<name>`, `dimensions[]=<name>`, and `filters[<name>]=<id>`. Use ISO 8601 UTC timestamps (e.g. `2026-01-14T13:36:06Z`).
- Choose the correct subroute for each data point: `/metrics/requests`, `/metrics/events-by-issue`, `/metrics/transformations`, `/metrics/queue-depth`. Each one returns `{"data": [{"time_bucket": ..., "dimensions": {...}, "metrics": {...}}, ...], "metadata": {...}}`.
- Sum or aggregate across the returned `data` rows as appropriate. For `events_by_issue`, group rows by their `dimensions.issue_id` and use the `count` measure as the value. Coerce integer-valued counts to `int` and rates to `number` before writing the report.
- Scope queries to the seeded resources: `filters[source_id]` for requests, `filters[connection_id]` for events-by-issue and transformations, `filters[destination_id]` for queue-depth.
- The CLI ships an equivalent `hookdeck gateway metrics ...` family, but the HTTP API is generally simpler for assembling a single JSON artifact.

## Acceptance Criteria
- Project path: `/home/user/myproject`
- Ensure the report-generation script is actually executed and that the artifacts described below exist.
- Artifact path: `/workspace/report.json`
- The report file MUST contain exactly these top-level keys with the documented types:
  - `requests_last_hour`: integer
  - `events_by_issue`: object whose keys are Hookdeck issue IDs (strings) and whose values are integer event counts (object MAY be empty)
  - `transformation_error_rate`: number (float or int)
  - `queue_depth`: integer
- Values MUST come from the Hookdeck Metrics API for the window `[now - 1h, now]`, scoped to the resources recorded in `/workspace/resource_ids.json`, and MUST agree with the same endpoints when re-queried by the verifier (small numeric tolerance is allowed for late-arriving sampled metrics).
- The script MUST authenticate using the `HOOKDECK_API_KEY` environment variable; no credentials may be hard-coded.

