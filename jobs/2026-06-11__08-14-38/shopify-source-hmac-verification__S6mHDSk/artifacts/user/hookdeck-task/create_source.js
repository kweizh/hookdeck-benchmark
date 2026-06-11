const HOOKDECK_API_KEY = process.env.HOOKDECK_API_KEY;
const ZEALT_RUN_ID = process.env.ZEALT_RUN_ID;
const SHOPIFY_WEBHOOK_SECRET = process.env.SHOPIFY_WEBHOOK_SECRET;

if (!HOOKDECK_API_KEY || !ZEALT_RUN_ID || !SHOPIFY_WEBHOOK_SECRET) {
  console.error("Missing environment variables!");
  process.exit(1);
}

async function createSource() {
  const name = `shopify-verify-${ZEALT_RUN_ID}`;
  const payload = {
    name: name,
    type: "SHOPIFY",
    config: {
      auth_type: "SHOPIFY",
      auth: {
        webhook_secret_key: SHOPIFY_WEBHOOK_SECRET
      }
    }
  };

  try {
    const res = await fetch("https://api.hookdeck.com/2025-07-01/sources", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${HOOKDECK_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Failed to create source: ${res.status} ${errText}`);
    }

    const data = await res.json();
    console.log("SOURCE_CREATED_JSON=" + JSON.stringify(data));
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

createSource();
