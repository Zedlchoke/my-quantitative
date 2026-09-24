"""Phorec dashboard server — local-only (127.0.0.1:8765).
Serves index.html, logo, and the live shadow state. No external deps."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE.parent / "shadow_state.json"
JOURNAL = HERE.parent / "shadow_journal.jsonl"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", (HERE / "index.html").read_bytes())
        elif self.path == "/logo.jpg":
            self._send(200, "image/jpeg", (HERE / "assets" / "logo.jpg").read_bytes())
        elif self.path == "/state.json":
            try:
                self._send(200, "application/json", STATE.read_bytes())
            except FileNotFoundError:
                self._send(200, "application/json", b'{"data_stale": true, "note": "daemon not started yet"}')
        elif self.path == "/equity_curve.json":
            try:
                self._send(200, "application/json", (HERE.parent / "equity_curve.json").read_bytes())
            except FileNotFoundError:
                self._send(200, "application/json", b'{"points": []}')
        elif self.path == "/journal.jsonl":
            try:
                self._send(200, "application/x-ndjson", JOURNAL.read_bytes())
            except FileNotFoundError:
                self._send(200, "application/x-ndjson", b"")
        else:
            self._send(404, "text/plain", b"not found")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
