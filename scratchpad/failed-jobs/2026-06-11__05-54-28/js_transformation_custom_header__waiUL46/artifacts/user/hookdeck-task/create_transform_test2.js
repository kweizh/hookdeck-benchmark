const axios = require('axios');
const runId = process.env.ZEALT_RUN_ID;

const code = `
addHandler('transform', (request, context) => {
  console.log("process.env:", typeof process !== 'undefined' ? Object.keys(process.env) : 'undefined');
  console.log("context:", JSON.stringify(context));
  return request;
});
`;

axios.put("https://api.hookdeck.com/2024-03-01/transformations/trs_knrS3O6GOUwkAg", {
  code: code,
  env: { "MY_SECRET_ENV": "secret-val-" + runId }
}, {
  headers: { Authorization: "Bearer " + process.env.HOOKDECK_API_KEY }
}).then(r => console.log(JSON.stringify(r.data, null, 2))).catch(e => console.error(e.response.data));
