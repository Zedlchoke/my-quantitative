"""Read-only HTTP server for the .app window (localhost only).

GET/HEAD ONLY — every other method answers 405. Routes:

- ``/``                      the single dashboard page (static bytes)
- ``/api/snapshot.json``     engine snapshot + app status envelope
- ``/api/trade/<id>.json``   click-through detail by virtual_trade_id
                             or event_id

No static file serving, no write route, no order route, no credential
handling. Binds 127.0.0.1 only (never the LAN). The server belongs to
this dashboard alone; closing the window shuts IT down and never
touches the decision/valuation workers.
"""

from __future__ import annotations

import json
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from .page import PAGE_HTML_BYTES
from .store import SnapshotStore

__all__ = ["ROUTES", "make_server", "pick_port"]

ROUTES = (
    "/",
    "/api/snapshot.json",
    "/api/trade/",
)

_ALLOWED_METHODS = "GET, HEAD"


def pick_port(host: str = "127.0.0.1", preferred: int = 8791) -> int:
    """Prefer a stable port so the owner can bookmark it; walk a small
    range, then fall back to an ephemeral port. Multiple app instances
    are safe (read-only, stateless) and simply take the next port."""
    for port in list(range(preferred, preferred + 50)) + [0]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return sock.getsockname()[1]
    raise RuntimeError("cannot bind any local port for the dashboard")


def make_server(store: SnapshotStore, port: int, bind: str = "127.0.0.1"):
    class AppRequestHandler(BaseHTTPRequestHandler):
        server_version = "QuantShadowDashboard/1.0"
        store: SnapshotStore

        # ---- method gate ----
        def do_GET(self) -> None:  # noqa: N802
            self._route()

        def do_HEAD(self) -> None:  # noqa: N802
            self._route()

        def _reject_method(self) -> None:
            body = (
                b'{"error": "method not allowed; read-only dashboard '
                b'(GET/HEAD only)"}\n'
            )
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.send_header("Allow", _ALLOWED_METHODS)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        do_POST = _reject_method
        do_PUT = _reject_method
        do_DELETE = _reject_method
        do_PATCH = _reject_method
        do_OPTIONS = _reject_method

        # ---- helpers ----
        def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD" and body:
                self.wfile.write(body)

        def _send_json(self, status: HTTPStatus, payload: object) -> None:
            body = (
                json.dumps(payload, sort_keys=True, ensure_ascii=False,
                           allow_nan=False)
                + "\n"
            ).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8")

        # ---- routing ----
        def _route(self) -> None:
            path = self.path.split("?", 1)[0]
            if path == "/":
                self._send(HTTPStatus.OK, PAGE_HTML_BYTES,
                           "text/html; charset=utf-8")
                return
            if path == "/api/snapshot.json":
                try:
                    self._send_json(HTTPStatus.OK, self.store.envelope())
                except Exception as exc:  # noqa: BLE001 - fail closed
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                        {"error": f"snapshot failed closed: {exc}"},
                    )
                return
            if path.startswith("/api/trade/") and path.endswith(".json"):
                from urllib.parse import unquote

                trade_id = unquote(path[len("/api/trade/"):-len(".json")])
                detail = self.store.trade_detail(trade_id)
                if detail is None:
                    self._send_json(
                        HTTPStatus.NOT_FOUND,
                        {"error": f"unknown trade/event id: {trade_id!r}"},
                    )
                else:
                    self._send_json(HTTPStatus.OK, detail)
                return
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": f"no such route: {path}", "routes": list(ROUTES)},
            )

        def log_message(self, fmt: str, *args: object) -> None:
            pass  # quiet; app-level logging lives in app_main

    handler = AppRequestHandler
    handler.store = store  # type: ignore[attr-defined]
    httpd = ThreadingHTTPServer((bind, port), handler)
    httpd.daemon_threads = True
    return httpd


def serve_forever(store: SnapshotStore, port: int, bind: str = "127.0.0.1") -> None:
    httpd = make_server(store, port, bind=bind)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
