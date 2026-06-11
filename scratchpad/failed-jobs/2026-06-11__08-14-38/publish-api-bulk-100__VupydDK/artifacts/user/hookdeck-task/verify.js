const apiKey = process.env.HOOKDECK_API_KEY;
const runId = process.env.ZEALT_RUN_ID;

if (!apiKey || !runId) {
  console.error("Missing HOOKDECK_API_KEY or ZEALT_RUN_ID environment variables.");
  process.exit(1);
}

const sourceId = "src_2qt8dcr5rj6080"; // Handled dynamically if we want, but we can also fetch it by name or use the ID we know.
const sourceName = `bulk-source-${runId}`;

async function getSourceId() {
  const url = `https://api.hookdeck.com/2025-07-01/sources`;
  const res = await fetch(url, {
    headers: { "Authorization": `Bearer ${apiKey}` }
  });
  const data = await res.json();
  const source = data.models.find(s => s.name === sourceName);
  if (!source) {
    throw new Error(`Source not found: ${sourceName}`);
  }
  return source.id;
}

async function verify() {
  const sId = await getSourceId();
  console.log(`Using Source ID: ${sId} for verification.`);

  // Fetch all events for this source
  let url = `https://api.hookdeck.com/2025-07-01/events?source_id=${sId}&limit=100`;
  let allEvents = [];
  
  while (url) {
    const res = await fetch(url, {
      headers: { "Authorization": `Bearer ${apiKey}` }
    });
    const data = await res.json();
    allEvents.push(...data.models);
    
    if (data.pagination && data.pagination.next) {
      url = `https://api.hookdeck.com/2025-07-01/events?source_id=${sId}&limit=100&next=${data.pagination.next}`;
    } else {
      url = null;
    }
  }

  console.log(`Total events fetched: ${allEvents.length}`);

  // Fetch full details for each event to get body and headers
  const batchSize = 10;
  const verifiedEvents = [];
  
  for (let start = 0; start < allEvents.length; start += batchSize) {
    const batch = allEvents.slice(start, start + batchSize);
    const promises = batch.map(async (evt) => {
      const detailUrl = `https://api.hookdeck.com/2025-07-01/events/${evt.id}`;
      const res = await fetch(detailUrl, {
        headers: { "Authorization": `Bearer ${apiKey}` }
      });
      if (!res.ok) {
        throw new Error(`Failed to fetch event details for ${evt.id}`);
      }
      return await res.json();
    });
    
    const details = await Promise.all(promises);
    verifiedEvents.push(...details);
    console.log(`Fetched details for ${verifiedEvents.length}/${allEvents.length} events...`);
  }

  // Verify the requirements
  let successfulCount = 0;
  let batchIdCount = 0;
  const receivedValues = new Set();
  const duplicateValues = [];
  const extraValues = [];

  for (const evt of verifiedEvents) {
    if (evt.status === "SUCCESSFUL") {
      successfulCount++;
    }

    const headers = evt.data?.headers || {};
    // Header keys are case-insensitive, but Hookdeck usually normalizes them or returns them as they were sent.
    // Let's check both 'x-batch-id' and 'X-Batch-Id'.
    const batchId = headers["x-batch-id"] || headers["X-Batch-ID"] || headers["X-Batch-Id"];
    if (batchId === "BATCH-001") {
      batchIdCount++;
    }

    const body = evt.data?.body;
    if (body && typeof body.i === "number") {
      const val = body.i;
      if (val >= 0 && val < 100) {
        if (receivedValues.has(val)) {
          duplicateValues.push(val);
        } else {
          receivedValues.add(val);
        }
      } else {
        extraValues.push(val);
      }
    }
  }

  console.log("\n--- VERIFICATION RESULTS ---");
  console.log(`SUCCESSFUL Status Count: ${successfulCount}`);
  console.log(`x-batch-id: BATCH-001 Count: ${batchIdCount}`);
  console.log(`Unique values count (0-99): ${receivedValues.size}`);
  console.log(`Duplicate values:`, duplicateValues);
  console.log(`Extra values:`, extraValues);

  const missingValues = [];
  for (let i = 0; i < 100; i++) {
    if (!receivedValues.has(i)) {
      missingValues.push(i);
    }
  }
  console.log(`Missing values:`, missingValues);

  if (
    successfulCount === 100 &&
    batchIdCount === 100 &&
    receivedValues.size === 100 &&
    duplicateValues.length === 0 &&
    extraValues.length === 0 &&
    missingValues.length === 0
  ) {
    console.log("\n✅ ALL ACCEPTANCE CRITERIA MET SUCCESSFULLY!");
  } else {
    console.log("\n❌ SOME CRITERIA FAILED!");
    process.exit(1);
  }
}

verify().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
