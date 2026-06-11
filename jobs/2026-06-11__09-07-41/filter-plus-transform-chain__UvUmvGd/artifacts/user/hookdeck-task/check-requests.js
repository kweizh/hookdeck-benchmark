const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID || 'default-run';
const SRC_NAME = `chain-src-${RUN_ID}`;

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
  const sources = await request('GET', `/sources?name=${SRC_NAME}`);
  if (sources.models && sources.models.length > 0) {
    const sourceId = sources.models[0].id;
    const reqs = await request('GET', `/requests?source_id=${sourceId}`);
    console.log(`Requests for source ${sourceId}:`, reqs.count);
    if (reqs.models) {
       console.log(reqs.models.map(r => r.id));
    }
  } else {
    console.log('Source not found');
  }
}

main();
