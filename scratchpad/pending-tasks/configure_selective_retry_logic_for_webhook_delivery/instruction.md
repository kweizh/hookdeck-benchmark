Treating all HTTP delivery failures equally leads to unnecessary retry storms for unrecoverable client errors.

You need to write a JSON destination configuration that applies a custom retry strategy designed to automatically retry on `5xx` server errors but completely ignore and drop delivery attempts on `4xx` client errors in a Hookdeck destination routing environment.

**Constraints:**
- The output MUST be valid JSON focusing purely on the destination's retry rule and HTTP status code targeting.
- Do NOT include code for creating the source or transformations; focus solely on the destination retry logic.