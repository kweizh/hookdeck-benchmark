# Hookdeck Transformation to Inject Headers

This project configures a Hookdeck connection that receives events and forwards them to a Mock API destination, injecting a custom header `x-custom-run-id` with the value of the current `run-id` using a JavaScript transformation.

## Environment Variables

* **ZEALT_RUN_ID**: `zr-d9nizby`
* **HOOKDECK_API_KEY**: Provided via environment

## Created Hookdeck Resources

* **Source**: `source-zr-d9nizby`
  * ID: `src_dtax5xb0jf6mpy`
  * Type: `WEBHOOK`
  * URL: `https://hkdk.events/dtax5xb0jf6mpy`
* **Destination**: `mock-dest-zr-d9nizby`
  * ID: `des_iLa5D6IV3EYa`
  * Type: `MOCK_API`
* **Transformation**: `inject-header-zr-d9nizby`
  * ID: `trs_C1vhBZMsCMKukH`
* **Connection**: `header-conn-zr-d9nizby`
  * ID: `web_F1IxOByxu9cN`
  * Links `source-zr-d9nizby` to `mock-dest-zr-d9nizby` with transformation `inject-header-zr-d9nizby` attached.

## JavaScript Transformation Code

Located in `transform.js`:

```javascript
addHandler("transform", (request, context) => {
  if (!request.headers) {
    request.headers = {};
  }
  request.headers["x-custom-run-id"] = "zr-d9nizby";
  return request;
});
```
