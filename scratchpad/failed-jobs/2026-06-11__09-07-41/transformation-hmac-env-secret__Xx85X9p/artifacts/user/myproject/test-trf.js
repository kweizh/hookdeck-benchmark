const https = require('https');
const fs = require('fs');

const API_KEY = process.env.HOOKDECK_API_KEY;

const data = JSON.stringify({
  code: fs.readFileSync('transform.js', 'utf8'),
  env: { MY_SECRET: 'test-secret' },
  request: {
    body: { hello: "world" },
    headers: { "content-type": "application/json" }
  }
});

const options = {
  hostname: 'api.hookdeck.com',
  path: '/2024-09-01/transformations/executions',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(data)
  }
};

const req = https.request(options, res => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => console.log(body));
});

req.write(data);
req.end();
