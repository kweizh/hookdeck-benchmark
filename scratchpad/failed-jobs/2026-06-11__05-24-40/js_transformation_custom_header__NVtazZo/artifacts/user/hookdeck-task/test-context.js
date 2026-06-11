addHandler("transform", (request, context) => {
  request.headers["x-context"] = JSON.stringify(context);
  return request;
});
