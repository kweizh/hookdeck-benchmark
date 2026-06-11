const apiKey = process.env.HOOKDECK_API_KEY;
const runId = process.env.ZEALT_RUN_ID;

if (!apiKey || !runId) {
  console.error("Missing HOOKDECK_API_KEY or ZEALT_RUN_ID environment variables.");
  process.exit(1);
}

const sourceName = `bulk-source-${runId}`;
const publishUrl = "https://hkdk.events/v1/publish";

async function publishEvent(i) {
  const body = { i };
  const res = await fetch(publishUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
      "X-Hookdeck-Source-Name": sourceName,
      "x-batch-id": "BATCH-001"
    },
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to publish i=${i}: Status ${res.status} - ${text}`);
  }

  const data = await res.json();
  return { i, requestId: data.request_id };
}

async function run() {
  console.log(`Starting publish of 100 events to source: ${sourceName}`);
  const results = [];
  const batchSize = 10;

  for (let start = 0; start < 100; start += batchSize) {
    const batch = [];
    for (let i = start; i < start + batchSize && i < 100; i++) {
      batch.push(i);
    }

    console.log(`Publishing batch for i = ${batch[0]} to ${batch[batch.length - 1]}...`);
    const promises = batch.map(i => 
      publishEvent(i)
        .then(res => {
          console.log(`Successfully published i=${i}, Request ID: ${res.requestId}`);
          return res;
        })
        .catch(err => {
          console.error(`Error publishing i=${i}:`, err.message);
          throw err;
        })
    );

    const batchResults = await Promise.all(promises);
    results.push(...batchResults);

    // Minor delay between batches
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log(`Finished publishing 100 events. Total successful: ${results.length}`);
}

run().catch(err => {
  console.error("Publishing script failed:", err);
  process.exit(1);
});
