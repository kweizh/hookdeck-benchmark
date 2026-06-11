addHandler("transform", (request, context) => {
  if (request.body && request.body.data && request.body.data.user) {
    request.body.user_id = request.body.data.user.id;
    request.body.user_email = request.body.data.user.email;
  }
  delete request.body.data;
  return request;
});
