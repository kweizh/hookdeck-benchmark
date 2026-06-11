const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;

function request(method, path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: '/2025-07-01' + path,
      method,
      headers: {
        'Authorization': `Bearer ${API_KEY}`
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve(JSON.parse(body)));
    });

    req.on('error', reject);
    req.end();
  });
}

async function main() {
  const fs = require('fs');
  const connLog = fs.readFileSync('/home/user/hookdeck-task/output.log', 'utf8');
  const connId = connLog.split(': ')[1].trim();
  
  const events = await request('GET', `/events?webhook_id=${connId}`);
  console.log('Count:', events.count);
  if (events.models && events.models.length > 0) {
    console.log('First event body:', events.models[0].data.body);
    console.log('First event headers:', events.models[0].data.headers);
  }
}

main();
