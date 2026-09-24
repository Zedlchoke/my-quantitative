"""Entry point of the Phorec .app (PyInstaller + pywebview/WKWebView).

Owner order 2026-09-24 ("PHOREC PHẢI LÀ APP THỰC SỰ NHƯ CRYPTO"):

- double-click from Finder opens the dashboard INSIDE the app in a
  WKWebView window — never Chrome/Safari, never a Terminal, no
  external .venv or interpreter needed for the UI;
- the app READS the Forex shadow state only. The shadow daemon is an
  INDEPENDENT process started outside this app; closing the window
  must NOT stop the daemon, clear positions or lose PnL — this app
  never spawns, signals or owns it;
- if the WKWebView window cannot be opened the failure is logged
  loudly (~/Library/Logs/Phorec/app.log) and the local server keeps
  serving — there is NO silent fallback to a browser;
- read-only by construction: no broker/order route exists anywhere in
  this stack (tests/test_no_order_api.py pins it).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CYCLE_DIR = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
                 "fx-rangefade-2m-shadow-v1/research/control/"
                 "FX-RANGEFADE-2M-SHADOW-V1")
LOG_DIR = Path("~/Library/Logs/Phorec").expanduser()
LOG_PATH = LOG_DIR / "app.log"
LOG_MAX_BYTES = 1_000_000
WINDOW_TITLE = "Phorec — FX Shadow Dashboard"
WINDOW_SIZE = (1440, 900)
WINDOW_MIN = (860, 640)


def log(line: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > LOG_MAX_BYTES:
            LOG_PATH.replace(LOG_PATH.with_suffix(".log.1"))
    except OSError:
        pass
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with LOG_PATH.open("a") as f:
        f.write(f"{stamp} {line}\n")


def bundled(name: str) -> Path:
    """Resource next to the entry module — inside the PyInstaller bundle
    (sys._MEIPASS) when frozen, or the dashboard dir when run from
    source."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / name


def make_handler(page_bytes: bytes, logo_bytes: bytes, root: Path):
    from urllib.parse import urlparse, parse_qs

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlparse(self.path).path
            q = parse_qs(urlparse(self.path).query)
            if path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", page_bytes)
            elif path == "/logo.jpg":
                self._send(200, "image/jpeg", logo_bytes)
            elif path == "/state.json":
                try:
                    self._send(200, "application/json", (root / "shadow_state.json").read_bytes())
                except FileNotFoundError:
                    self._send(200, "application/json", b'{"data_stale": true, "marks_fresh": false, "account": null, "sleeves": {}}')
            elif path == "/equity_curve.json":
                try:
                    self._send(200, "application/json", (root / "equity_curve.json").read_bytes())
                except FileNotFoundError:
                    self._send(200, "application/json", b'{"points": []}')
            elif path == "/journal.jsonl":
                try:
                    data = (root / "shadow_journal.jsonl").read_bytes()
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
                import datetime as dt
                now = dt.datetime.now(dt.timezone.utc)
                hb_age = None
                try:
                    hb = json.loads((root / "daemon_heartbeat.json").read_text())
                    ts = str(hb.get("pid_heartbeat_utc", ""))
                    if ts:
                        moment = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        hb_age = max(0.0, (now - moment).total_seconds())
                except Exception:
                    hb_age = None
                alive = hb_age is not None and hb_age <= 90
                self._send(200, "application/json", json.dumps({
                    "schema": "phorec.health@1",
                    "server_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "daemon_alive": alive,
                    "heartbeat_age_s": None if hb_age is None else round(hb_age, 1),
                    "state_age_s": None,
                    "daemon_fresh_threshold_s": 90,
                }).encode())
            else:
                self._send(404, "text/plain", b"not found")

        def log_message(self, *a):
            pass

    return Handler


def pick_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def main() -> int:
    log(f"=== Phorec start (pid {os.getpid()}) ===")
    if "--check" in sys.argv:
        state = CYCLE_DIR / "shadow_state.json"
        hb = CYCLE_DIR / "daemon_heartbeat.json"
        print(json.dumps({
            "cycle_dir": str(CYCLE_DIR),
            "state_exists": state.is_file(),
            "heartbeat_exists": hb.is_file(),
            "log_path": str(LOG_PATH),
        }))
        return 0

    dashboard_src = CYCLE_DIR / "dashboard"
    page = (dashboard_src / "index.html").read_bytes()
    logo_path = bundled("logo.jpg")
    logo = logo_path.read_bytes() if logo_path.is_file() else (dashboard_src / "assets" / "logo.jpg").read_bytes()

    port = pick_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(page, logo, CYCLE_DIR))
    url = f"http://127.0.0.1:{port}"
    log(f"local server on {url} (read-only, loopback only)")

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    # sanity: our own server must answer before the window opens
    for _ in range(20):
        try:
            with urllib.request.urlopen(f"{url}/health.json", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.5)

    try:
        import webview  # pywebview
        log("opening WKWebView window (pywebview cocoa backend)")
        window = webview.create_window(
            WINDOW_TITLE, url, width=WINDOW_SIZE[0], height=WINDOW_SIZE[1],
            min_size=WINDOW_MIN)
        webview.start()
        log("window closed by user; shutting down ONLY this app's server")
    except Exception as exc:  # noqa: BLE001 - loud failure, NO browser fallback
        log(f"ERROR: WKWebView window failed: {type(exc).__name__}: {exc}")
        log(f"the dashboard stays served at {url} — open it manually; "
            "the app does NOT silently switch to a browser")
        print(f"PHOREC ERROR: webview failed: {exc}; dashboard still at {url}",
              file=sys.stderr)
        # keep serving so the owner still has a surface; exit only on SIGTERM
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
    httpd.shutdown()
    log("=== Phorec exit (daemon untouched) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
