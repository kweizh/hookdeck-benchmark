#!/usr/bin/env python3
"""Flaky local HTTP server: returns 500 on first POST /hooks, then 200 thereafter."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

class FlakyHandler(BaseHTTPRequestHandler):
    first_request = True

    def do_POST(self):
        body_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(body_len) if body_len > 0 else b''

        if self.path == '/hooks':
            if FlakyHandler.first_request:
                FlakyHandler.first_request = False
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Internal Server Error (first request)')
                print("POST /hooks -> 500 (first request)", flush=True)
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
                print("POST /hooks -> 200", flush=True)
        else:
            self.send_response(404)
            self.end_headers()
            print(f"POST {self.path} -> 404", flush=True)

    def log_message(self, format, *args):
        # Suppress default logging to stderr
        pass

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = HTTPServer(('0.0.0.0', port), FlakyHandler)
    print(f"Flaky server listening on port {port}", flush=True)
    server.serve_forever()
