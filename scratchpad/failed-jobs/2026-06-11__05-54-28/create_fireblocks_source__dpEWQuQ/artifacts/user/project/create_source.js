const fs = require('fs');
const https = require('https');

const runId = process.env.ZEALT_RUN_ID;
const apiKey = process.env.HOOKDECK_API_KEY;

const data = JSON.stringify({
  name: `fireblocks-source-${runId}`,
  type: "FIREBLOCKS",
  config: {
    auth_type: "FIREBLOCKS",
    auth: {
      environment: "sandbox"
    }
  }
});

const options = {
  hostname: 'api.hookdeck.com',
  path: '/2024-03-01/sources',
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json',
    'Content-Length': data.length
  }
};

const req = https.request(options, (res) => {
  let body = '';
  res.on('data', (chunk) => {
    body += chunk;
  });
  
  res.on('end', () => {
    const response = JSON.parse(body);
    if (response.id) {
      fs.writeFileSync('/home/user/project/source.log', `Source ID: ${response.id}\n`);
      console.log(`Successfully created source ${response.id}`);
    } else {
      console.error('Failed to create source:', response);
    }
  });
});

req.on('error', (error) => {
  console.error(error);
});

req.write(data);
req.end();
