const fs = require('fs');
const https = require('https');

const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID;

const API_BASE = 'https://api.hookdeck.com/2024-09-01';

async function req(method, path, data) {
  return new Promise((resolve, reject) => {
    const options = {
      method,
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      }
    };
    
    const req = https.request(`${API_BASE}${path}`, options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body || '{}'));
        } else if (res.statusCode === 409) {
          const parsed = JSON.parse(body || '{}');
          const id = parsed.data.id || 
                     (parsed.data.transformation && parsed.data.transformation.id) || 
                     (parsed.data.source && parsed.data.source.id) ||
                     (parsed.data.connection && parsed.data.connection.id) ||
                     (parsed.data.webhook && parsed.data.webhook.id);
          resolve({ _conflict: true, id: id });
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

async function getOrCreate(resource, data) {
  let res = await req('POST', `/${resource}`, data);
  if (res._conflict) {
    console.log(`Resource ${resource} already exists. ID: ${res.id}`);
    if (resource === 'transformations') {
      res = await req('PUT', `/${resource}/${res.id}`, data);
    }
    return res;
  }
  return res;
}

async function main() {
  try {
    console.log('Creating Source...');
    const source = await getOrCreate('sources', {
      name: `hmac-src-${RUN_ID}`,
      type: 'WEBHOOK'
    });
    console.log('Source ID:', source.id);
    
    console.log('Creating Destination...');
    const destination = await getOrCreate('destinations', {
      name: `hmac-dst-${RUN_ID}`,
      url: `https://mock.hookdeck.com/hmac-dst-${RUN_ID}`
    });
    console.log('Destination ID:', destination.id);
    
    console.log('Creating Transformation...');
    const code = fs.readFileSync('transform.js', 'utf8');
    const transformation = await getOrCreate('transformations', {
      name: `hmac-trf-${RUN_ID}`,
      code: code,
      env: {
        MY_SECRET: `s3cr3t-${RUN_ID}`
      }
    });
    console.log('Transformation ID:', transformation.id);
    
    console.log('Creating Connection...');
    const connection = await getOrCreate('connections', {
      name: `hmac-conn-${RUN_ID}`,
      source_id: source.id,
      destination_id: destination.id,
      rules: [
        {
          type: 'transform',
          transformation_id: transformation.id
        }
      ]
    });
    console.log('Connection ID:', connection.id);
    
    const logOutput = `Source Name: hmac-src-${RUN_ID}\nDestination Name: hmac-dst-${RUN_ID}\nConnection ID: ${connection.id}\nTransformation ID: ${transformation.id}\n`;
    fs.writeFileSync('output.log', logOutput);
    console.log('Wrote to output.log');
    
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

main();
