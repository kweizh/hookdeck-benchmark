#!/usr/bin/env node
/**
 * Hookdeck HMAC Signature Transformation Setup Script
 *
 * Creates:
 *  - A source named hmac-source-${ZEALT_RUN_ID}
 *  - A MOCK destination named hmac-dest-${ZEALT_RUN_ID}
 *  - A transformation that computes HMAC-SHA256 of the request body
 *    and attaches it as the x-hmac-signature header
 *  - A connection linking the above source → transformation → destination
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const API_KEY    = process.env.HOOKDECK_API_KEY;
const RUN_ID     = process.env.ZEALT_RUN_ID;
const HMAC_SECRET = process.env.HMAC_SECRET;
const LOG_FILE   = path.join(__dirname, 'output.log');

if (!API_KEY)     { console.error('HOOKDECK_API_KEY is not set'); process.exit(1); }
if (!RUN_ID)      { console.error('ZEALT_RUN_ID is not set');    process.exit(1); }
if (!HMAC_SECRET) { console.error('HMAC_SECRET is not set');     process.exit(1); }

const SOURCE_NAME    = `hmac-source-${RUN_ID}`;
const DEST_NAME      = `hmac-dest-${RUN_ID}`;
const CONN_NAME      = `hmac-connection-${RUN_ID}`;
const TRANSFORM_NAME = `hmac-transform-${RUN_ID}`;

function log(msg) {
  console.log(msg);
  fs.appendFileSync(LOG_FILE, msg + '\n');
}

function apiRequest(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: `/latest${urlPath}`,
      method,
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
        ...(data ? { 'Content-Length': Buffer.byteLength(data) } : {}),
      },
    };

    const req = https.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => { responseData += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(responseData);
          if (res.statusCode >= 400) {
            reject(new Error(`API error ${res.statusCode} on ${method} ${urlPath}: ${responseData}`));
          } else {
            resolve(parsed);
          }
        } catch (e) {
          reject(new Error(`Failed to parse response (${res.statusCode}): ${responseData}`));
        }
      });
    });

    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function main() {
  // Clear (or create) log file
  fs.writeFileSync(LOG_FILE, '');

  log(`Setting up Hookdeck resources for run: ${RUN_ID}`);
  log(`Source name:      ${SOURCE_NAME}`);
  log(`Destination name: ${DEST_NAME}`);
  log(`Connection name:  ${CONN_NAME}`);
  log(`Transform name:   ${TRANSFORM_NAME}`);
  log('');

  // ── 1. Create Source ──────────────────────────────────────────────────────
  log('Creating source...');
  const source = await apiRequest('POST', '/sources', {
    name: SOURCE_NAME,
    type: 'WEBHOOK',
    config: {
      allowed_http_methods: ['POST', 'PUT', 'PATCH', 'DELETE'],
    },
  });
  log(`Source created → ID: ${source.id}  URL: ${source.url}`);

  // ── 2. Create MOCK Destination ────────────────────────────────────────────
  log('\nCreating mock destination...');
  const destination = await apiRequest('POST', '/destinations', {
    name: DEST_NAME,
    type: 'MOCK_API',
  });
  log(`Destination created → ID: ${destination.id}  Name: ${destination.name}`);

  // ── 3. Create Transformation ──────────────────────────────────────────────
  log('\nCreating transformation...');

  // The transformation code runs inside a Hookdeck V8 isolate.
  // `addHandler('transform', fn)` is the required entry point.
  // `env` contains the environment variables configured on the transformation.
  const transformCode = [
    "addHandler('transform', function(request, context) {",
    "  var crypto = require('crypto');",
    "  var secret = env.HMAC_SECRET;",
    "  var body = JSON.stringify(request.body);",
    "  var signature = crypto.createHmac('sha256', secret).update(body).digest('hex');",
    "  request.headers['x-hmac-signature'] = signature;",
    "  return request;",
    "});",
  ].join('\n');

  const transformation = await apiRequest('POST', '/transformations', {
    name: TRANSFORM_NAME,
    code: transformCode,
    env: {
      HMAC_SECRET: HMAC_SECRET,
    },
  });
  log(`Transformation created → ID: ${transformation.id}  Name: ${transformation.name}`);

  // ── 4. Create Connection ──────────────────────────────────────────────────
  // The connection must include:
  //   - source: { id, name }   (both required by the API)
  //   - destination: { id, name }
  //   - rules: [{ type: 'transform', transformation_id: ... }]
  log('\nCreating connection...');
  const connection = await apiRequest('POST', '/connections', {
    name: CONN_NAME,
    source: {
      id: source.id,
      name: source.name,
    },
    destination: {
      id: destination.id,
      name: destination.name,
    },
    rules: [
      {
        type: 'transform',
        transformation_id: transformation.id,
      },
    ],
  });
  log(`Connection created → ID: ${connection.id}  Name: ${connection.name}`);

  // ── Summary ───────────────────────────────────────────────────────────────
  log('\n========== Setup Complete ==========');
  log(`Source ID: ${source.id}`);
  log(`Destination ID: ${destination.id}`);
  log(`Transformation ID: ${transformation.id}`);
  log(`Connection ID: ${connection.id}`);
  log('====================================');
}

main().catch((err) => {
  const msg = `Setup failed: ${err.message}`;
  console.error(msg);
  fs.appendFileSync(LOG_FILE, `ERROR: ${msg}\n`);
  process.exit(1);
});
