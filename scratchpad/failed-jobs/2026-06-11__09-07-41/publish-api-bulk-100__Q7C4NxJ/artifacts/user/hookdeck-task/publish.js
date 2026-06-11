const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID;

const API_BASE = 'https://api.hookdeck.com/2025-07-01';
const PUBLISH_URL = 'https://hkdk.events/v1/publish';

async function run() {
  const sourceName = `bulk-source-${RUN_ID}`;
  const destName = `bulk-dest-${RUN_ID}`;
  
  // Publish 100 events
  console.log('Publishing 100 events...');
  const promises = [];
  for (let i = 0; i < 100; i++) {
    promises.push(
      fetch(PUBLISH_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${API_KEY}`,
          'X-Hookdeck-Source-Name': sourceName,
          'x-batch-id': 'BATCH-001'
        },
        body: JSON.stringify({ i })
      })
    );
  }
  
  await Promise.all(promises);
  console.log('Published 100 events.');

  // Fetch source and destination IDs
  const sourcesRes = await fetch(`${API_BASE}/sources?name=${sourceName}`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const sources = await sourcesRes.json();
  const sourceId = sources.models[0].id;

  const destsRes = await fetch(`${API_BASE}/destinations?name=${destName}`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const dests = await destsRes.json();
  const destId = dests.models[0].id;
  
  console.log(`Source ID: ${sourceId}, Dest ID: ${destId}`);

  // Poll for events
  let successfulEvents = 0;
  while (true) {
    const eventsRes = await fetch(`${API_BASE}/events?destination_id=${destId}&status=SUCCESSFUL&limit=100`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    });
    const events = await eventsRes.json();
    successfulEvents = events.pagination.total_entries; // Assuming total_entries is returned
    console.log(`Successful events: ${successfulEvents}`);
    if (successfulEvents >= 100) {
      break;
    }
    if (!events.pagination || typeof events.pagination.total_entries === 'undefined') {
        console.log("No total_entries, trying to count models...");
        successfulEvents = events.models ? events.models.length : 0;
        console.log(`Successful events (counted): ${successfulEvents}`);
        if (successfulEvents >= 100) break;
    }
    await new Promise(r => setTimeout(r, 2000));
  }
  
  const fs = require('fs');
  const logContent = `Source Name: ${sourceName}
Destination Name: ${destName}
Published Count: 100
Batch ID: BATCH-001
`;
  fs.writeFileSync('/home/user/hookdeck-task/output.log', logContent);
  console.log('Log written.');
}

run().catch(console.error);
