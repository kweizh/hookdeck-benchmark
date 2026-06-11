const http = require('http');
const { execSync, spawn } = require('child_process');

const RUN_ID = process.env.ZEALT_RUN_ID;
const SOURCE_NAME = `cli-replay-${RUN_ID}`.toLowerCase();
const API_KEY = process.env.HOOKDECK_API_KEY;
const LOG_FILE = '/home/user/project/output.log';

let requestCount = 0;

// Helper: HTTP request
function httpRequest(options, body) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

// Helper: HTTPS request (for Hookdeck API)
function httpsRequest(url, method, headers, body) {
  const https = require('https');
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: 443,
      path: urlObj.pathname + urlObj.search,
      method: method,
      headers: headers
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ statusCode: res.statusCode, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log('=== Starting Hookdeck CLI Replay Workflow ===');
  console.log('Source Name:', SOURCE_NAME);

  // Step 1: Start local HTTP server
  const server = http.createServer((req, res) => {
    if (req.method === 'POST' && req.url === '/hooks') {
      requestCount++;
      let body = '';
      req.on('data', chunk => { body += chunk; });
      req.on('end', () => {
        console.log(`Request #${requestCount} to POST /hooks`);
        if (requestCount === 1) {
          console.log('Returning 500 (first request)');
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Internal Server Error' }));
        } else {
          console.log('Returning 200 (subsequent request)');
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ received: true }));
        }
      });
    } else {
      res.writeHead(404);
      res.end('Not found');
    }
  });

  await new Promise(resolve => server.listen(3000, resolve));
  console.log('Server listening on port 3000');

  // Step 2: Authenticate Hookdeck CLI
  console.log('Authenticating Hookdeck CLI...');
  try {
    execSync('hookdeck ci', {
      env: { ...process.env, HOOKDECK_API_KEY: API_KEY },
      stdio: 'inherit'
    });
  } catch (e) {
    console.log('CI auth may have already been done, continuing...');
  }

  // Step 3: Start hookdeck listen in background
  console.log('Starting hookdeck listen...');
  const listenProcess = spawn('hookdeck', [
    'listen', '3000', SOURCE_NAME,
    '--path', '/hooks',
    '--output', 'quiet'
  ], {
    env: { ...process.env, HOOKDECK_API_KEY: API_KEY },
    stdio: 'pipe'
  });

  listenProcess.stdout.on('data', (data) => {
    console.log('[listen stdout]', data.toString());
  });
  listenProcess.stderr.on('data', (data) => {
    console.log('[listen stderr]', data.toString());
  });

  // Wait for connection to be established
  console.log('Waiting for connection to be established...');
  await sleep(15);

  // Step 4: Get connection info
  console.log('Fetching connection info...');
  const connResponse = await httpsRequest(
    `https://api.hookdeck.com/connections?source_name=${encodeURIComponent(SOURCE_NAME)}`,
    'GET',
    {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    null
  );
  console.log('Connection response:', connResponse.body);

  const connData = JSON.parse(connResponse.body);
  const connections = connData.models || connData.data || [];
  const connectionId = connections.length > 0 ? connections[0].id : '';
  console.log('Connection ID:', connectionId);

  // Step 5: Publish event
  console.log('Publishing event...');
  const publishPayload = JSON.stringify({ test: 'data', message: 'hello from cli replay' });
  const publishResponse = await httpsRequest(
    'https://hkdk.events/v1/publish',
    'POST',
    {
      'Authorization': `Bearer ${API_KEY}`,
      'X-Hookdeck-Source-Name': SOURCE_NAME,
      'Content-Type': 'application/json'
    },
    publishPayload
  );
  console.log('Publish response:', publishResponse.body);

  const publishData = JSON.parse(publishResponse.body);
  const eventId = publishData.id || publishData.event_id || '';
  console.log('Event ID:', eventId);

  // Step 6: Wait for first delivery to fail
  console.log('Waiting for first delivery attempt to fail...');
  await sleep(10);

  // Check event status after first attempt
  let eventCheck = await httpsRequest(
    `https://api.hookdeck.com/events/${eventId}`,
    'GET',
    {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    null
  );
  console.log('Event status after first attempt:', eventCheck.body);

  // Step 7: Retry the event
  console.log('Retrying event...');
  const retryResponse = await httpsRequest(
    `https://api.hookdeck.com/events/${eventId}/retry`,
    'POST',
    {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    null
  );
  console.log('Retry response:', retryResponse.body);

  const retryData = JSON.parse(retryResponse.body);
  const retryEventId = retryData.id || '';
  console.log('Retry Response Event ID:', retryEventId);

  // Step 8: Poll until SUCCESSFUL with attempts == 2
  console.log('Polling for successful delivery...');
  let finalStatus = '';
  let finalAttempts = 0;

  for (let i = 0; i < 30; i++) {
    console.log(`Poll ${i + 1}: Checking event status...`);
    
    eventCheck = await httpsRequest(
      `https://api.hookdeck.com/events/${eventId}`,
      'GET',
      {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json'
      },
      null
    );

    const eventData = JSON.parse(eventCheck.body);
    const status = eventData.status || '';
    const attempts = eventData.attempts || 0;

    console.log(`  Status: ${status}, Attempts: ${attempts}`);

    if (status === 'SUCCESSFUL' && attempts === 2) {
      finalStatus = status;
      finalAttempts = attempts;
      console.log('Success! Event delivered successfully after retry.');
      break;
    }

    if (i === 29) {
      finalStatus = status;
      finalAttempts = attempts;
      console.log(`Warning: Max polls reached. Last status: ${status}, attempts: ${attempts}`);
    }

    await sleep(5);
  }

  // Step 9: Write output.log
  console.log('Writing output.log...');
  const logContent = [
    `Source Name: ${SOURCE_NAME}`,
    `Connection ID: ${connectionId}`,
    `Event ID: ${eventId}`,
    `Retry Response Event ID: ${retryEventId}`,
    `Final Status: ${finalStatus}`,
    `Final Attempts: ${finalAttempts}`
  ].join('\n') + '\n';

  require('fs').writeFileSync(LOG_FILE, logContent);
  console.log('=== Output Log ===');
  console.log(logContent);

  // Cleanup
  console.log('Cleaning up...');
  listenProcess.kill();
  server.close();

  console.log('=== Workflow Complete ===');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});