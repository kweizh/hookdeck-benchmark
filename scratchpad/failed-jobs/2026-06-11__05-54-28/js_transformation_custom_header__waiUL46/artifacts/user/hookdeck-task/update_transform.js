const axios = require('axios');
const runId = process.env.ZEALT_RUN_ID;

const code = `
addHandler('transform', (request, context) => {
  if (request.body && typeof request.body === 'object' && !Array.isArray(request.body)) {
    if ('old_key' in request.body) {
      request.body.new_key = request.body.old_key;
      delete request.body.old_key;
    }
  }
  if (!request.headers) {
    request.headers = {};
  }
  request.headers['x-custom-secret'] = process.env.MY_SECRET_ENV;
  return request;
});
`;

axios.put("https://api.hookdeck.com/2024-03-01/transformations/trs_TCGmW8rQcpWsv0", {
  code: code,
  env: {
    "MY_SECRET_ENV": "secret-val-" + runId
  }
}, {
  headers: { Authorization: "Bearer " + process.env.HOOKDECK_API_KEY }
}).then(r => console.log(JSON.stringify(r.data, null, 2))).catch(e => console.error(e.response.data));
