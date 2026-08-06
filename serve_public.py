#!/usr/bin/env python3
"""Simple static file server for AnswerFirst AI public site."""
import http.server
import socketserver
import os

PORT = 8090
DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "public-site"))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Portal-Token")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"[+] Serving AnswerFirst AI from {DIRECTORY}")
        print(f"[+] Public site: http://localhost:{PORT}/")
        print(f"[+] Portal login: http://localhost:{PORT}/portal/login")
        print("[+] Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupted:
            print("\n[+] Server stopped")
