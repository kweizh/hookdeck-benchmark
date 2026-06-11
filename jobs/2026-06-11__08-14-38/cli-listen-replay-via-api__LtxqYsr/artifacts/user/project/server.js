const http = require('http');

let requestCount = 0;

const server = http.createServer((req, res) => {
  console.log(`[SERVER] Received ${req.method} request to ${req.url}`);
  
  if (req.method === 'POST' && req.url === '/hooks') {
    requestCount++;
    console.log(`[SERVER] Request #${requestCount}`);
    if (requestCount === 1) {
      console.log("[SERVER] First request: Returning 500");
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: "First delivery attempt failed on purpose" }));
    } else {
      console.log(`[SERVER] Request #${requestCount}: Returning 200`);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: true, attempts: requestCount }));
    }
  } else {
    console.log(`[SERVER] Path not found: ${req.url}`);
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

const PORT = 3000;
server.listen(PORT, () => {
  console.log(`[SERVER] Tiny HTTP server running on port ${PORT}`);
});
