const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID;

const API_BASE = 'https://api.hookdeck.com/2025-07-01';

async function run() {
  const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  };

  // Create Destination
  let res = await fetch(`${API_BASE}/destinations`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      name: `bulk-dest-${RUN_ID}`,
      type: 'MOCK_API'
    })
  });
  const dest = await res.json();
  console.log('Dest:', dest);

  // Create Source
  res = await fetch(`${API_BASE}/sources`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      name: `bulk-source-${RUN_ID}`
    })
  });
  const source = await res.json();
  console.log('Source:', source);

  // Create Connection
  res = await fetch(`${API_BASE}/connections`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      source_id: source.id,
      destination_id: dest.id
    })
  });
  const conn = await res.json();
  console.log('Connection:', conn);
}

run().catch(console.error);
