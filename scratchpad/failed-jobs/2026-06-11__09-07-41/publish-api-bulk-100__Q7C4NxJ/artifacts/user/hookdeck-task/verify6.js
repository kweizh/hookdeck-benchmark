const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID;
const API_BASE = 'https://api.hookdeck.com/2025-07-01';

async function verify() {
  const destName = `bulk-dest-${RUN_ID}`;
  const destsRes = await fetch(`${API_BASE}/destinations?name=${destName}`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const dests = await destsRes.json();
  const destId = dests.models[0].id;

  const evRes = await fetch(`${API_BASE}/events?destination_id=${destId}&status=SUCCESSFUL&limit=100`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const evs = await evRes.json();
  console.log('Successful events:', evs.models.length);
}
verify();
