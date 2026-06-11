const fs = require('fs');
const path = require('path');

const runId = process.env.ZEALT_RUN_ID;
const apiKey = process.env.HOOKDECK_API_KEY;

if (!runId || !apiKey) {
  console.error("Missing ZEALT_RUN_ID or HOOKDECK_API_KEY environment variables.");
  process.exit(1);
}

const apiBase = "https://api.hookdeck.com/2024-09-01";

async function cleanUp() {
  console.log("Starting clean-up of existing resources...");

  // 1. Clean Connections
  const connRes = await fetch(`${apiBase}/connections`, {
    headers: { 'Authorization': `Bearer ${apiKey}` }
  });
  if (connRes.ok) {
    const data = await connRes.json();
    const existingConns = data.models || [];
    for (const conn of existingConns) {
      if (conn.name === `conn-${runId}`) {
        console.log(`Deleting existing connection: ${conn.id}`);
        await fetch(`${apiBase}/connections/${conn.id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
      }
    }
  }

  // 2. Clean Sources
  const srcRes = await fetch(`${apiBase}/sources`, {
    headers: { 'Authorization': `Bearer ${apiKey}` }
  });
  if (srcRes.ok) {
    const data = await srcRes.json();
    const existingSrcs = data.models || [];
    for (const src of existingSrcs) {
      if (src.name === `src-${runId}`) {
        console.log(`Deleting existing source: ${src.id}`);
        await fetch(`${apiBase}/sources/${src.id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
      }
    }
  }

  // 3. Clean Destinations
  const destRes = await fetch(`${apiBase}/destinations`, {
    headers: { 'Authorization': `Bearer ${apiKey}` }
  });
  if (destRes.ok) {
    const data = await destRes.json();
    const existingDests = data.models || [];
    for (const dest of existingDests) {
      if (dest.name === `dst-${runId}`) {
        console.log(`Deleting existing destination: ${dest.id}`);
        await fetch(`${apiBase}/destinations/${dest.id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
      }
    }
  }

  // 4. Clean Transformations
  const transRes = await fetch(`${apiBase}/transformations`, {
    headers: { 'Authorization': `Bearer ${apiKey}` }
  });
  if (transRes.ok) {
    const data = await transRes.json();
    const existingTrans = data.models || [];
    for (const trans of existingTrans) {
      if (trans.name === `validate-${runId}`) {
        console.log(`Deleting existing transformation: ${trans.id}`);
        await fetch(`${apiBase}/transformations/${trans.id}`, {
          method: 'DELETE',
          headers: { 'Authorization': `Bearer ${apiKey}` }
        });
      }
    }
  }

  console.log("Clean-up completed.");
}

async function run() {
  try {
    console.log(`Starting Hookdeck provisioning for Run ID: ${runId}`);

    // Clean up first to ensure idempotency
    await cleanUp();

    // 1. Create Source
    const sourceName = `src-${runId}`;
    console.log(`Creating source: ${sourceName}...`);
    const sourceRes = await fetch(`${apiBase}/sources`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: sourceName
      })
    });

    if (!sourceRes.ok) {
      const errText = await sourceRes.text();
      throw new Error(`Failed to create source: ${sourceRes.status} ${errText}`);
    }

    const sourceData = await sourceRes.json();
    const sourceId = sourceData.id;
    console.log(`Created Source ID: ${sourceId}`);

    // 2. Create Destination
    const destName = `dst-${runId}`;
    console.log(`Creating destination: ${destName}...`);
    const destRes = await fetch(`${apiBase}/destinations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: destName,
        url: "https://mock.hookdeck.com"
      })
    });

    if (!destRes.ok) {
      const errText = await destRes.text();
      throw new Error(`Failed to create destination: ${destRes.status} ${errText}`);
    }

    const destData = await destRes.json();
    const destId = destData.id;
    console.log(`Created Destination ID: ${destId}`);

    // 3. Create Transformation
    const transformName = `validate-${runId}`;
    const transformCode = `addHandler("transform", (request, context) => {
  const body = request.body;
  if (!body || typeof body !== "object") {
    console.log("validation_failed: user_id");
    return null;
  }
  if (typeof body.user_id !== "string" || body.user_id.trim() === "") {
    console.log("validation_failed: user_id");
    return null;
  }
  if (typeof body.amount !== "number" || !Number.isFinite(body.amount)) {
    console.log("validation_failed: amount");
    return null;
  }
  return request;
});`;

    console.log(`Creating transformation: ${transformName}...`);
    const transformRes = await fetch(`${apiBase}/transformations`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: transformName,
        code: transformCode
      })
    });

    if (!transformRes.ok) {
      const errText = await transformRes.text();
      throw new Error(`Failed to create transformation: ${transformRes.status} ${errText}`);
    }

    const transformData = await transformRes.json();
    const transformationId = transformData.id;
    console.log(`Created Transformation ID: ${transformationId}`);

    // 4. Create Connection
    const connName = `conn-${runId}`;
    console.log(`Creating connection: ${connName}...`);
    const connRes = await fetch(`${apiBase}/connections`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: connName,
        source_id: sourceId,
        destination_id: destId,
        rules: [
          {
            type: "transform",
            transformation_id: transformationId
          }
        ]
      })
    });

    if (!connRes.ok) {
      const errText = await connRes.text();
      throw new Error(`Failed to create connection: ${connRes.status} ${errText}`);
    }

    const connData = await connRes.json();
    console.log(`Created Connection ID: ${connData.id}`);

    // 5. Write output.log
    const logPath = "/home/user/hookdeck-task/output.log";
    const logContent = `Source ID: ${sourceId}\nTransformation ID: ${transformationId}\n`;
    fs.writeFileSync(logPath, logContent);
    console.log(`Successfully wrote log to ${logPath}`);

  } catch (error) {
    console.error("Error during provisioning:", error);
    process.exit(1);
  }
}

run();
