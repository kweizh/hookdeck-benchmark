const API_KEY = process.env.HOOKDECK_API_KEY;
const RUN_ID = process.env.ZEALT_RUN_ID;
const API_BASE = 'https://api.hookdeck.com/2025-07-01';

async function verify() {
  const sourceName = `bulk-source-${RUN_ID}`;
  const sourcesRes = await fetch(`${API_BASE}/sources?name=${sourceName}`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const sources = await sourcesRes.json();
  const sourceId = sources.models[0].id;

  const reqRes = await fetch(`${API_BASE}/requests?source_id=${sourceId}&include=data&limit=100`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
  const reqs = await reqRes.json();
  console.log('Total:', reqs.models.length);
  const bodies = reqs.models.map(r => r.data.body.i).sort((a,b) => a - b);
  console.log('Bodies:', bodies.join(','));
  const headers = reqs.models.filter(r => r.data.headers && r.data.headers['x-batch-id'] === 'BATCH-001');
  console.log('Headers count:', headers.length);
}
verify();
