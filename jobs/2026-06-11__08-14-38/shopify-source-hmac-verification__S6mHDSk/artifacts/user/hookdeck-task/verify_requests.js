const fs = require("fs");
const path = require("path");

const HOOKDECK_API_KEY = process.env.HOOKDECK_API_KEY;
const SOURCE_ID = "src_atuxgtvg9m8ntl";

if (!HOOKDECK_API_KEY) {
  console.error("Missing HOOKDECK_API_KEY env var!");
  process.exit(1);
}

async function verify() {
  console.log(`Fetching requests for Source ID: ${SOURCE_ID}...`);
  try {
    const res = await fetch(`https://api.hookdeck.com/2025-07-01/requests?source_id=${SOURCE_ID}`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${HOOKDECK_API_KEY}`,
      },
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to fetch requests: ${res.status} ${errText}`);
    }

    const data = await res.json();
    console.log("Requests received:", JSON.stringify(data, null, 2));

    const requests = data.models || [];
    console.log(`\nFound ${requests.length} requests.`);

    let verifiedCount = 0;
    let failedVerificationCount = 0;

    for (const req of requests) {
      console.log(`- Request ID: ${req.id}, Verified: ${req.verified}, Rejection Cause: ${req.rejection_cause}`);
      if (req.verified === true) {
        verifiedCount++;
      } else if (req.verified === false && req.rejection_cause === "VERIFICATION_FAILED") {
        failedVerificationCount++;
      }
    }

    console.log(`\nVerified true count: ${verifiedCount}`);
    console.log(`Failed verification count: ${failedVerificationCount}`);

    if (requests.length >= 2 && verifiedCount === 1 && failedVerificationCount >= 1) {
      console.log("\nAcceptance criteria met!");
      
      const logContent = `Source ID: ${SOURCE_ID}\n`;
      const logPath = "/home/user/hookdeck-task/output.log";
      fs.writeFileSync(logPath, logContent);
      console.log(`Wrote log to ${logPath}`);
    } else {
      console.log("\nAcceptance criteria NOT met yet. Retrying in a few seconds...");
    }
  } catch (err) {
    console.error("Error during verification:", err.message);
  }
}

verify();
