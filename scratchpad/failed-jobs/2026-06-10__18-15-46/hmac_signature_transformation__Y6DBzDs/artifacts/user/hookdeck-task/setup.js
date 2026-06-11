const { execSync } = require('child_process');
const fs = require('fs');

const RUN_ID = process.env.ZEALT_RUN_ID;
const SOURCE_NAME = `hmac-source-${RUN_ID}`;
const DEST_NAME = `hmac-dest-${RUN_ID}`;
const CONNECTION_NAME = `hmac-connection-${RUN_ID}`;
const TRANSFORM_NAME = `hmac-transform-${RUN_ID}`;
const HMAC_SECRET_VALUE = 'hmac-secret-key-12345';

const TRANSFORMATION_CODE = `addHandler("transform", (request, context) => {
  const signature = crypto.createHmac('sha256', env.HMAC_SECRET).update(JSON.stringify(request.body)).digest('hex');
  request.headers['x-hmac-signature'] = signature;
  return request;
});`;

const LOG_FILE = '/home/user/hookdeck-task/output.log';

function runCLI(cmd, ignoreError = false) {
  try {
    const result = execSync(cmd, { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] });
    return result.trim();
  } catch (e) {
    if (ignoreError) {
      return null;
    }
    throw e;
  }
}

function log(msg) {
  console.log(msg);
  fs.appendFileSync(LOG_FILE, msg + '\n');
}

// Clear log file
fs.writeFileSync(LOG_FILE, '');

// Step 1: Authenticate
log('Authenticating with Hookdeck CLI...');
runCLI(`hookdeck ci --api-key ${process.env.HOOKDECK_API_KEY}`);

// Step 2: Create Source
log('Creating source...');
const sourceOutput = runCLI(`hookdeck gateway source create --name "${SOURCE_NAME}" --type WEBHOOK --output json`);
const sourceData = JSON.parse(sourceOutput);
const sourceId = sourceData.id;
log(`Source ID: ${sourceId}`);

// Step 3: Create Destination (MOCK_API)
log('Creating destination...');
const destOutput = runCLI(`hookdeck gateway destination create --name "${DEST_NAME}" --type MOCK_API --output json`);
const destData = JSON.parse(destOutput);
const destId = destData.id;
log(`Destination ID: ${destId}`);

// Step 4: Create Transformation
log('Creating transformation...');
// Write transformation code to a temp file to avoid shell escaping issues
const tmpCodeFile = '/tmp/transform_code.js';
fs.writeFileSync(tmpCodeFile, TRANSFORMATION_CODE);

const transformOutput = runCLI(`hookdeck gateway transformation create --name "${TRANSFORM_NAME}" --code-file "${tmpCodeFile}" --env HMAC_SECRET=${HMAC_SECRET_VALUE} --output json`);
const transformData = JSON.parse(transformOutput);
const transformId = transformData.id;
log(`Transformation ID: ${transformId}`);

// Step 5: Create Connection
log('Creating connection...');
const connectionOutput = runCLI(`hookdeck gateway connection create --name "${CONNECTION_NAME}" --source-id ${sourceId} --destination-id ${destId} --rule-transform-name "${TRANSFORM_NAME}" --output json`);
const connectionData = JSON.parse(connectionOutput);
const connectionId = connectionData.id;
log(`Connection ID: ${connectionId}`);

// Clean up temp file
try { fs.unlinkSync(tmpCodeFile); } catch(e) {}

log('\nSetup complete!');
log(`Source: ${SOURCE_NAME} (${sourceId})`);
log(`Destination: ${DEST_NAME} (${destId})`);
log(`Transformation: ${TRANSFORM_NAME} (${transformId})`);
log(`Connection: ${CONNECTION_NAME} (${connectionId})`);