# Hookdeck Header Injection Setup

## Run ID: zr-8mkgmjf

## Resources Created

### Source
- **Name**: `source-zr-8mkgmjf`
- **ID**: `src_t08t9bhp0xx69d`
- **URL**: `https://hkdk.events/t08t9bhp0xx69d`

### Destination
- **Name**: `mock-dest-zr-8mkgmjf`
- **ID**: `des_wkbLFYHca57a`
- **Type**: `MOCK_API`

### Transformation
- **Name**: `inject-header-zr-8mkgmjf`
- **ID**: `trs_g8AtLQIVbf9Iho`
- **Code**:
  ```js
  addHandler('transform', (request, context) => {
    request.headers['x-custom-run-id'] = 'zr-8mkgmjf';
    return request;
  });
  ```

### Connection
- **Name**: `header-conn-zr-8mkgmjf`
- **ID**: `web_xUBpAjTGEor5`
- **Source** → `source-zr-8mkgmjf`
- **Destination** → `mock-dest-zr-8mkgmjf`
- **Transformation Rule** → `inject-header-zr-8mkgmjf` (type: `transform`, transformer: `target`)
