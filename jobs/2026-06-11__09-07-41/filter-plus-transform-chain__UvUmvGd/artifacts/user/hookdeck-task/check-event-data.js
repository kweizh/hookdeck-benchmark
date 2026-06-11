const https = require('https');
const API_KEY = process.env.HOOKDECK_API_KEY;

function request(method, path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: '/2025-07-01' + path,
      method,
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    };
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve(JSON.parse(body)));
    });
    req.on('error', reject);
    req.end();
  });
}

async function main() {
  const dests = await request('GET', `/destinations?name=chain-dest-zr-uvumvgd`);
  if (dests.models && dests.models.length > 0) {
    const destId = dests.models[0].id;
    const events = await request('GET', `/events?destination_id=${destId}`);
    for (const ev of events.models) {
       const reqData = await request('GET', `/requests/${ev.request_id}`);
       console.log('Request id:', ev.request_id);
       console.log('Request ignored_count:', reqData.ignored_count);
       // The transformed data is in the event, not the original request.
       // We can get the event data by ID? Or get the event itself.
       // Hookdeck API: GET /events/{id} might not return data. GET /events/{id}/data ?
       const eventData = await request('GET', `/events/${ev.id}`);
       console.log('Event Data:', JSON.stringify(eventData, null, 2));
    }
  }
}
main();
