const https = require('https');
const fs = require('fs');

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
    console.log('Creating transformation...');
    const transformCode = `addHandler('transform', (request, context) => {
  request.body.processed_at = new Date().toISOString();
  if (!request.headers) { request.headers = {}; }
  request.headers['x-processed'] = 'true';
  return request;
});`;
    const transformRes = await request('POST', '/transformations', {
      name: TRANSFORM_NAME,
      code: transformCode
    });
    
    let transformId = transformRes.id;
    if (transformRes.code === 'RESOURCE_ALREADY_EXISTS') {
      transformId = transformRes.data.transformation.id;
    }
    console.log('Transform ID:', transformId);

    console.log('Creating destination...');
    const destRes = await request('POST', '/destinations', {
      name: DEST_NAME,
      type: 'MOCK_API'
    });
    console.log('Destination ID:', destRes.id);

    console.log('Creating source...');
    const srcRes = await request('POST', '/sources', {
      name: SRC_NAME,
      type: 'WEBHOOK'
    });
    console.log('Source ID:', srcRes.id);

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

    fs.writeFileSync('/home/user/hookdeck-task/output.log', `Connection ID: ${connRes.id}\n`);

    console.log('Publishing events...');
    const publishPath = '/v1/publish';
    
    await request('POST', publishPath, { type: 'order.created', data: 'event1' }, true);
    await request('POST', publishPath, { type: 'order.created', data: 'event2' }, true);
    await request('POST', publishPath, { type: 'order.updated', data: 'event3' }, true);
    await request('POST', publishPath, { type: 'customer.created', data: 'event4' }, true);

    console.log('Events published. Waiting 5 seconds...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    console.log('Done.');

  } catch (error) {
    console.error('Error:', error);
  }
}

main();
