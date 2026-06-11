const axios = require('axios');
const runId = process.env.ZEALT_RUN_ID;

const code = `
addHandler('transform', (request, context) => {
  console.log("Context keys:", Object.keys(context));
  return request;
});
`;

axios.post("https://api.hookdeck.com/2024-03-01/transformations", {
  name: "transform-test",
  code: code
}, {
  headers: { Authorization: "Bearer " + process.env.HOOKDECK_API_KEY }
}).then(r => console.log(JSON.stringify(r.data, null, 2))).catch(e => console.error(e.response.data));
