const http = require('http');

let requestCount = 0;

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/hooks') {
    requestCount++;
    console.log(`Received POST /hooks request #${requestCount}`);
    
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      if (requestCount === 1) {
        // First request returns 500
        console.log('Returning 500 (first request)');
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Internal Server Error' }));
      } else {
        // Subsequent requests return 200
        console.log('Returning 200 (subsequent request)');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ received: true }));
      }
    });
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(3000, () => {
  console.log('Server listening on port 3000');
});