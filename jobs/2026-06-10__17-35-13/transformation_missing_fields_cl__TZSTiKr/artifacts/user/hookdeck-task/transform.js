addHandler('transform', (request, context) => {
  if (!request.body || typeof request.body !== 'object') {
    request.body = {};
  }
  request.body.user_id = request.body?.data?.user?.id ?? null;
  return request;
});
