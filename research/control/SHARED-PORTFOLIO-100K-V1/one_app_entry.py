"""PhorecOne .app entry (PyInstaller + pywebview, gate A preview).

Sibling of the earlier review entries; the app:
- opens the ONE-account two-sleeve dashboard in a WKWebView window;
- is READ-ONLY: epoch-1 sources are only read; the FX daemon, PSV1
  workers and every other process are never spawned, signalled or owned;
- GET-only HTTP surface (no order route — pinned by tests);
- --check verifies the frozen bundle without opening a window.
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG_DIR = Path("~/Library/Logs/Phorec").expanduser()
LOG_PATH = LOG_DIR / "app.log"
WINDOW_TITLE = "Phorec One — Shadow Portfolio $100,000 (PREVIEW · epoch2 NOT activated)"
WINDOW_SIZE = (1440, 940)
WINDOW_MIN = (900, 660)


def log(line: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if LOG_PATH.exists() and LOG_PATH.stat().st_size > 1_000_000:
            LOG_PATH.replace(LOG_PATH.with_suffix(".log.1"))
    except OSError:
        pass
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with LOG_PATH.open("a") as f:
        f.write(f"{stamp} [phorecone] {line}\n")


def main() -> int:
    log(f"=== PhorecOne start (pid {os.getpid()}) ===")
    if "--check" in sys.argv:
        print(json.dumps({"app": "phorecone-gateA-preview",
                          "log_path": str(LOG_PATH)}))
        return 0
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    from one.serve_one import Handler, PORT

    port = PORT
    import socket
    try:
        s = socket.socket()
        s.bind(("127.0.0.1", port))
        s.close()
    except OSError:
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        log(f"port {PORT} busy, falling back to {port}")

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    log(f"PhorecOne server on {url} (read-only, loopback only)")
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    for _ in range(20):
        try:
            with urllib.request.urlopen(f"{url}/health.json", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    try:
        import webview
        log("opening WKWebView window (pywebview cocoa backend)")
        webview.create_window(WINDOW_TITLE, url, width=WINDOW_SIZE[0],
                              height=WINDOW_SIZE[1], min_size=WINDOW_MIN)
        webview.start()
        log("window closed; shutting down ONLY this app's server (workers untouched)")
    except Exception as exc:  # noqa: BLE001 - loud failure, NO browser fallback
        log(f"ERROR: WKWebView window failed: {type(exc).__name__}: {exc}")
        print(f"PHORECONE ERROR: webview failed: {exc}; dashboard still at {url}",
              file=sys.stderr)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
    httpd.shutdown()
    log("=== PhorecOne exit (workers untouched) ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
