addHandler("transform", (request, context) => {
  const body = JSON.parse(request.body);
  
  // Extract user fields from nested data.user
  const user_id = body.data?.user?.id;
  const user_email = body.data?.user?.email;
  
  // Remove the data object and add flattened fields at root level
  delete body.data;
  body.user_id = user_id;
  body.user_email = user_email;
  
  request.body = JSON.stringify(body);
  return request;
});
