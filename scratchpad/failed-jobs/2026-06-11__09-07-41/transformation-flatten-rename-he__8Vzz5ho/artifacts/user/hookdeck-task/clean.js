const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;
const API_BASE = 'api.hookdeck.com';
const API_PATH = '/2025-07-01';

function request(method, path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: API_BASE,
      path: `${API_PATH}${path}`,
      method: method,
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(body || '{}'));
          } catch (e) {
            resolve(body);
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function clean() {
  try {
    const conns = await request('GET', '/connections');
    for (const c of conns.models) await request('DELETE', `/connections/${c.id}`);

    const sources = await request('GET', '/sources');
    for (const s of sources.models) await request('DELETE', `/sources/${s.id}`);

    const dests = await request('GET', '/destinations');
    for (const d of dests.models) await request('DELETE', `/destinations/${d.id}`);

    const trans = await request('GET', '/transformations');
    for (const t of trans.models) await request('DELETE', `/transformations/${t.id}`);

    console.log('Cleaned up');
  } catch (e) {
    console.error(e);
  }
}

clean();
