const https = require('https');

const apiKey = process.env.HOOKDECK_API_KEY;

async function request(method, path, body = null, headers = {}) {
  // ...
}

// Just curl it directly
const { execSync } = require('child_process');
try {
  const out = execSync(`curl -s -X POST -H "Authorization: Bearer ${apiKey}" -H "Content-Type: application/json" -d '{"provider": "SHOPIFY", "label": "shopify", "features": ["VERIFICATION"], "configs": {"webhook_secret_key": "my_secret_key"}}' https://api.hookdeck.com/2025-07-01/integrations`);
  console.log(out.toString());
} catch(e) { console.error(e) }
