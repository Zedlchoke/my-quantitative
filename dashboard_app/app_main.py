"""Entry point of the Quant Shadow Dashboard .app.

Double-click flow: resolve the runtime paths from the cycle registry,
build the first snapshot, bind the read-only server on 127.0.0.1, open
ONE pywebview (WKWebView) window. Closing the window shuts down only
this dashboard's server — the PROSPECTIVE-SHADOW-V1 decision and
valuation workers are independent processes and keep running.

Fail-safe behaviours:
- every step logs to ~/Library/Logs/QuantShadowDashboard/app.log so a
  failed launch can be diagnosed without Terminal;
- if pywebview cannot open a window the dashboard falls back to the
  default browser (still localhost-only) and keeps serving;
- the app NEVER takes the heavy lock, NEVER writes to the ledgers and
  NEVER places orders (read-only by construction).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from typing import Optional

from .resolve import APP_SUPPORT_DIR, RuntimePaths, find_runtime, remember_runtime
from .server import make_server, pick_port
from .store import SnapshotStore

LOG_DIR = os.path.expanduser("~/Library/Logs/QuantShadowDashboard")
LOG_PATH = os.path.join(LOG_DIR, "app.log")
LOG_MAX_BYTES = 1_000_000

# The dashboard reads files at most every 30 s and rebuilds only when
# bytes change; this background loop keeps the snapshot warm even if
# the window is idle (cheap: one stat-fingerprint per cycle).
WARM_REFRESH_SECONDS = 30


def setup_logging() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > LOG_MAX_BYTES:
            os.replace(LOG_PATH, LOG_PATH + ".1")
    except OSError:
        pass


def log(message: str) -> None:
    line = time.strftime("%Y-%m-%dT%H:%M:%S") + " " + message
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass
    sys.stderr.write(line + "\n")


def write_pidfile(port: int) -> Optional[str]:
    try:
        os.makedirs(APP_SUPPORT_DIR, exist_ok=True)
        path = os.path.join(APP_SUPPORT_DIR, "app.pid")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"pid": os.getpid(), "port": port,
                       "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, fh)
        return path
    except OSError:
        return None


def note_existing_instance() -> None:
    path = os.path.join(APP_SUPPORT_DIR, "app.pid")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            info = json.load(fh)
        pid = info.get("pid")
        if isinstance(pid, int):
            os.kill(pid, 0)  # raises if dead
        log(f"note: another dashboard instance appears to be running "
            f"(pid {pid}); this read-only instance will run beside it safely")
    except (OSError, ValueError, ProcessLookupError):
        pass


def warm_loop(store: SnapshotStore, stop: threading.Event) -> None:
    """Keep the snapshot warm; retries after errors instead of dying."""
    while not stop.wait(WARM_REFRESH_SECONDS):
        try:
            store.refresh()
        except Exception as exc:  # noqa: BLE001 - never crash the app
            log(f"warm refresh error (will retry): {exc}")


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="Quant Shadow Dashboard")
    parser.add_argument("--check", action="store_true",
                        help="resolve paths, build one snapshot, print a "
                             "summary and exit (no window; diagnostics)")
    parser.add_argument("--port", type=int, default=None,
                        help="preferred localhost port (default: 8791, "
                             "auto-walk when busy)")
    args = parser.parse_args(argv)

    setup_logging()
    log("=== Quant Shadow Dashboard start "
        f"(pid {os.getpid()}, py {sys.version.split()[0]}) ===")

    try:
        paths: RuntimePaths = find_runtime()
    except RuntimeError as exc:
        log(f"FATAL cannot resolve runtime: {exc}")
        if args.check:
            print(f"RESOLVE FAIL:\n{exc}")
            return 2
        _fatal_dialog(
            "Không tìm thấy dữ liệu PROSPECTIVE-SHADOW-V1",
            "Chi tiết trong ~/Library/Logs/QuantShadowDashboard/app.log",
        )
        return 2
    log(f"runtime resolved via {paths.source}: {paths.runtime_root}")
    remember_runtime(paths)

    try:
        store = SnapshotStore(paths)
        store.refresh()
    except Exception as exc:  # noqa: BLE001
        log(f"FATAL first snapshot failed: {type(exc).__name__}: {exc}")
        if args.check:
            print(f"SNAPSHOT FAIL: {exc}")
            return 3
        _fatal_dialog(
            "Không đọc được dữ liệu shadow",
            f"Lỗi: {exc}\nChi tiết trong ~/Library/Logs/QuantShadowDashboard/app.log",
        )
        return 3

    if args.check:
        env = store.envelope()
        status = env["app"]["status"]["state"]
        vc = (env["snapshot"] or {}).get("valuation", {}).get("combined", {})
        print(json.dumps({
            "runtime": paths.describe(),
            "status": status,
            "combined_equity": vc.get("equity"),
            "as_of_utc": vc.get("as_of_utc"),
            "trades": len((env["snapshot"] or {}).get("trades", [])),
            "engine_build_error": env["app"]["engine_build_error"],
        }, indent=2, ensure_ascii=False))
        ok = env["snapshot"] is not None
        log(f"--check done ok={ok}")
        return 0 if ok else 3

    port = pick_port(preferred=args.port or 8791)
    httpd = make_server(store, port)
    server_thread = threading.Thread(
        target=httpd.serve_forever, name="dashboard-http", daemon=True
    )
    server_thread.start()
    log(f"read-only server on http://127.0.0.1:{port}/ (GET/HEAD only)")

    stop = threading.Event()
    warm = threading.Thread(
        target=warm_loop, args=(store, stop), name="dashboard-warm", daemon=True
    )
    warm.start()
    note_existing_instance()  # before writing OUR pidfile (self-check)
    write_pidfile(port)

    url = f"http://127.0.0.1:{port}/"
    exit_code = 0
    try:
        import webview  # pywebview (WKWebView on macOS)

        log("opening pywebview window (cocoa/WKWebView)")
        webview.create_window(
            "Quant Shadow Dashboard — PROSPECTIVE-SHADOW-V1",
            url,
            width=1340,
            height=940,
            min_size=(1080, 760),
        )
        webview.start()
        log("window closed by user")
    except Exception as exc:  # noqa: BLE001
        log(f"pywebview unavailable/failed ({exc}); falling back to browser")
        try:
            import webbrowser

            webbrowser.open(url)
            log(f"opened default browser at {url}; serving until killed")
            while True:
                time.sleep(3600)
        except Exception:  # noqa: BLE001
            exit_code = 4

    stop.set()
    try:
        httpd.shutdown()
        httpd.server_close()
    except Exception:  # noqa: BLE001
        pass
    log(f"=== dashboard stopped (exit {exit_code}); shadow workers untouched ===")
    return exit_code


def _fatal_dialog(title: str, message: str) -> None:
    """Best-effort native alert when the app cannot start."""
    try:
        import subprocess

        script = (
            f'display dialog "{message}" with title "{title}" '
            f'buttons {{"OK"}} default button "OK" with icon caution'
        )
        subprocess.run(["osascript", "-e", script], check=False, timeout=30)
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    raise SystemExit(main())
