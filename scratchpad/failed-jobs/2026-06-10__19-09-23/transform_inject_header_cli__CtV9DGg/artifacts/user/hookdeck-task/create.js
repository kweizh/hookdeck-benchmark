const fetch = require('node-fetch');

const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID;
const BASE_URL = 'https://api.hookdeck.com/2024-03-01';

async function request(endpoint, method, body) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: body ? JSON.stringify(body) : undefined
  });
  const data = await res.json();
  if (!res.ok) {
    console.error(`Error on ${method} ${endpoint}:`, data);
    process.exit(1);
  }
  return data;
}

async function main() {
  console.log(`Creating resources for run-id: ${RUN_ID}`);

  // 1. Create Source
  const sourceName = `source-${RUN_ID}`;
  console.log(`Creating source: ${sourceName}`);
  const source = await request('/sources', 'POST', { name: sourceName });
  console.log(`Source created: ${source.id}`);

  // 2. Create Destination
  const destName = `mock-dest-${RUN_ID}`;
  console.log(`Creating destination: ${destName}`);
  const dest = await request('/destinations', 'POST', { 
    name: destName, 
    url: 'https://mock.hookdeck.com' 
  });
  console.log(`Destination created: ${dest.id}`);

  // 3. Create Transformation
  const transformName = `inject-header-${RUN_ID}`;
  console.log(`Creating transformation: ${transformName}`);
  const code = `
addHandler("transform", (request, context) => {
  request.headers["x-custom-run-id"] = "${RUN_ID}";
  return request;
});
  `.trim();
  
  const transform = await request('/transformations', 'POST', {
    name: transformName,
    code: code
  });
  console.log(`Transformation created: ${transform.id}`);

  // 4. Create Connection
  const connName = `header-conn-${RUN_ID}`;
  console.log(`Creating connection: ${connName}`);
  const connection = await request('/connections', 'POST', {
    name: connName,
    source_id: source.id,
    destination_id: dest.id,
    rules: [
      {
        type: 'transform',
        transformation_id: transform.id
      }
    ]
  });
  console.log(`Connection created: ${connection.id}`);
  
  console.log('Done!');
}

main().catch(console.error);
