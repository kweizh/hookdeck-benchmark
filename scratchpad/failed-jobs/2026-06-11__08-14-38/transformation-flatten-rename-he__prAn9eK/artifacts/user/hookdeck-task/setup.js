const apiKey = process.env.HOOKDECK_API_KEY;
const runId = process.env.ZEALT_RUN_ID;

if (!apiKey || !runId) {
  console.error('HOOKDECK_API_KEY and ZEALT_RUN_ID must be set!');
  process.exit(1);
}

const sourceName = `flatten-src-${runId}`;
const destName = `flatten-dest-${runId}`;
const transName = `flatten-rename-${runId}`;
const connName = `flatten-conn-${runId}`;

const transCode = `
addHandler("transform", (request, context) => {
  const body = request.body;
  if (!body || !body.data || !body.data.object) {
    return null;
  }
  const obj = body.data.object;
  if (typeof obj.amount !== 'number' || obj.amount < 100) {
    return null;
  }
  request.body = {
    id: obj.id,
    amount: obj.amount,
    currency: obj.currency,
    email: obj.customer_email
  };
  if (!request.headers) {
    request.headers = {};
  }
  request.headers["x-hookdeck-transformed"] = "true";
  return request;
});
`;

async function apiRequest(method, path, body = null) {
  const url = `https://api.hookdeck.com/2025-07-01${path}`;
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    }
  };
  if (body) {
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url, options);
  const text = await res.text();
  let data = null;
  try {
    data = JSON.parse(text);
  } catch (e) {
    data = text;
  }
  return { status: res.status, data };
}

function extractIdFromConflict(res) {
  if (res.data && res.data.data) {
    if (res.data.data.id) return res.data.data.id;
    if (res.data.data.transformation && res.data.data.transformation.id) return res.data.data.transformation.id;
    if (res.data.data.webhook && res.data.data.webhook.id) return res.data.data.webhook.id;
    if (res.data.data.destination && res.data.data.destination.id) return res.data.data.destination.id;
    if (res.data.data.source && res.data.data.source.id) return res.data.data.source.id;
  }
  return null;
}

async function getOrCreateSource() {
  console.log(`Creating Source: ${sourceName}`);
  const res = await apiRequest('POST', '/sources', {
    name: sourceName,
    type: 'WEBHOOK'
  });
  if (res.status === 201 || res.status === 200) {
    return res.data;
  } else if (res.status === 409) {
    const id = extractIdFromConflict(res);
    console.log(`Source already exists with ID: ${id}. Fetching...`);
    const getRes = await apiRequest('GET', `/sources/${id}`);
    return getRes.data;
  } else {
    throw new Error(`Failed to create source: ${JSON.stringify(res.data)}`);
  }
}

async function getOrCreateDestination() {
  console.log(`Creating Destination: ${destName}`);
  const res = await apiRequest('POST', '/destinations', {
    name: destName,
    type: 'MOCK_API'
  });
  if (res.status === 201 || res.status === 200) {
    return res.data;
  } else if (res.status === 409) {
    const id = extractIdFromConflict(res);
    console.log(`Destination already exists with ID: ${id}. Fetching...`);
    const getRes = await apiRequest('GET', `/destinations/${id}`);
    return getRes.data;
  } else {
    throw new Error(`Failed to create destination: ${JSON.stringify(res.data)}`);
  }
}

async function getOrCreateTransformation() {
  console.log(`Creating/Updating Transformation: ${transName}`);
  const res = await apiRequest('POST', '/transformations', {
    name: transName,
    code: transCode
  });
  if (res.status === 201 || res.status === 200) {
    return res.data;
  } else if (res.status === 409) {
    const id = extractIdFromConflict(res);
    console.log(`Transformation already exists with ID: ${id}. Updating code...`);
    const putRes = await apiRequest('PUT', `/transformations/${id}`, {
      name: transName,
      code: transCode
    });
    return putRes.data;
  } else {
    throw new Error(`Failed to create/update transformation: ${JSON.stringify(res.data)}`);
  }
}

async function getOrCreateConnection(sourceId, destId, transId) {
  console.log(`Creating/Updating Connection: ${connName}`);
  const res = await apiRequest('POST', '/connections', {
    name: connName,
    source_id: sourceId,
    destination_id: destId,
    rules: [
      {
        type: 'transform',
        transformation_id: transId
      }
    ]
  });
  if (res.status === 201 || res.status === 200) {
    return res.data;
  } else if (res.status === 409) {
    const id = extractIdFromConflict(res);
    console.log(`Connection already exists with ID: ${id}. Updating rules...`);
    const putRes = await apiRequest('PUT', `/connections/${id}`, {
      rules: [
        {
          type: 'transform',
          transformation_id: transId
        }
      ]
    });
    return putRes.data;
  } else {
    throw new Error(`Failed to create/update connection: ${JSON.stringify(res.data)}`);
  }
}

async function run() {
  try {
    const source = await getOrCreateSource();
    console.log('Source URL:', source.url);
    console.log('Source ID:', source.id);

    const destination = await getOrCreateDestination();
    console.log('Destination ID:', destination.id);

    const transformation = await getOrCreateTransformation();
    console.log('Transformation ID:', transformation.id);

    const connection = await getOrCreateConnection(source.id, destination.id, transformation.id);
    console.log('Connection ID:', connection.id);

    console.log('Setup completed successfully!');
    console.log(JSON.stringify({
      source_id: source.id,
      source_url: source.url,
      destination_id: destination.id,
      transformation_id: transformation.id,
      connection_id: connection.id
    }, null, 2));

  } catch (err) {
    console.error('Error during setup:', err);
    process.exit(1);
  }
}

run();
