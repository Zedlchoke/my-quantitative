"""Read-only HTTP server for the PROSPECTIVE-SHADOW-V1 owner dashboard.

GET/HEAD ONLY. Every other HTTP method answers ``405`` with an
``Allow: GET, HEAD`` header. Routes:

- ``/``                    the self-contained dashboard page
- ``/api/snapshot.json``   the full snapshot as canonical JSON
- ``/api/trade/<id>.json`` click-through detail by virtual_trade_id or event_id
- ``/api/export.csv``      sanitized CSV of the (query-filtered) trades table
- ``/api/export.json``     sanitized JSON of the (query-filtered) trades + equity series

There is NO static file serving, NO write route, NO order route, NO
credential handling: the server can never mutate the append-only
ledgers nor place an order. Exports are generated in memory and
streamed to the client; nothing is written server-side.
"""

from __future__ import annotations

import csv
import io
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Mapping, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from .render import generate_html
from .snapshot import (
    build_dashboard_snapshot,
    resolve_ledger_paths,
    resolve_valuation_mark_paths,
)

__all__ = ["ROUTES", "DashboardApp", "DashboardRequestHandler", "make_server", "serve"]

ROUTES: Tuple[str, ...] = (
    "/",
    "/api/snapshot.json",
    "/api/trade/",
    "/api/export.csv",
    "/api/export.json",
)

_ALLOWED_METHODS = "GET, HEAD"


class DashboardApp:
    """Read-only application state: ledger locations + snapshot factory."""

    def __init__(
        self,
        ledger_paths_by_family: Mapping[str, Optional[str]],
        identity_manifest_path: Optional[str] = None,
        shadow_start_utc: Optional[str] = None,
        valuation_marks_by_family: Optional[Mapping[str, Optional[str]]] = None,
    ):
        self.ledger_paths_by_family = dict(ledger_paths_by_family)
        self.identity_manifest_path = identity_manifest_path
        self.shadow_start_utc = shadow_start_utc
        self.valuation_marks_by_family = (
            dict(valuation_marks_by_family)
            if valuation_marks_by_family is not None
            else resolve_valuation_mark_paths(
                next(
                    (os.path.dirname(p) for p in ledger_paths_by_family.values() if p),
                    "",
                )
                if any(ledger_paths_by_family.values())
                else ""
            )
        )

    def snapshot(self) -> Dict[str, Any]:
        from datetime import datetime, timezone

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return build_dashboard_snapshot(
            self.ledger_paths_by_family,
            now_iso,
            identity_manifest_path=self.identity_manifest_path,
            shadow_start_utc=self.shadow_start_utc,
            valuation_marks_by_family=self.valuation_marks_by_family,
        )

    def page_html(self) -> str:
        return generate_html(self.snapshot())

    def trade_detail(self, trade_or_event_id: str) -> Optional[Dict[str, Any]]:
        snap = self.snapshot()
        detail = snap["trade_index"].get(trade_or_event_id)
        if detail is not None:
            return detail
        event = snap["event_index"].get(trade_or_event_id)
        return event

    @staticmethod
    def _filter_trades(
        snapshot: Mapping[str, Any], query: Mapping[str, List[str]]
    ) -> List[Dict[str, Any]]:

        def q1(name: str) -> str:
            values = query.get(name)
            return values[0] if values else ""

        family = q1("family").strip()
        asset = q1("asset").strip().upper()
        side = q1("side").strip()
        status = q1("status").strip()
        date_from = q1("date_from").strip()
        date_to = q1("date_to").strip()
        event_status = q1("event_status").strip()

        rows = []
        for row in snapshot["trades"]:
            if family and row.get("family") != family:
                continue
            if asset and str(row.get("asset") or "").upper() != asset:
                continue
            if side and row.get("side") != side:
                continue
            if status and row.get("status") != status:
                continue
            if event_status:
                ev = snapshot["event_index"].get(row.get("event_id"), {})
                if ev.get("status") != event_status:
                    continue
            fill_ts = str(row.get("actual_virtual_fill_time") or "")
            if date_from and fill_ts[:10] < date_from:
                continue
            if date_to and fill_ts[:10] > date_to:
                continue
            rows.append(row)
        return rows

    @staticmethod
    def trades_csv(rows: List[Mapping[str, Any]]) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
        if rows:
            columns = list(rows[0].keys())
            writer.writerow(columns)
            for row in rows:
                writer.writerow(
                    "UNAVAILABLE" if row.get(col) is None else row.get(col)
                    for col in columns
                )
        return buffer.getvalue()

    @staticmethod
    def export_json(
        snapshot: Mapping[str, Any], rows: List[Mapping[str, Any]]
    ) -> str:
        payload = {
            "schema": "shv1_dashboard_export_v1",
            "cycle_id": snapshot.get("cycle_id"),
            "generated_utc": snapshot.get("generated_utc"),
            "note": snapshot.get("exports_note"),
            "baseline_usdt": snapshot["combined"]["baseline_usdt"],
            "trades_filtered": rows,
            "equity_series": snapshot["combined"]["chart_points"],
            "drawdown_series": snapshot["combined"]["drawdown_series"],
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)


class DashboardRequestHandler(BaseHTTPRequestHandler):
    server_version = "ShV1ReadOnlyDashboard/1.0"
    app: DashboardApp

    # ---- method gate: GET/HEAD only, everything else is 405 ----
    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        self._route(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._route(include_body=False)

    def _reject_method(self) -> None:
        body = b'{"error": "method not allowed; this dashboard is GET/HEAD read-only"}\n'
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

    # ---- routing ----
    def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD" and body:
            self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, payload: Any) -> None:
        body = (
            json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        ).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _route(self, include_body: bool) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        app = self.app

        if path == "/":
            try:
                page = app.page_html().encode("utf-8")
            except Exception as exc:  # fail closed: report, never fake data
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                {"error": f"snapshot failed closed: {exc}"})
                return
            self._send(HTTPStatus.OK, page, "text/html; charset=utf-8")
            return

        if path == "/api/snapshot.json":
            try:
                self._send_json(HTTPStatus.OK, app.snapshot())
            except Exception as exc:  # noqa: BLE001 - fail closed
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR,
                                {"error": f"snapshot failed closed: {exc}"})
            return

        if path.startswith("/api/trade/") and path.endswith(".json"):
            trade_id = unquote(path[len("/api/trade/"):-len(".json")])
            detail = app.trade_detail(trade_id)
            if detail is None:
                self._send_json(HTTPStatus.NOT_FOUND,
                                {"error": f"unknown trade/event id: {trade_id!r}"})
            else:
                self._send_json(HTTPStatus.OK, detail)
            return

        if path == "/api/export.csv":
            snap = app.snapshot()
            rows = DashboardApp._filter_trades(snap, query)
            self._send(HTTPStatus.OK,
                       app.trades_csv(rows).encode("utf-8"),
                       "text/csv; charset=utf-8")
            return

        if path == "/api/export.json":
            snap = app.snapshot()
            rows = DashboardApp._filter_trades(snap, query)
            self._send_json(HTTPStatus.OK, app.export_json(snap, rows))
            return

        self._send_json(HTTPStatus.NOT_FOUND,
                        {"error": f"no such route: {path}", "routes": list(ROUTES)})

    def log_message(self, fmt: str, *args: Any) -> None:  # quiet, no secrets
        pass


def make_server(
    read_only_root: str,
    port: int,
    bind: str = "127.0.0.1",
    identity_manifest_path: Optional[str] = None,
    shadow_start_utc: Optional[str] = None,
    valuation_marks_by_family: Optional[Mapping[str, Optional[str]]] = None,
) -> ThreadingHTTPServer:
    """Bind the read-only dashboard server (caller decides how to run it).

    The near-real valuation mark ledgers are derived from the
    ``valuation_marks/`` sibling of ``read_only_root`` unless pinned
    explicitly.
    """
    app = DashboardApp(
        resolve_ledger_paths(read_only_root),
        identity_manifest_path=identity_manifest_path,
        shadow_start_utc=shadow_start_utc,
        valuation_marks_by_family=(
            valuation_marks_by_family
            if valuation_marks_by_family is not None
            else resolve_valuation_mark_paths(read_only_root)
        ),
    )

    handler = type(
        "BoundDashboardRequestHandler",
        (DashboardRequestHandler,),
        {"app": app},
    )
    return ThreadingHTTPServer((bind, port), handler)


def serve(
    read_only_root: str,
    port: int,
    bind: str = "127.0.0.1",
    identity_manifest_path: Optional[str] = None,
    shadow_start_utc: Optional[str] = None,
    valuation_marks_by_family: Optional[Mapping[str, Optional[str]]] = None,
) -> None:
    """Serve the dashboard for the ledgers in ``read_only_root`` (GET/HEAD only)."""
    httpd = make_server(
        read_only_root,
        port,
        bind=bind,
        identity_manifest_path=identity_manifest_path,
        shadow_start_utc=shadow_start_utc,
        valuation_marks_by_family=valuation_marks_by_family,
    )
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
