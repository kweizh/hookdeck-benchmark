/**
 * Hookdeck Transformation Setup
 * Run ID: zr-wanskaq
 *
 * Resources created:
 *   Source:          transform-source-zr-wanskaq  (src_bm778qlb1jrtxl)
 *   Destination:     transform-dest-zr-wanskaq    (des_jgen9iA5xXvk)  [MOCK_API]
 *   Transformation:  transform-zr-wanskaq         (trs_pqGz1rR8nXMztT)
 *   Connection:      transform-conn-zr-wanskaq    (web_epqYE64HWewR)
 *
 * The transformation renames `customer_id` -> `userId` in the request body
 * and adds the header `x-custom-transformed: true`.
 */

const API_KEY = process.env.HOOKDECK_API_KEY;
const BASE_URL = "https://api.hookdeck.com/2024-09-01";
const RUN_ID = process.env.ZEALT_RUN_ID;

// JavaScript transformation code applied to the connection rule
const TRANSFORMATION_CODE = `addHandler("transform", (request, context) => {
  // Rename customer_id -> userId
  if (request.body && typeof request.body === 'object' && !Array.isArray(request.body)) {
    if ('customer_id' in request.body) {
      request.body.userId = request.body.customer_id;
      delete request.body.customer_id;
    }
  }

  // Add x-custom-transformed header
  if (!request.headers) {
    request.headers = {};
  }
  request.headers['x-custom-transformed'] = 'true';

  return request;
});`;

async function createResources() {
  const headers = {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json",
  };

  // 1. Create Source
  const sourceRes = await fetch(`${BASE_URL}/sources`, {
    method: "POST",
    headers,
    body: JSON.stringify({ name: `transform-source-${RUN_ID}`, type: "WEBHOOK" }),
  });
  const source = await sourceRes.json();
  console.log("Source:", source.id, source.name);

  // 2. Create Destination (MOCK_API)
  const destRes = await fetch(`${BASE_URL}/destinations`, {
    method: "POST",
    headers,
    body: JSON.stringify({ name: `transform-dest-${RUN_ID}`, type: "MOCK_API", url: "https://mock.hookdeck.com" }),
  });
  const dest = await destRes.json();
  console.log("Destination:", dest.id, dest.name);

  // 3. Create Transformation
  const transformRes = await fetch(`${BASE_URL}/transformations`, {
    method: "POST",
    headers,
    body: JSON.stringify({ name: `transform-${RUN_ID}`, code: TRANSFORMATION_CODE }),
  });
  const transform = await transformRes.json();
  console.log("Transformation:", transform.id, transform.name);

  // 4. Create Connection with transformation rule
  const connRes = await fetch(`${BASE_URL}/connections`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: `transform-conn-${RUN_ID}`,
      source_id: source.id,
      destination_id: dest.id,
      rules: [{ type: "transform", transformation_id: transform.id }],
    }),
  });
  const conn = await connRes.json();
  console.log("Connection:", conn.id, conn.name);
  console.log("Rules:", JSON.stringify(conn.rules));
}

createResources().catch(console.error);
