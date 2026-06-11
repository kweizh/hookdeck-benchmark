addHandler("transform", (request, context) => {
  if (request.body === undefined || request.body === null || request.body.required_field === undefined) {
    throw new Error("Missing required field: required_field");
  }
  return request;
});
