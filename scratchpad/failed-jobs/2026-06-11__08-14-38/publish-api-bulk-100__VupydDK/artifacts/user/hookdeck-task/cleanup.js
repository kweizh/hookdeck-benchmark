const apiKey = process.env.HOOKDECK_API_KEY;
const runId = process.env.ZEALT_RUN_ID;

if (!apiKey || !runId) {
  console.error("Missing HOOKDECK_API_KEY or ZEALT_RUN_ID environment variables.");
  process.exit(1);
}

const sourceName = `bulk-source-${runId}`;
const destName = `bulk-dest-${runId}`;
const connName = `bulk-conn-${runId}`;

async function cleanupAndRecreate() {
  // 1. Get existing connection, source, destination
  console.log("Fetching existing resources...");
  
  // Connections
  const connRes = await fetch("https://api.hookdeck.com/2025-07-01/connections", {
    headers: { "Authorization": `Bearer ${apiKey}` }
  });
  const connData = await connRes.json();
  const connection = connData.models.find(c => c.name === connName);

  // Sources
  const srcRes = await fetch("https://api.hookdeck.com/2025-07-01/sources", {
    headers: { "Authorization": `Bearer ${apiKey}` }
  });
  const srcData = await srcRes.json();
  const source = srcData.models.find(s => s.name === sourceName);

  // Destinations
  const destRes = await fetch("https://api.hookdeck.com/2025-07-01/destinations", {
    headers: { "Authorization": `Bearer ${apiKey}` }
  });
  const destData = await destRes.json();
  const destination = destData.models.find(d => d.name === destName);

  // 2. Delete Connection
  if (connection) {
    console.log(`Deleting Connection: ${connection.id}...`);
    const delConn = await fetch(`https://api.hookdeck.com/2025-07-01/connections/${connection.id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${apiKey}` }
    });
    console.log(`Delete Connection Status: ${delConn.status}`);
  }

  // 3. Delete Source
  if (source) {
    console.log(`Deleting Source: ${source.id}...`);
    const delSrc = await fetch(`https://api.hookdeck.com/2025-07-01/sources/${source.id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${apiKey}` }
    });
    console.log(`Delete Source Status: ${delSrc.status}`);
  }

  // 4. Delete Destination
  if (destination) {
    console.log(`Deleting Destination: ${destination.id}...`);
    const delDest = await fetch(`https://api.hookdeck.com/2025-07-01/destinations/${destination.id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${apiKey}` }
    });
    console.log(`Delete Destination Status: ${delDest.status}`);
  }

  console.log("Cleanup completed!");
}

cleanupAndRecreate().catch(console.error);
