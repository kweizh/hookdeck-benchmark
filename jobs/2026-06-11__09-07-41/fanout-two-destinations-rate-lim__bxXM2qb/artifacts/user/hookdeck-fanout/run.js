const fs = require('fs');

const runId = process.env.ZEALT_RUN_ID;
const apiKey = process.env.HOOKDECK_API_KEY;

const sourceName = `fanout-src-${runId}`;
const fastDestName = `fanout-fast-${runId}`;
const slowDestName = `fanout-slow-${runId}`;
const fastConnName = `fanout-fast-conn-${runId}`;
const slowConnName = `fanout-slow-conn-${runId}`;

async function apiCall(method, path, body) {
  let retries = 3;
  while (retries > 0) {
    const res = await fetch(`https://api.hookdeck.com/2025-07-01${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: body ? JSON.stringify(body) : undefined
    });
    if (!res.ok) {
      if (res.status === 429) {
        retries--;
        await new Promise(r => setTimeout(r, 2000));
        continue;
      }
      const text = await res.text();
      throw new Error(`API error ${res.status}: ${text}`);
    }
    return res.json();
  }
  throw new Error('Max retries reached for 429');
}

async function main() {
  try {
    // 1. Create Source
    const source = await apiCall('POST', '/sources', { name: sourceName });
    const sourceId = source.id;
    console.log('Source ID:', sourceId);
    await new Promise(r => setTimeout(r, 500));

    // 2. Create Fast Destination
    const fastDest = await apiCall('POST', '/destinations', {
      name: fastDestName,
      type: 'MOCK_API'
    });
    const fastDestId = fastDest.id;
    console.log('Fast Destination ID:', fastDestId);
    await new Promise(r => setTimeout(r, 500));

    // 3. Create Slow Destination
    const slowDest = await apiCall('POST', '/destinations', {
      name: slowDestName,
      type: 'MOCK_API',
      config: {
        rate_limit: 2,
        rate_limit_period: 'second'
      }
    });
    const slowDestId = slowDest.id;
    console.log('Slow Destination ID:', slowDestId);
    await new Promise(r => setTimeout(r, 500));

    // 4. Create Connections
    const fastConn = await apiCall('POST', '/connections', {
      name: fastConnName,
      source_id: sourceId,
      destination_id: fastDestId
    });
    const fastConnId = fastConn.id;
    console.log('Fast Connection ID:', fastConnId);
    await new Promise(r => setTimeout(r, 500));

    const slowConn = await apiCall('POST', '/connections', {
      name: slowConnName,
      source_id: sourceId,
      destination_id: slowDestId
    });
    const slowConnId = slowConn.id;
    console.log('Slow Connection ID:', slowConnId);
    await new Promise(r => setTimeout(r, 500));

    // 5. Publish 12 Events
    console.log('Publishing 12 events...');
    const publishPromises = [];
    for (let i = 0; i < 12; i++) {
      const p = fetch('https://hkdk.events/v1/publish', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'X-Hookdeck-Source-Id': sourceId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ eventNumber: i, timestamp: Date.now() })
      }).then(res => {
        if (!res.ok) throw new Error('Publish failed');
        return res.json();
      });
      publishPromises.push(p);
      // Wait a tiny bit to avoid hitting publish rate limits, just in case
      await new Promise(r => setTimeout(r, 50));
    }
    await Promise.all(publishPromises);
    console.log('Published 12 events.');

    // 6. Wait for events to drain (slow dest is 2/sec, 12 events = ~6 seconds)
    // We'll wait 12 seconds to be safe
    console.log('Waiting 12 seconds for events to drain...');
    await new Promise(resolve => setTimeout(resolve, 12000));

    const logContent = `Source ID: ${sourceId}
Fast Destination ID: ${fastDestId}
Slow Destination ID: ${slowDestId}
Fast Connection ID: ${fastConnId}
Slow Connection ID: ${slowConnId}
Published Events: 12
`;

    fs.writeFileSync('/home/user/hookdeck-fanout/output.log', logContent);
    console.log('Log written to /home/user/hookdeck-fanout/output.log');

  } catch (err) {
    console.error(err);
  }
}

main();
