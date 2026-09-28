"""PhorecOne — single minimal .app backend (gate A preview, port 8768).

GET-only loopback server for the ONE-account two-sleeve view
(FX-RANGEFADE-2M + BTC4H-BANDRIDGE). Read-only: no order surface of any
kind (pinned by tests); closing the app never touches workers; the old
dashboards (8765/8766/8791) are untouched.
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
from one import read_model as rm  # noqa: E402
import portfolio_lib as pl  # noqa: E402

HERE = Path(__file__).resolve().parent
PORT = 8768
_cache: dict = {"key": None, "state": None}


def _mtime_key() -> tuple:
    # the frozen app has no bundled epoch_config.json — track the LIVE
    # repo config so activation is picked up without a restart
    paths = [pl.FX_DIR / "shadow_journal.jsonl", pl.FX_DIR / "shadow_state.json",
             rm.BANDRIDGE_STATE, rm.BANDRIDGE_LEDGER,
             pl.PSV1_RESULTS / "valuation_marks/BTC4H-BANDRIDGE.jsonl",
             pl.HERE / "epoch_config.json", pl.CONFIG_FALLBACK]
    key = []
    for p in paths:
        try:
            key.append((str(p), p.stat().st_mtime_ns))
        except OSError:
            key.append((str(p), None))
    return tuple(key)


def one_state() -> dict:
    key = _mtime_key()
    if _cache["key"] != key or _cache["state"] is None:
        _cache["state"] = rm.build_one_state()
        _cache["key"] = key
    return _cache["state"]


def calendar(month: str) -> dict:
    st = one_state()
    ref = float((st["account"].get("usdt_usd_ref") or {}).get("rate", 1.0))
    year, mon = (int(x) for x in month.split("-"))
    import calendar as _cal
    ndays = _cal.monthrange(year, mon)[1]
    by_day = {d["day_utc"]: d for d in st["history_days"]}
    cells, weeks = [], {}
    for dd in range(1, ndays + 1):
        day = f"{year:04d}-{mon:02d}-{dd:02d}"
        if day in by_day:
            d = by_day[day]
            # totals are USD-eq: USDT sleeve PnL joins through the DECLARED
            # reference (1:1 reporting assumption), never unconverted
            br_pnl = d["sleeves"]["BTC4H-BANDRIDGE"].get("day_pnl")
            total = (d["sleeves"]["FX-RANGEFADE-2M"]["day_realized_usd"]
                     + (br_pnl * ref if br_pnl is not None else 0.0))
            cells.append({"day_utc": day, "covered": True,
                          "total_day_pnl_usd_eq": round(total, 2),
                          "sleeves": d["sleeves"],
                          "status": ("PARTIAL" if any(
                              s.get("status") not in ("OK", "NO_TRADE")
                              for s in d["sleeves"].values()) else "OK")})
            wk = pl.week_key(day)
            w = weeks.setdefault(wk, {"week": wk, "pnl": 0.0, "days": 0})
            w["pnl"] = round(w["pnl"] + (total), 2)
            w["days"] += 1
        else:
            cells.append({"day_utc": day, "covered": False, "status": "OUTSIDE_COVERAGE",
                          "reason": "ngoài phạm vi dữ liệu epoch-1 đã ghi"})
    month_total = round(sum(c.get("total_day_pnl_usd_eq") or 0.0
                            for c in cells if c.get("covered")), 2)
    return {"schema": pl.CAL_SCHEMA, "month": month, "epoch": "epoch1_reference",
            "usdt_usd_ref": ref,
            "label": ("Lịch tham chiếu từ sách epoch-1 (2 sleeve được mount; "
                      "USDT×ref) — KHÔNG phải PnL của tài khoản $100k mới"),
            "days": cells, "weeks": list(weeks.values()),
            "month_total_usd_eq": month_total}


def day_detail(date: str) -> dict:
    st = one_state()
    row = next((d for d in st["history_days"] if d["day_utc"] == date), None)
    fx = st["sleeves"]["FX-RANGEFADE-2M"]
    return {"day_utc": date, "portfolio_row": row,
            "fx_trades": [t for t in fx["closed_trades"]
                          if t.get("day_utc") == date]}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # GET-only by design (no order surface)
        url = urlparse(self.path)
        path, q = url.path, parse_qs(url.query)
        # frozen bundles put --add-data files at MEIPASS root while this
        # module lives under MEIPASS/one/ — try both neighborhoods
        page_candidates = [HERE / "index.html", HERE.parent / "index.html"]
        logo_candidates = [HERE / "assets/logo.jpg", HERE / "logo.jpg",
                           HERE.parent / "assets/logo.jpg", HERE.parent / "logo.jpg"]
        if path in ("/", "/index.html"):
            for cand in page_candidates:
                if cand.exists():
                    self._send(200, "text/html; charset=utf-8", cand.read_bytes())
                    return
            self._send(500, "text/plain", b"index.html missing")
        elif path == "/logo.jpg":
            for cand in logo_candidates:
                if cand.exists():
                    self._send(200, "image/jpeg", cand.read_bytes())
                    return
            self._send(404, "text/plain", b"no logo")
        elif path == "/one.json":
            self._send(200, "application/json",
                       json.dumps(one_state(), ensure_ascii=False,
                                  default=str).encode())
        elif path == "/calendar.json":
            month = (q.get("month") or [time.strftime("%Y-%m")])[0]
            self._send(200, "application/json",
                       json.dumps(calendar(month), ensure_ascii=False).encode())
        elif path == "/day.json":
            date = (q.get("date") or [time.strftime("%Y-%m-%d")])[0]
            self._send(200, "application/json",
                       json.dumps(day_detail(date), ensure_ascii=False).encode())
        elif path == "/sources.json":
            self._send(200, "application/json",
                       json.dumps({"sources": one_state()["source_manifest"]},
                                  ensure_ascii=False).encode())
        elif path == "/health.json":
            now = datetime.now(timezone.utc)
            hb_age = None
            try:
                hb = json.loads((pl.FX_DIR / "daemon_heartbeat.json").read_text())
                ts = str(hb.get("pid_heartbeat_utc", ""))
                if ts:
                    hb_age = max(0.0, (now - datetime.fromisoformat(
                        ts.replace("Z", "+00:00"))).total_seconds())
            except Exception:
                hb_age = None
            self._send(200, "application/json", json.dumps({
                "schema": "phorec.health@1",
                "server_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "daemon_alive": hb_age is not None and hb_age <= 90,
                "heartbeat_age_s": None if hb_age is None else round(hb_age, 1),
                "state_age_s": None,
                "daemon_fresh_threshold_s": 90,
            }).encode())
        else:
            self._send(404, "text/plain", b"not found")

    def log_message(self, *a) -> None:
        pass


if __name__ == "__main__":
    print(f"PhorecOne (gate A preview, epoch2 NOT activated) → http://127.0.0.1:{PORT}/")
    print("read-only; old dashboards 8765/8766/8791 untouched")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
