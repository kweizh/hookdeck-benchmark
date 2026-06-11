const https = require('https');
const API_KEY = process.env.HOOKDECK_API_KEY;

function request(method, path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: '/2025-07-01' + path,
      method,
      headers: { 'Authorization': `Bearer ${API_KEY}` }
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
  const reqDetail = await request('GET', `/requests/req_3GQYxUY6zCH0ddqeOwOp`);
  console.log(JSON.stringify(reqDetail, null, 2));
}
main();
