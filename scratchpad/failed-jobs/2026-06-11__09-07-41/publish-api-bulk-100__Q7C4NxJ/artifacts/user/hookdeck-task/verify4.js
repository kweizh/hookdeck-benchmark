const API_KEY = process.env.HOOKDECK_API_KEY;
const API_BASE = 'https://api.hookdeck.com/2025-07-01';

async function verify() {
  const reqRes = await fetch(`${API_BASE}/events?limit=1`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const reqs = await reqRes.json();
  console.log(JSON.stringify(reqs.models[0], null, 2));
}
verify();
