addHandler("transform", (request, context) => {
  if (request.body && request.body.data && request.body.data.object) {
    request.body = request.body.data.object;
  }
  return request;
});
