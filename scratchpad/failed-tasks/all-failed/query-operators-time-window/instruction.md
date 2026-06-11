# Hookdeck Time-Window Event Query

## Background
A fleet of events has already been published into a Hookdeck Source during environment initialization. The events are spread across a short interval and form three clusters: an *early* window, a *middle* window, and a *late* window. Your job is to interrogate the Hookdeck Events API and retrieve **only** the events whose server-assigned `created_at` falls inside the middle window.

Hookdeck's REST API exposes query operators on list endpoints (see https://hookdeck.com/docs/api). Time-bounded filtering is done with the `gte` / `lte` operators applied to the `created_at` field — for example `?created_at[gte]=<iso>&created_at[lte]=<iso>`. Your solution must rely on this server-side filter; you may **not** download all events and filter them client-side.

## Requirements
- Read the seed file at `/workspace/seed.json` produced during initialization. It contains the following fields:
  - `source_id` — the Hookdeck Source whose events you must query.
  - `window_start` — ISO-8601 timestamp (with millisecond precision and `Z` suffix) marking the inclusive start of the middle window.
  - `window_end` — ISO-8601 timestamp marking the inclusive end of the middle window.
- Write a Python program at `/workspace/query.py` that:
  - Loads `seed.json`.
  - Calls the Hookdeck Events API (`GET https://api.hookdeck.com/2025-07-01/events`) with the bearer token from the `HOOKDECK_API_KEY` environment variable.
  - Restricts the result to the given `source_id` and to the inclusive `[window_start, window_end]` interval using the `created_at[gte]` and `created_at[lte]` query operators in the request URL.
  - Walks the full cursor pagination (use the `next` parameter) until no further pages exist.
  - Writes the result to `/workspace/window.json` with this exact shape:
    ```json
    {
      "count": <integer>,
      "ids": ["evt_...", "evt_...", ...]
    }
    ```
    `count` MUST equal `len(ids)` and MUST equal the value returned by Hookdeck when the same filter is issued server-side. `ids` MUST be the event IDs returned by Hookdeck for that query, with no client-side filtering, slicing, or post-processing.
- Execute the script so that `/workspace/window.json` exists when verification runs.

## Implementation Hints
- Authentication uses `Authorization: Bearer $HOOKDECK_API_KEY`.
- The `gte` and `lte` operators are bracketed query params and must be URL-encoded carefully — the literal `[` and `]` characters need to appear in the request URL after encoding.
- ISO timestamps must be passed through verbatim from `seed.json`; do not round, truncate, or reformat them.
- The Hookdeck list response contains `pagination`, `count`, and `models[]` with each event's `id`.
- Iterate pages until `pagination.next` is absent or null, otherwise tasks with more than 100 events would be truncated.

## Acceptance Criteria
- Project path: `/workspace`
- Ensure `/workspace/query.py` is executed and the artifact `/workspace/window.json` exists.
- `/workspace/window.json` must be valid JSON with exactly two keys: `count` (integer) and `ids` (array of strings).
- `count` must equal `len(ids)`.
- The set of returned `ids` must equal exactly the set of event IDs that an independent server-side query (using `source_id`, `created_at[gte]=window_start`, and `created_at[lte]=window_end` from `seed.json`) returns.
- No event whose `created_at` falls outside the `[window_start, window_end]` window may appear in `ids`.
- The script `/workspace/query.py` must perform server-side filtering: its source must contain the literal substrings `created_at[gte]` and `created_at[lte]`.

