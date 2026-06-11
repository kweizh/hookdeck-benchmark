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
      res.on('end', () => resolve(body ? JSON.parse(body) : {}));
    });
    req.on('error', reject);
    req.end();
  });
}

async function clean() {
  const RUN_ID = process.env.ZEALT_RUN_ID;
  
  const conns = await request('GET', `/connections?name=chain-conn-${RUN_ID}`);
  for (const c of (conns.models || [])) await request('DELETE', `/connections/${c.id}`);

  const dests = await request('GET', `/destinations?name=chain-dest-${RUN_ID}`);
  for (const d of (dests.models || [])) await request('DELETE', `/destinations/${d.id}`);

  const srcs = await request('GET', `/sources?name=chain-src-${RUN_ID}`);
  for (const s of (srcs.models || [])) await request('DELETE', `/sources/${s.id}`);

  const trans = await request('GET', `/transformations?name=transform-${RUN_ID}`);
  for (const t of (trans.models || [])) await request('DELETE', `/transformations/${t.id}`);
  
  console.log('Cleaned up resources');
}
clean();
