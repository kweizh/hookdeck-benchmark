addHandler("transform", (request, context) => {
  if (request.body && request.body.data) {
    request.body = request.body.data.object;
  }
  request.headers["x-hookdeck-transformed"] = "true";
  request.headers["x-secret-token"] = context.env.SECRET_TOKEN;
  return request;
});
