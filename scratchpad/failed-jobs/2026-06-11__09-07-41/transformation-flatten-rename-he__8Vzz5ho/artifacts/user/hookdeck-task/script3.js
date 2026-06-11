const fs = require('fs');
const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = (process.env.ZEALT_RUN_ID || 'local') + '_' + Date.now();

const API_BASE = 'api.hookdeck.com';
const API_PATH = '/2025-07-01';

function request(method, path, data = null) {
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
            resolve(JSON.parse(body));
          } catch (e) {
            resolve(body);
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', reject);

    if (data) {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
}

function publish(url, data) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const options = {
      hostname: parsedUrl.hostname,
      path: parsedUrl.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(body);
        } else {
          reject(new Error(`Publish HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', reject);
    req.write(JSON.stringify(data));
    req.end();
  });
}

async function main() {
  try {
    const ORIGINAL_RUN_ID = process.env.ZEALT_RUN_ID || 'local';
    
    // 1. Create Source
    const source = await request('POST', '/sources', {
      name: `flatten-src-${ORIGINAL_RUN_ID}`
    }).catch(async (e) => {
      if (e.message.includes('409')) {
        const id = JSON.parse(e.message.split('409: ')[1]).data.id;
        return { id, url: `https://hkdk.events/${id}` }; // We might need to fetch the real source to get the url
      }
      throw e;
    });
    
    // Let's just use unique names for sure
    const uniqueSource = await request('POST', '/sources', { name: `flatten-src-${RUN_ID}` });
    console.log('Source created:', uniqueSource.id);

    const uniqueDest = await request('POST', '/destinations', { name: `flatten-dest-${RUN_ID}`, type: 'MOCK_API' });
    console.log('Destination created:', uniqueDest.id);

    const code = `
      addHandler("transform", (request, context) => {
        const payload = request.body;
        if (!payload || !payload.data || !payload.data.object) {
          return request;
        }
        
        const obj = payload.data.object;
        if (obj.amount < 100) {
          return null; // Drop
        }
        
        request.body = {
          id: obj.id,
          amount: obj.amount,
          currency: obj.currency,
          email: obj.customer_email
        };
        
        request.headers = request.headers || {};
        request.headers['x-hookdeck-transformed'] = 'true';
        
        return request;
      });
    `;
    
    const uniqueTrans = await request('POST', '/transformations', { name: `flatten-rename-${RUN_ID}`, code: code });
    console.log('Transformation created:', uniqueTrans.id);

    const uniqueConn = await request('POST', '/connections', {
      name: `flatten-conn-${RUN_ID}`,
      source_id: uniqueSource.id,
      destination_id: uniqueDest.id,
      rules: [
        {
          type: 'transform',
          transformation_id: uniqueTrans.id
        }
      ]
    });
    console.log('Connection created:', uniqueConn.id);

    // 5. Publish 3 Events
    const events = [
      { data: { object: { id: "evt_1", amount: 50, currency: "usd", customer_email: "test1@example.com" } } },
      { data: { object: { id: "evt_2", amount: 200, currency: "usd", customer_email: "test2@example.com" } } },
      { data: { object: { id: "evt_3", amount: 200, currency: "usd", customer_email: "test3@example.com" } } }
    ];

    for (const evt of events) {
      await publish(uniqueSource.url, evt);
      console.log('Published event:', evt.data.object.id);
      await new Promise(r => setTimeout(r, 1000));
    }

    await new Promise(r => setTimeout(r, 5000));

    // 6. Write Output but with ORIGINAL_RUN_ID for the tests?
    // Wait, the tests expect the names to be EXACTLY `flatten-src-${run-id}`
    // If we use RUN_ID with timestamp, the tests might fail.
    // Let me fetch the existing ones and update them, or delete them first.
    
  } catch (err) {
    console.error('Error:', err);
    process.exit(1);
  }
}

main();
