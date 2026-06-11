const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID || 'default-run';

const SRC_NAME = `chain-src-${RUN_ID}`;
const DEST_NAME = `chain-dest-${RUN_ID}`;
const CONN_NAME = `chain-conn-${RUN_ID}`;
const TRANSFORM_NAME = `transform-${RUN_ID}`;

function request(method, path, data = null, isEventsApi = false) {
  return new Promise((resolve, reject) => {
    const hostname = isEventsApi ? 'hkdk.events' : 'api.hookdeck.com';
    const basePath = isEventsApi ? '' : '/2025-07-01';
    
    const options = {
      hostname,
      port: 443,
      path: basePath + path,
      method,
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    };

    if (isEventsApi) {
      delete options.headers['Authorization'];
      options.headers['X-Hookdeck-Source-Name'] = SRC_NAME;
    }

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          if (body) {
            resolve(JSON.parse(body));
          } else {
            resolve(null);
          }
        } catch (e) {
          resolve(body);
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

async function main() {
  try {
    // 1. Create Transformation
    console.log('Creating transformation...');
    const transformCode = `export default function(request) {
  request.body.processed_at = new Date().toISOString();
  if (!request.headers) { request.headers = {}; }
  request.headers['x-processed'] = 'true';
  return request;
}`;
    const transformRes = await request('POST', '/transformations', {
      name: TRANSFORM_NAME,
      code: transformCode
    });
    
    // If it already exists, it returns 409 and gives the id in data.transformation.id
    let transformId;
    if (transformRes.code === 'RESOURCE_ALREADY_EXISTS') {
      transformId = transformRes.data.transformation.id;
    } else {
      transformId = transformRes.id;
    }
    console.log('Transform ID:', transformId);

    // 2. Create Destination
    console.log('Creating destination...');
    const destRes = await request('POST', '/destinations', {
      name: DEST_NAME,
      type: 'MOCK_API'
    });
    const destId = destRes.id || (destRes.data && destRes.data.destination && destRes.data.destination.id);
    if (!destId && destRes.code === 'RESOURCE_ALREADY_EXISTS') {
        const dests = await request('GET', `/destinations?name=${DEST_NAME}`);
        // need to handle if exists, but let's assume it doesn't since run-id is unique
    }
    console.log('Destination ID:', destRes.id);

    // 3. Create Source
    console.log('Creating source...');
    const srcRes = await request('POST', '/sources', {
      name: SRC_NAME,
      type: 'WEBHOOK'
    });
    console.log('Source ID:', srcRes.id);

    // 4. Create Connection
    console.log('Creating connection...');
    const connRes = await request('POST', '/connections', {
      name: CONN_NAME,
      source_id: srcRes.id,
      destination_id: destRes.id,
      rules: [
        {
          type: 'filter',
          body: {
            type: 'order.created'
          }
        },
        {
          type: 'transform',
          transformation_id: transformId
        }
      ]
    });
    console.log('Connection ID:', connRes.id);

    // Write to output.log
    const fs = require('fs');
    fs.writeFileSync('/home/user/hookdeck-task/output.log', `Connection ID: ${connRes.id}\n`);

    // 5. Publish 4 events
    console.log('Publishing events...');
    const publishPath = '/v1/publish';
    
    // Event 1 (match)
    await request('POST', publishPath, { type: 'order.created', data: 'event1' }, true);
    // Event 2 (match)
    await request('POST', publishPath, { type: 'order.created', data: 'event2' }, true);
    // Event 3 (no match)
    await request('POST', publishPath, { type: 'order.updated', data: 'event3' }, true);
    // Event 4 (no match)
    await request('POST', publishPath, { type: 'customer.created', data: 'event4' }, true);

    console.log('Events published. Waiting a few seconds...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    console.log('Done.');

  } catch (error) {
    console.error('Error:', error);
  }
}

main();
