const fs = require('fs');
const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID || 'local';

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
    // 1. Create Source
    const source = await request('POST', '/sources', {
      name: `flatten-src-${RUN_ID}`
    });
    console.log('Source created:', source.id);

    // 2. Create Destination
    const destination = await request('POST', '/destinations', {
      name: `flatten-dest-${RUN_ID}`,
      type: 'MOCK_API'
    });
    console.log('Destination created:', destination.id);

    // 3. Create Transformation
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
    
    const transformation = await request('POST', '/transformations', {
      name: `flatten-rename-${RUN_ID}`,
      code: code
    });
    console.log('Transformation created:', transformation.id);

    // 4. Create Connection
    const connection = await request('POST', '/connections', {
      name: `flatten-conn-${RUN_ID}`,
      source_id: source.id,
      destination_id: destination.id,
      rules: [
        {
          type: 'transform',
          transformation_id: transformation.id
        }
      ]
    });
    console.log('Connection created:', connection.id);

    // 5. Publish 3 Events
    const events = [
      {
        data: {
          object: {
            id: "evt_1",
            amount: 50,
            currency: "usd",
            customer_email: "test1@example.com"
          }
        }
      },
      {
        data: {
          object: {
            id: "evt_2",
            amount: 200,
            currency: "usd",
            customer_email: "test2@example.com"
          }
        }
      },
      {
        data: {
          object: {
            id: "evt_3",
            amount: 200,
            currency: "usd",
            customer_email: "test3@example.com"
          }
        }
      }
    ];

    for (const evt of events) {
      await publish(source.url, evt);
      console.log('Published event:', evt.data.object.id);
      await new Promise(r => setTimeout(r, 1000));
    }

    // Wait a bit for delivery
    await new Promise(r => setTimeout(r, 5000));

    // 6. Write Output
    const result = {
      transformation_id: transformation.id,
      source_id: source.id,
      destination_id: destination.id,
      connection_id: connection.id
    };

    const outDir = '/home/user/hookdeck-task';
    if (!fs.existsSync(outDir)) {
      fs.mkdirSync(outDir, { recursive: true });
    }
    fs.writeFileSync(`${outDir}/output.log`, `RESULT: ${JSON.stringify(result)}\n`);
    console.log('Done.');

  } catch (err) {
    console.error('Error:', err);
    process.exit(1);
  }
}

main();
