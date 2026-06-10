Legacy backends often require flattened JSON payloads and specific custom headers to authenticate or process incoming webhooks.

You need to implement a JavaScript Transformation using `addHandler("transform", (request, context) => {...})` that extracts the nested object at `request.body.data.object`, assigns it directly to `request.body`, and adds the header `"x-hookdeck-transformed": "true"` in the Hookdeck transformation sandbox environment.

**Constraints:**
- Do NOT use `async/await`, `Promises`, `fetch()`, or any network requests, as the V8 isolate environment strictly prohibits them.
- The handler MUST return the mutated `request` object at the end of the function.