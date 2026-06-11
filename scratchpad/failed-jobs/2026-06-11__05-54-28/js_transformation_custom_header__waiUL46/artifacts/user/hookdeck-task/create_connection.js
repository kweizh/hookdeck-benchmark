const axios = require('axios');
const runId = process.env.ZEALT_RUN_ID;

const sourceId = "src_9ouhs4wv60dasn";
const destId = "des_XUzGLqgSR99F";
const transformId = "trs_TCGmW8rQcpWsv0";

axios.post("https://api.hookdeck.com/2024-03-01/connections", {
  name: "transform-connection-" + runId,
  source_id: sourceId,
  destination_id: destId,
  rules: [
    {
      type: "transform",
      transformation_id: transformId
    }
  ]
}, {
  headers: { Authorization: "Bearer " + process.env.HOOKDECK_API_KEY }
}).then(r => console.log(JSON.stringify(r.data, null, 2))).catch(e => console.error(e.response.data));
