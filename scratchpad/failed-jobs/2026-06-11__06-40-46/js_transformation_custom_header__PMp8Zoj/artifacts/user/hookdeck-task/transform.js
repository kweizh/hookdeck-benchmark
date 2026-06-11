addHandler("transform", (request, context) => {
  // Rename old_key to new_key in the JSON payload body
  const body = request.body;
  if (body && typeof body === "object" && "old_key" in body) {
    body.new_key = body.old_key;
    delete body.old_key;
    request.body = body;
  }

  // Add custom header x-custom-secret from environment variable
  const secret = process.env.MY_SECRET_ENV;
  if (secret) {
    request.headers["x-custom-secret"] = secret;
  }

  return request;
});
