const https = require('https');
const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID || 'default-run';
const SRC_NAME = `chain-src-${RUN_ID}`;

function request(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'hkdk.events',
      port: 443,
      path: path,
      method,
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
        'X-Hookdeck-Source-Name': SRC_NAME
      }
    };
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); } catch (e) { resolve(body); }
      });
    });
    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function main() {
  console.log('Publishing exact match:', await request('POST', '/v1/publish', { type: 'order.created' }));
}
main();
