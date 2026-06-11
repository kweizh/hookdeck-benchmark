const http = require('http');

let first = true;

const server = http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/hooks') {
    if (first) {
      first = false;
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Failed');
      console.log('500 returned');
    } else {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('OK');
      console.log('200 returned');
    }
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not found');
  }
});

server.listen(3000, () => {
  console.log('Server listening on port 3000');
});