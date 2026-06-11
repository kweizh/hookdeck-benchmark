const https = require('https');
const fs = require('fs');

const runId = process.env.ZEALT_RUN_ID || 'default-run-id';
const apiKey = process.env.HOOKDECK_API_KEY;

if (!apiKey) {
  console.error("HOOKDECK_API_KEY is required");
  process.exit(1);
}

const sourceName = `source-${runId}`;
const destName = `dest-${runId}`;
const connName = `conn-${runId}`;

async function request(method, path, data = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: `/2024-09-01${path}`,
      method: method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      }
    };

    const req = https.request(options, res => {
      let body = '';
      res.on('data', chunk => body += chunk.toString());
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body));
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on('error', error => reject(error));

    if (data) {
      req.write(JSON.stringify(data));
    }
    req.end();
  });
}

async function main() {
  try {
    // 1. Create Source
    console.log(`Creating source: ${sourceName}`);
    const source = await request('POST', '/sources', {
      name: sourceName
    });
    console.log(`Source created: ${source.id}`);

    // 2. Create Destination
    console.log(`Creating destination: ${destName}`);
    const destination = await request('POST', '/destinations', {
      name: destName,
      url: 'https://mock.hookdeck.com'
    });
    console.log(`Destination created: ${destination.id}`);

    // 3. Create Connection
    console.log(`Creating connection: ${connName}`);
    const connection = await request('POST', '/connections', {
      name: connName,
      source_id: source.id,
      destination_id: destination.id,
      rules: [
        {
          type: 'filter',
          body: {
            type: 'order.created'
          }
        }
      ]
    });
    console.log(`Connection created: ${connection.id}`);

    fs.writeFileSync('/home/user/hookdeck-task/output.log', `Connection ID: ${connection.id}\n`);
    console.log('Log file written successfully.');

  } catch(e) {
    console.error(e);
    process.exit(1);
  }
}

main();