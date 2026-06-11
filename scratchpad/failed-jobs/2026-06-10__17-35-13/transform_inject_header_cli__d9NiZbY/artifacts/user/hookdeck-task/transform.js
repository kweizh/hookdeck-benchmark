addHandler("transform", (request, context) => {
  if (!request.headers) {
    request.headers = {};
  }
  request.headers["x-custom-run-id"] = "zr-d9nizby";
  return request;
});
