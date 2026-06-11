addHandler("transform", (request, context) => {
  // Rename old_key to new_key in the body
  if (request.body && request.body.old_key !== undefined) {
    request.body.new_key = request.body.old_key;
    delete request.body.old_key;
  }

  // Add custom header from environment variable
  request.headers = request.headers || {};
  request.headers["x-custom-secret"] = context.env.MY_SECRET_ENV;

  return request;
});