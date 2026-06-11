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
        try {
          resolve(JSON.parse(body));
        } catch (e) {
          resolve(body);
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function main() {
  const publishPath = '/v1/publish';
  console.log('Publishing event 1:', await request('POST', publishPath, { type: 'order.created', data: 'event1' }));
  console.log('Publishing event 2:', await request('POST', publishPath, { type: 'order.created', data: 'event2' }));
  console.log('Publishing event 3:', await request('POST', publishPath, { type: 'order.updated', data: 'event3' }));
  console.log('Publishing event 4:', await request('POST', publishPath, { type: 'customer.created', data: 'event4' }));
}

main();
