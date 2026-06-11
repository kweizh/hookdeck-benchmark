addHandler("transform", (request, context) => {
  // 1. Rename the key `old_key` to `new_key` in the JSON payload body (keeping the same value).
  // If `old_key` does not exist, do nothing to the body.
  if (request.body && typeof request.body === 'object' && !Array.isArray(request.body)) {
    if ('old_key' in request.body) {
      request.body.new_key = request.body.old_key;
      delete request.body.old_key;
    }
  }

  // 2. Add a custom header `x-custom-secret` to the request.
  // The value of this header must be read from the transformation's environment variable `MY_SECRET_ENV`.
  if (!request.headers) {
    request.headers = {};
  }
  
  const secretEnv = (context && context.env && context.env.MY_SECRET_ENV) || (typeof process !== 'undefined' && process.env && process.env.MY_SECRET_ENV) || "";
  request.headers["x-custom-secret"] = secretEnv;

  return request;
});
