export default function (request, context) {
  if (request.body && request.body.data && request.body.data.object) {
    request.body = request.body.data.object;
  }
  
  request.headers = request.headers || {};
  request.headers['x-hookdeck-transformed'] = 'true';
  request.headers['x-secret-token'] = context.env.SECRET_TOKEN;

  return request;
}
