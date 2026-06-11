#!/usr/bin/env node
// Tiny HTTP server: returns 500 on first POST /hooks, 200 on all subsequent
const http = require('http');

let firstRequest = true;

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/hooks') {
    if (firstRequest) {
      firstRequest = false;
      console.log('[server] First request -> returning 500');
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'simulated failure' }));
    } else {
      console.log('[server] Subsequent request -> returning 200');
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true }));
    }
  } else {
    res.writeHead(404);
    res.end('Not found');
  }
});

server.listen(3000, '127.0.0.1', () => {
  console.log('[server] Listening on http://127.0.0.1:3000');
});
