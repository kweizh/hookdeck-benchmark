const crypto = require("crypto");

const SHOPIFY_WEBHOOK_SECRET = process.env.SHOPIFY_WEBHOOK_SECRET;
const SOURCE_URL = "https://hkdk.events/atuxgtvg9m8ntl";

if (!SHOPIFY_WEBHOOK_SECRET) {
  console.error("Missing SHOPIFY_WEBHOOK_SECRET environment variable!");
  process.exit(1);
}

const bodyObj = {
  id: 123456,
  email: "test@example.com",
  created_at: "2026-06-11T08:31:53Z",
  customer: {
    first_name: "John",
    last_name: "Doe"
  }
};

const rawBody = JSON.stringify(bodyObj);

// Compute HMAC SHA256 of rawBody
const hmac = crypto.createHmac("sha256", SHOPIFY_WEBHOOK_SECRET);
hmac.update(rawBody, "utf8");
const signature = hmac.digest("base64");

console.log("Raw Body:", rawBody);
console.log("Computed Signature (Base64):", signature);

async function sendRequest(isSigned) {
  const headers = {
    "Content-Type": "application/json",
  };

  if (isSigned) {
    headers["X-Shopify-Hmac-Sha256"] = signature;
  } else {
    // Send with an obviously wrong signature
    headers["X-Shopify-Hmac-Sha256"] = "obviously_wrong_signature_123456=";
  }

  console.log(`\nSending ${isSigned ? "SIGNED" : "UNSIGNED/TAMPERED"} request...`);
  try {
    const res = await fetch(SOURCE_URL, {
      method: "POST",
      headers: headers,
      body: rawBody,
    });

    console.log("Response Status:", res.status);
    const text = await res.text();
    console.log("Response Body:", text);
  } catch (err) {
    console.error("Error sending request:", err.message);
  }
}

async function run() {
  // Send correctly signed request
  await sendRequest(true);

  // Allow 2 seconds before sending the next
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // Send tampered request
  await sendRequest(false);
}

run();
