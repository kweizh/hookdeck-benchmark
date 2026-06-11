const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const runId = process.env.ZEALT_RUN_ID;
const apiKey = process.env.HOOKDECK_API_KEY;
const secret = process.env.SHOPIFY_WEBHOOK_SECRET;

if (!runId || !apiKey || !secret) {
  console.error("Missing environment variables.");
  process.exit(1);
}

async function request(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.hookdeck.com',
      port: 443,
      path: path,
      method: method,
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        ...headers
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });

    req.on('error', reject);
    if (body) {
      req.write(typeof body === 'string' ? body : JSON.stringify(body));
    }
    req.end();
  });
}

async function fetchUrl(url, method, body, headers = {}) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const options = {
            hostname: urlObj.hostname,
            port: urlObj.port || 443,
            path: urlObj.pathname + urlObj.search,
            method: method,
            headers: {
                ...headers
            }
        };

        const req = https.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                resolve({ status: res.statusCode, data });
            });
        });

        req.on('error', reject);
        if (body) {
            req.write(body);
        }
        req.end();
    });
}


async function main() {
  try {
    // 1. Create Source
    const sourcePayload = {
      name: `shopify-verify-${runId}`,
      custom_response: {
        content_type: "application/json",
        body: '{"success":true}'
      },
      verification: {
        type: "shopify",
        configs: {
          webhook_secret_key: secret
        }
      }
    };

    const sourceRes = await request('POST', '/2025-07-01/sources', sourcePayload);
    if (sourceRes.status !== 200 && sourceRes.status !== 201) {
      console.error("Failed to create source:", sourceRes);
      return;
    }

    const source = sourceRes.data;
    const sourceId = source.id;
    const sourceUrl = source.url;
    console.log(`Created source ${sourceId} with URL ${sourceUrl}`);
    
    fs.writeFileSync('/home/user/hookdeck-task/output.log', `Source ID: ${sourceId}\n`);

    // 2. Send requests
    const bodyObj = { hello: "world", runId };
    const rawBody = JSON.stringify(bodyObj);
    
    // Correctly signed
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(rawBody, 'utf8');
    const signature = hmac.digest('base64');
    
    console.log("Sending signed request...");
    const req1 = await fetchUrl(sourceUrl, 'POST', rawBody, {
        'Content-Type': 'application/json',
        'X-Shopify-Hmac-Sha256': signature
    });
    console.log("Req1 status:", req1.status);

    // Incorrectly signed
    console.log("Sending unsigned request...");
    const req2 = await fetchUrl(sourceUrl, 'POST', rawBody, {
        'Content-Type': 'application/json',
        'X-Shopify-Hmac-Sha256': 'wrongsignature'
    });
    console.log("Req2 status:", req2.status);

    console.log("Done.");

  } catch (err) {
    console.error(err);
  }
}

main();