const https = require('https');
const crypto = require('crypto');
const fs = require('fs');

const runId = process.env.ZEALT_RUN_ID;
const secret = process.env.SHOPIFY_WEBHOOK_SECRET;

const sourceUrl = 'https://hkdk.events/m0wih2hd6gtg3e';

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
    
    // Write Source ID to log
    fs.writeFileSync('/home/user/hookdeck-task/output.log', `Source ID: src_m0wih2hd6gtg3e\n`);
}

main();