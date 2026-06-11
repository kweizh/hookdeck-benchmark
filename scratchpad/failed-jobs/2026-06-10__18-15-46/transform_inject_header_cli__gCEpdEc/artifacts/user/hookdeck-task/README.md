# Hookdeck Transformation - Inject Headers

## Run ID
`zr-gcepdec`

## Created Resources

### Source
- **Name**: `source-zr-gcepdec`
- **ID**: `src_28w2y9vcdxt0hs`
- **URL**: `https://hkdk.events/28w2y9vcdxt0hs`

### Destination
- **Name**: `mock-dest-zr-gcepdec`
- **ID**: `des_qY5kcPgvfH6V`
- **Type**: MOCK (URL: `https://mock.hookdeck.com`)

### Transformation
- **Name**: `inject-header-zr-gcepdec`
- **ID**: `trs_NOVzRnWOYHnVGy`
- **Code**:
```javascript
addHandler('transform', (request, context) => { request.headers['x-custom-run-id'] = 'zr-gcepdec'; return request; });
```

### Connection
- **Name**: `header-conn-zr-gcepdec`
- **ID**: `web_OBAtxB91GKhl`
- **Source**: `source-zr-gcepdec`
- **Destination**: `mock-dest-zr-gcepdec`
- **Transformation**: `inject-header-zr-gcepdec` (attached via rules)

## Acceptance Criteria Met
- [x] Connection named `header-conn-zr-gcepdec` exists
- [x] Connection links Source `source-zr-gcepdec` to Destination `mock-dest-zr-gcepdec`
- [x] Destination `mock-dest-zr-gcepdec` is of type MOCK
- [x] Transformation `inject-header-zr-gcepdec` is attached to the connection
- [x] Transformation code adds header `x-custom-run-id` with value `zr-gcepdec`