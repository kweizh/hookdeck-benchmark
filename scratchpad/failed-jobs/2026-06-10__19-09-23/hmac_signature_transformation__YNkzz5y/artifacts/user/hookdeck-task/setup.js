const fs = require('fs');

async function main() {
  const apiKey = process.env.HOOKDECK_API_KEY;
  const runId = process.env.ZEALT_RUN_ID;
  const hmacSecret = process.env.HMAC_SECRET;

  if (!apiKey || !runId || !hmacSecret) {
    console.error('Missing required environment variables');
    process.exit(1);
  }

  const baseUrl = 'https://api.hookdeck.com/2024-03-01';
  const headers = {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  };

  try {
    // 1. Create Destination
    const destRes = await fetch(`${baseUrl}/destinations`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: `hmac-dest-${runId}`,
        url: 'https://mock.hookdeck.com'
      })
    });
    const destData = await destRes.json();
    const destId = destData.id;
    console.log(`Created Destination ID: ${destId}`);

    // 2. Create Source
    const sourceRes = await fetch(`${baseUrl}/sources`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: `hmac-source-${runId}`
      })
    });
    const sourceData = await sourceRes.json();
    const sourceId = sourceData.id;
    console.log(`Created Source ID: ${sourceId}`);

    // 3. Create Transformation
    const code = `addHandler("transform", (request, context) => {
  const secret = context.env.HMAC_SECRET;
  const body = JSON.stringify(request.body);
  const hmac = crypto.createHmac("sha256", secret).update(body).digest("hex");
  request.headers["x-hmac-signature"] = hmac;
  return request;
});`;
    const transRes = await fetch(`${baseUrl}/transformations`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: `hmac-transform-${runId}`,
        code,
        env: {
          HMAC_SECRET: hmacSecret
        }
      })
    });
    const transData = await transRes.json();
    const transId = transData.id;
    console.log(`Created Transformation ID: ${transId}`);

    // 4. Create Connection
    const connRes = await fetch(`${baseUrl}/connections`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        name: `hmac-connection-${runId}`,
        source_id: sourceId,
        destination_id: destId,
        rules: [
          {
            type: 'transform',
            transformation_id: transId
          }
        ]
      })
    });
    const connData = await connRes.json();
    const connId = connData.id;
    console.log(`Created Connection ID: ${connId}`);

    // 5. Write to output.log
    const logContent = `Source ID: ${sourceId}\nConnection ID: ${connId}\n`;
    fs.writeFileSync('/home/user/hookdeck-task/output.log', logContent);
    console.log('Successfully wrote to output.log');

  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

main();
