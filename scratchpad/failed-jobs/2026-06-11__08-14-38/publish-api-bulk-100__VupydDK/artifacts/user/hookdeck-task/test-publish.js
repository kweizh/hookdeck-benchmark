const apiKey = process.env.HOOKDECK_API_KEY;
const runId = process.env.ZEALT_RUN_ID;

if (!apiKey || !runId) {
  console.error("Missing HOOKDECK_API_KEY or ZEALT_RUN_ID environment variables.");
  process.exit(1);
}

const sourceName = `bulk-source-${runId}`;

async function testPublish() {
  const publishUrl = "https://hkdk.events/v1/publish";

  console.log("Publishing Style A (direct JSON)...");
  const resA = await fetch(publishUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
      "X-Hookdeck-Source-Name": sourceName,
      "x-batch-id": "BATCH-TEST-A"
    },
    body: JSON.stringify({ i: 999 })
  });
  console.log(`Style A Publish Status: ${resA.status} ${resA.statusText}`);
  try {
    console.log(`Style A Response:`, await resA.text());
  } catch (e) {}

  console.log("Publishing Style B (nested data)...");
  const resB = await fetch(publishUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
      "X-Hookdeck-Source-Name": sourceName,
      "x-batch-id": "BATCH-TEST-B"
    },
    body: JSON.stringify({ data: { i: 888 } })
  });
  console.log(`Style B Publish Status: ${resB.status} ${resB.statusText}`);
  try {
    console.log(`Style B Response:`, await resB.text());
  } catch (e) {}

  // Wait 3 seconds for ingestion
  console.log("Waiting 3 seconds for ingestion...");
  await new Promise(resolve => setTimeout(resolve, 3000));

  // Retrieve requests/events via REST API
  console.log("Fetching requests from REST API...");
  const inspectUrl = `https://api.hookdeck.com/2025-07-01/requests?source_id=src_2qt8dcr5rj6080`; // Let's get by source_id
  const inspectRes = await fetch(inspectUrl, {
    headers: {
      "Authorization": `Bearer ${apiKey}`
    }
  });

  const inspectData = await inspectRes.json();
  console.log("Requests count:", inspectData.models ? inspectData.models.length : "unknown");
  if (inspectData.models) {
    for (const req of inspectData.models) {
      console.log("-----------------------------------------");
      console.log("Request ID:", req.id);
      console.log("Headers:", JSON.stringify(req.headers));
      console.log("Body:", JSON.stringify(req.body));
      console.log("Original Body (if any):", req.original_body);
    }
  }
}

testPublish().catch(console.error);
