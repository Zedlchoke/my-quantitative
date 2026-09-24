"""Phorec dashboard server — local-only (127.0.0.1:8766).

Serves index.html, logo, the live shadow state, equity curve, journal
tail and a /health.json freshness block. Query strings are IGNORED for
routing (the page fetches /state.json?<cache-buster>, which must be a
200 — owner order 2026-09-24: the exact URLs the browser calls must
return data, not 404). Responses are no-store so the buster alone
never serves stale HTML/JSON.

No external deps. Read-only: nothing here writes cycle state.
"""
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATE = ROOT / "shadow_state.json"
JOURNAL = ROOT / "shadow_journal.jsonl"
HEARTBEAT = ROOT / "daemon_heartbeat.json"
EQUITY_CURVE = ROOT / "equity_curve.json"

DAEMON_FRESH_SEC = 90  # heartbeat older than this => daemon considered dead


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body, cache="no-store"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path  # query string must never break routing
        q = parse_qs(url.query)
        if path in ("/", "/index.html"):
            try:
                self._send(200, "text/html; charset=utf-8", (HERE / "index.html").read_bytes())
            except FileNotFoundError:
                self._send(500, "text/plain", b"index.html missing")
        elif path == "/logo.jpg":
            try:
                self._send(200, "image/jpeg", (HERE / "assets" / "logo.jpg").read_bytes(),
                           cache="max-age=3600")
            except FileNotFoundError:
                self._send(404, "text/plain", b"no logo")
        elif path == "/state.json":
            try:
                self._send(200, "application/json", STATE.read_bytes())
            except FileNotFoundError:
                self._send(200, "application/json",
                           b'{"schema": "phorec.shadow_state@2", "data_stale": true, '
                           b'"marks_fresh": false, "note": "daemon not started yet", '
                           b'"account": null, "sleeves": {}}')
        elif path == "/equity_curve.json":
            try:
                self._send(200, "application/json", EQUITY_CURVE.read_bytes())
            except FileNotFoundError:
                self._send(200, "application/json", b'{"schema": "phorec.equity_curve@1", "points": []}')
        elif path == "/journal.jsonl":
            try:
                data = JOURNAL.read_bytes()
            except FileNotFoundError:
                data = b""
            try:
                limit = int(q.get("limit", ["0"])[0])
            except ValueError:
                limit = 0
            if limit > 0:
                lines = data.decode("utf-8", "replace").splitlines()[-limit:]
                data = ("\n".join(lines) + "\n").encode("utf-8")
            self._send(200, "application/x-ndjson", data)
        elif path == "/health.json":
            now = time.time()
            try:
                state_age = max(0.0, now - STATE.stat().st_mtime)
            except OSError:
                state_age = None
            try:
                hb = json.loads(HEARTBEAT.read_text())
                hb_age = None
                from datetime import datetime, timezone
                ts = str(hb.get("pid_heartbeat_utc", ""))
                if ts:
                    moment = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hb_age = max(0.0, (datetime.now(timezone.utc) - moment).total_seconds())
            except Exception:
                hb_age = None
            alive = hb_age is not None and hb_age <= DAEMON_FRESH_SEC
            self._send(200, "application/json", json.dumps({
                "schema": "phorec.health@1",
                "server_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
                "daemon_alive": alive,
                "heartbeat_age_s": None if hb_age is None else round(hb_age, 1),
                "state_age_s": None if state_age is None else round(state_age, 1),
                "daemon_fresh_threshold_s": DAEMON_FRESH_SEC,
            }).encode())
        else:
            self._send(404, "text/plain", b"not found")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
