const https = require('https');
const fs = require('fs');

const apiKey = process.env.HOOKDECK_API_KEY;

async function request(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: path,
      method: method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });

    req.on('error', reject);
    if (body) {
      req.write(typeof body === 'string' ? body : JSON.stringify(body));
    }
    req.end();
  });
}

async function main() {
    const log = fs.readFileSync('/home/user/hookdeck-task/output.log', 'utf8');
    const sourceId = log.match(/Source ID: (.*)/)[1];
    
    const res = await request('GET', `/2025-07-01/sources/${sourceId}`);
    console.log(JSON.stringify(res.data, null, 2));
}

main();