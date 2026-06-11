const apiKey = process.env.HOOKDECK_API_KEY;
const runId = process.env.ZEALT_RUN_ID;

if (!apiKey || !runId) {
  console.error("Missing HOOKDECK_API_KEY or ZEALT_RUN_ID environment variables.");
  process.exit(1);
}

const sourceName = `bulk-source-${runId}`;
const destName = `bulk-dest-${runId}`;
const connName = `bulk-conn-${runId}`;

async function createConnection() {
  const url = "https://api.hookdeck.com/2025-07-01/connections";
  const body = {
    name: connName,
    source: {
      name: sourceName,
      type: "PUBLISH_API"
    },
    destination: {
      name: destName,
      type: "MOCK_API"
    }
  };

  console.log("Sending request to create connection...");
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify(body)
  });

  const responseText = await res.text();
  console.log(`Status: ${res.status} ${res.statusText}`);
  console.log(`Response: ${responseText}`);
  
  if (!res.ok) {
    throw new Error(`Failed to create connection: ${res.status} - ${responseText}`);
  }
}

createConnection().catch(err => {
  console.error(err);
  process.exit(1);
});
