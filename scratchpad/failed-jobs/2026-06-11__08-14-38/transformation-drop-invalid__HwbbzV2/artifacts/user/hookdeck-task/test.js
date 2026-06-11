const fs = require('fs');

const apiKey = process.env.HOOKDECK_API_KEY;

if (!apiKey) {
  console.error("Missing HOOKDECK_API_KEY environment variable.");
  process.exit(1);
}

const logPath = "/home/user/hookdeck-task/output.log";
if (!fs.existsSync(logPath)) {
  console.error(`Log file not found at ${logPath}`);
  process.exit(1);
}

const logContent = fs.readFileSync(logPath, 'utf8');
const sourceIdMatch = logContent.match(/Source ID:\s*(\S+)/);
const transIdMatch = logContent.match(/Transformation ID:\s*(\S+)/);

if (!sourceIdMatch || !transIdMatch) {
  console.error("Failed to parse Source ID or Transformation ID from output.log");
  process.exit(1);
}

const sourceId = sourceIdMatch[1];
const transId = transIdMatch[1];
const sourceUrl = `https://hkdk.events/${sourceId}`;

const apiBase = "https://api.hookdeck.com/2024-09-01";

async function sendWebhook(payload, description) {
  console.log(`Sending webhook (${description}) to ${sourceUrl}...`);
  const res = await fetch(sourceUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
  console.log(`Response status: ${res.status}`);
}

async function run() {
  try {
    // 1. Send test payloads
    await sendWebhook({
      user_id: "user_123",
      amount: 42.5
    }, "Valid Payload");

    await sendWebhook({
      user_id: "",
      amount: 42.5
    }, "Invalid Payload - empty user_id");

    await sendWebhook({
      user_id: "user_123",
      amount: "not-a-number"
    }, "Invalid Payload - string amount");

    // 2. Wait for executions to process
    console.log("Waiting 5 seconds for Hookdeck to process transformation executions...");
    await new Promise(resolve => setTimeout(resolve, 5000));

    // 3. Retrieve executions
    console.log("Retrieving transformation executions...");
    const execRes = await fetch(`${apiBase}/transformations/${transId}/executions`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });

    if (!execRes.ok) {
      const errText = await execRes.text();
      throw new Error(`Failed to fetch executions: ${execRes.status} ${errText}`);
    }

    const execData = await execRes.json();
    const executions = execData.models || [];
    console.log(`Found ${executions.length} executions.`);

    for (let i = 0; i < executions.length; i++) {
      const exec = executions[i];
      console.log(`\n--- Execution ${i + 1} (ID: ${exec.id}) ---`);
      console.log(`Status: ${exec.status}`);
      console.log(`Logs:`, JSON.stringify(exec.logs));
      console.log(`Original Event Data (first 200 chars):`, JSON.stringify(exec.original_event_data)?.substring(0, 200));
      console.log(`Transformed Event Data:`, JSON.stringify(exec.transformed_event_data));
    }

  } catch (error) {
    console.error("Error during testing:", error);
    process.exit(1);
  }
}

run();
