const https = require('https');
const API_KEY = process.env.HOOKDECK_API_KEY;

function req(path) {
  return new Promise((resolve, reject) => {
    https.get(`https://api.hookdeck.com/2024-09-01${path}`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` }
    }, res => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => resolve(JSON.parse(body)));
    });
  });
}

async function main() {
  const events = await req('/events?request_id=req_UJh95v8E7c9B8poQjL4c');
  const event = events.models[0];
  console.log('Event Data ID:', event.event_data_id);
  
  const data = await req(`/events/data/${event.event_data_id}`);
  console.log('Headers:', data.headers);
}
main();
