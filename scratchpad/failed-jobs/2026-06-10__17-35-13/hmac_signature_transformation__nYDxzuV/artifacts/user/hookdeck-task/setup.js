const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function runCommand(command) {
  console.log(`Executing: ${command}`);
  try {
    const stdout = execSync(command, { encoding: "utf-8" });
    return JSON.parse(stdout);
  } catch (error) {
    console.error(`Error executing command: ${command}`);
    if (error.stdout) console.error(`stdout: ${error.stdout}`);
    if (error.stderr) console.error(`stderr: ${error.stderr}`);
    throw error;
  }
}

async function main() {
  const runId = process.env.ZEALT_RUN_ID;
  const hmacSecret = process.env.HMAC_SECRET;

  if (!runId) {
    console.error("Error: ZEALT_RUN_ID environment variable is not set.");
    process.exit(1);
  }
  if (!hmacSecret) {
    console.error("Error: HMAC_SECRET environment variable is not set.");
    process.exit(1);
  }

  console.log(`Run ID: ${runId}`);
  console.log(`HMAC Secret: [REDACTED]`);

  const transformName = `hmac-transform-${runId}`;
  const sourceName = `hmac-source-${runId}`;
  const destinationName = `hmac-dest-${runId}`;
  const connectionName = `hmac-connection-${runId}`;

  const transformJsPath = path.join(__dirname, "transform.js");

  // 1. Create Transformation
  console.log("Creating transformation...");
  const transformCmd = `hookdeck gateway transformation create --name "${transformName}" --code-file "${transformJsPath}" --env "HMAC_SECRET=${hmacSecret}" --output json`;
  const transformResult = runCommand(transformCmd);
  const transformId = transformResult.id;
  console.log(`Created Transformation ID: ${transformId}`);

  // 2. Create Source
  console.log("Creating source...");
  const sourceCmd = `hookdeck gateway source create --name "${sourceName}" --type WEBHOOK --output json`;
  const sourceResult = runCommand(sourceCmd);
  const sourceId = sourceResult.id;
  console.log(`Created Source ID: ${sourceId}`);

  // 3. Create Destination
  console.log("Creating destination...");
  const destCmd = `hookdeck gateway destination create --name "${destinationName}" --type MOCK_API --output json`;
  const destResult = runCommand(destCmd);
  const destId = destResult.id;
  console.log(`Created Destination ID: ${destId}`);

  // 4. Create Connection with Transformation
  console.log("Creating connection...");
  const connCmd = `hookdeck gateway connection create --name "${connectionName}" --source-id "${sourceId}" --destination-id "${destId}" --rule-transform-name "${transformName}" --output json`;
  const connResult = runCommand(connCmd);
  const connectionId = connResult.id;
  console.log(`Created Connection ID: ${connectionId}`);

  // 5. Write output.log
  const logContent = `Source ID: ${sourceId}\nConnection ID: ${connectionId}\n`;
  const logPath = path.join(__dirname, "output.log");
  fs.writeFileSync(logPath, logContent, "utf-8");
  console.log(`Successfully wrote output.log to ${logPath}`);
}

main().catch((err) => {
  console.error("Setup failed:", err);
  process.exit(1);
});
