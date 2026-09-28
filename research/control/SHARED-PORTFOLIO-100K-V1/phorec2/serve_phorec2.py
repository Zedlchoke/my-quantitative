"""Phorec v2 — Shared Portfolio 100K dashboard server (PREVIEW build).

SCRATCH PORT 8767. This is a REVIEW BUILD: it does NOT replace the
running Phorec (127.0.0.1:8766) or the crypto view (127.0.0.1:8765),
owns no worker, writes nothing outside this control dir's out/ cache,
and exposes GET endpoints only.

Endpoints (all GET, no-store):
  /                     unified portfolio page (phorec2/index.html)
  /logo.jpg
  /health.json          FX daemon freshness (epoch-1 FX worker)
  /state.json           FX shadow state (epoch-1 book, read-only)
  /journal.jsonl?limit  FX journal tail (read-only)
  /portfolio.json       full engine state (PREVIEW) + exposure + workers
  /calendar.json?month  PnL calendar grid for YYYY-MM (epoch-1 history)
  /day.json?date=       drill-down: per-sleeve day breakdown + FX trades
  /sources.json         sha256 manifest of the immutable epoch-1 sources
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import portfolio_lib as pl

HERE = Path(__file__).resolve().parent
PORT = 8767
DAEMON_FRESH_SEC = 90

_cache: dict = {"key": None, "state": None}


def _mtime_key() -> tuple:
    paths = [pl.FX_DIR / "shadow_journal.jsonl", pl.FX_DIR / "shadow_state.json",
             pl.HERE / "epoch_config.json"] + \
            [pl.PSV1_RESULTS / f"valuation_marks/{f}.jsonl" for f in pl.CRYPTO_SLEEVES]
    key = []
    for p in paths:
        try:
            key.append((str(p), p.stat().st_mtime_ns))
        except OSError:
            key.append((str(p), None))
    return tuple(key)


def portfolio_state() -> dict:
    key = _mtime_key()
    if _cache["key"] != key or _cache["state"] is None:
        _cache["state"] = pl.build_state()
        _cache["key"] = key
    return _cache["state"]


def calendar(month: str) -> dict:
    """Calendar grid for YYYY-MM from epoch-1 history (USD-eq, labelled)."""
    st = portfolio_state()
    days = {d["day_utc"]: d for d in st["epoch1"]["history_days"]}
    year, mon = (int(x) for x in month.split("-"))
    import calendar as _cal
    ndays = _cal.monthrange(year, mon)[1]
    cells = []
    for dd in range(1, ndays + 1):
        day = f"{year:04d}-{mon:02d}-{dd:02d}"
        wd = datetime.fromisoformat(day + "T00:00:00+00:00").strftime("%a")
        if day in days:
            d = days[day]
            cells.append({
                "day_utc": day, "weekday": wd, "in_covered_history": True,
                "total_day_pnl_usd_eq": d["total_day_pnl_usd_eq"],
                "status": d["status"],
                "sleeves": d["sleeves"],
            })
        else:
            cells.append({"day_utc": day, "weekday": wd, "in_covered_history": False,
                          "status": "OUTSIDE_COVERAGE",
                          "reason": "ngoài phạm vi dữ liệu epoch-1 đã ghi (không phải ngày không giao dịch)"})
    # ISO week totals over days that have data
    weeks: dict = {}
    for c in cells:
        if not c.get("in_covered_history"):
            continue
        wk = pl.week_key(c["day_utc"])
        w = weeks.setdefault(wk, {"week": wk, "pnl": 0.0, "days": 0,
                                  "status": "OK"})
        w["pnl"] = round(w["pnl"] + (c.get("total_day_pnl_usd_eq") or 0.0), 2)
        w["days"] += 1
        if c["status"] not in ("OK", "NO_TRADE"):
            w["status"] = "PARTIAL"
    month_total = round(sum(c.get("total_day_pnl_usd_eq") or 0.0
                            for c in cells if c.get("in_covered_history")), 2)
    return {
        "schema": pl.CAL_SCHEMA, "month": month, "epoch": "epoch1_history",
        "label": "LỊCH SỬ CŨ (epoch-1, mô hình mỗi sleeve 100k) — KHÔNG cộng vào kỳ mới",
        "days": cells, "weeks": list(weeks.values()), "month_total_usd_eq": month_total,
        "note": ("Ngày OUTSIDE_COVERAGE = ngoài phạm vi dữ liệu đã ghi; "
                 "NO_TRADE = có dữ liệu và không có giao dịch. Hai trạng thái "
                 "không được gộp làm một."),
    }


def day_detail(date: str) -> dict:
    st = portfolio_state()
    row = next((d for d in st["epoch1"]["history_days"] if d["day_utc"] == date), None)
    fx = pl.fx_replay(pl.FX_DIR / "shadow_journal.jsonl")
    fx_trades = [t for t in fx["trades"] if t["day_utc"] == date]
    out: dict = {"day_utc": date, "epoch": "epoch1_history", "portfolio_row": row,
                 "fx_trades": fx_trades, "sleeves": {}}
    for fam in pl.CRYPTO_SLEEVES:
        series = pl.crypto_daily_series(pl.PSV1_RESULTS / f"valuation_marks/{fam}.jsonl")
        r = next((x for x in series["rows"] if x.get("day_utc") == date), None)
        out["sleeves"][fam] = r or {"status": pl.UNAVAILABLE,
                                    "reason": "no valuation mark on this UTC day"}
    return out


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj: dict) -> None:
        self._send(200, "application/json",
                   json.dumps(obj, ensure_ascii=False, default=str).encode())

    def do_GET(self) -> None:  # GET-only server by design (no order surface)
        url = urlparse(self.path)
        path, q = url.path, parse_qs(url.query)
        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8",
                       (HERE / "index.html").read_bytes())
        elif path == "/logo.jpg":
            for cand in (HERE / "assets/logo.jpg", HERE / "logo.jpg"):
                if cand.exists():
                    self._send(200, "image/jpeg", cand.read_bytes())
                    return
            self._send(404, "text/plain", b"no logo")
        elif path == "/state.json":
            try:
                self._send(200, "application/json",
                           (pl.FX_DIR / "shadow_state.json").read_bytes())
            except FileNotFoundError:
                self._json({"data_stale": True, "marks_fresh": False,
                            "account": None, "sleeves": {}})
        elif path == "/journal.jsonl":
            try:
                data = (pl.FX_DIR / "shadow_journal.jsonl").read_bytes()
            except FileNotFoundError:
                data = b""
            try:
                limit = int(q.get("limit", ["0"])[0])
            except ValueError:
                limit = 0
            if limit > 0:
                lines = data.decode("utf-8", "replace").splitlines()[-limit:]
                data = ("\n".join(lines) + "\n").encode()
            self._send(200, "application/x-ndjson", data)
        elif path == "/equity_curve.json":
            try:
                self._send(200, "application/json",
                           (pl.FX_DIR / "equity_curve.json").read_bytes())
            except FileNotFoundError:
                self._json({"schema": "phorec.equity_curve@1", "points": []})
        elif path == "/health.json":
            now = datetime.now(timezone.utc)
            hb_age = None
            try:
                hb = json.loads((pl.FX_DIR / "daemon_heartbeat.json").read_text())
                ts = str(hb.get("pid_heartbeat_utc", ""))
                if ts:
                    moment = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hb_age = max(0.0, (now - moment).total_seconds())
            except Exception:
                hb_age = None
            self._json({
                "schema": "phorec.health@1",
                "server_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "daemon_alive": hb_age is not None and hb_age <= DAEMON_FRESH_SEC,
                "heartbeat_age_s": None if hb_age is None else round(hb_age, 1),
                "state_age_s": None,
                "daemon_fresh_threshold_s": DAEMON_FRESH_SEC,
            })
        elif path == "/portfolio.json":
            self._json(portfolio_state())
        elif path == "/calendar.json":
            month = (q.get("month") or [time.strftime("%Y-%m")])[0]
            self._json(calendar(month))
        elif path == "/day.json":
            date = (q.get("date") or [time.strftime("%Y-%m-%d")])[0]
            self._json(day_detail(date))
        elif path == "/sources.json":
            self._json({"sources": portfolio_state()["source_manifest"]})
        else:
            self._send(404, "text/plain", b"not found")

    def log_message(self, *a) -> None:
        pass


if __name__ == "__main__":
    print(f"phorec2 (PREVIEW, epoch2 NOT activated) → http://127.0.0.1:{PORT}/")
    print("review build — does not touch 8765/8766 or any worker")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
