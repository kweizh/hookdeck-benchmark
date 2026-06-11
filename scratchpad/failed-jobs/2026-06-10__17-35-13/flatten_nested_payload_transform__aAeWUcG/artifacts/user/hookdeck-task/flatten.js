addHandler('transform', (request, context) => {
  let bodyObj = request.body;
  if (typeof bodyObj === 'string') {
    try {
      bodyObj = JSON.parse(bodyObj);
    } catch (e) {
      // ignore
    }
  }

  if (bodyObj && bodyObj.data && bodyObj.data.object) {
    request.body = bodyObj.data.object;
  }
  return request;
});
