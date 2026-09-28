"""Tiny local server for the PWA dashboard — stdlib only, no Flask/FastAPI.

Serves the pwa/ folder as static files and exposes /api/jobs, which reads
output/jobs.json fresh on every request (so the dashboard always reflects
the latest pipeline run without needing a server restart).

This is local-only by design: it binds to localhost and nothing here talks
to the internet except your own browser hitting it. Run it, then open
http://localhost:8787 and (optionally) install it as a PWA from your
browser's install prompt.
"""
from __future__ import annotations

import json
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config  # noqa: E402

PWA_DIR = Path(__file__).resolve().parent.parent / "pwa"
PORT = 8787


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PWA_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/jobs":
            self._serve_jobs_json()
            return
        super().do_GET()

    def _serve_jobs_json(self):
        jobs_path = config.OUTPUT_DIR / "jobs.json"
        if jobs_path.exists():
            body = jobs_path.read_bytes()
        else:
            body = b"[]"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        # Quieter default logging — just method + path + status.
        pass


def main() -> None:
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"Serving {PWA_DIR} at http://localhost:{PORT}")
    print(f"Job data source: {config.OUTPUT_DIR / 'jobs.json'}")
    print("Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
