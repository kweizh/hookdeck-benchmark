# Hookdeck JS Transformation Setup

## Overview

This project configures a Hookdeck connection with a JavaScript transformation that:
1. Renames `old_key` to `new_key` in the incoming JSON payload
2. Adds an `x-custom-secret` header using a value from the transformation environment variable `MY_SECRET_ENV`

## Resources Created (run-id: zr-8pvnavp)

| Resource | Name | ID |
|----------|------|----|
| Source | `webhook-source-zr-8pvnavp` | `src_rrvf9bw5tzatif` |
| Destination | `mock-dest-zr-8pvnavp` | `des_UAEdydv0swAN` |
| Transformation | `transform-zr-8pvnavp` | `trs_AlalYmYwqarCKP` |
| Connection | `transform-connection-zr-8pvnavp` | `web_JB8uYTnKDGap` |

## Transformation Code

```javascript
addHandler('transform', (request, context) => {
  // Rename old_key to new_key if it exists
  if (request.body && request.body.hasOwnProperty('old_key')) {
    request.body.new_key = request.body.old_key;
    delete request.body.old_key;
  }

  // Add custom header from env var
  request.headers['x-custom-secret'] = context.env.MY_SECRET_ENV;

  return request;
});
```

## Environment Variables

| Variable | Value |
|----------|-------|
| `MY_SECRET_ENV` | `secret-val-zr-8pvnavp` |

## Connection Architecture

```
webhook-source-zr-8pvnavp
        |
        | (POST /rrvf9bw5tzatif)
        v
transform-connection-zr-8pvnavp
        |
        | [Transform Rule: trs_AlalYmYwqarCKP]
        | - Rename old_key -> new_key
        | - Add x-custom-secret header
        v
mock-dest-zr-8pvnavp (MOCK_API)
```

## Re-running Setup

To recreate the resources from scratch:
```bash
export HOOKDECK_API_KEY=<your-key>
export ZEALT_RUN_ID=<your-run-id>
bash setup.sh
```
