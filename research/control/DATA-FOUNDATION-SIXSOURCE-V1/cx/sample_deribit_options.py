#!/usr/bin/env python3
"""Deribit crypto options keyless sample — lane CX, DATA-FOUNDATION-SIXSOURCE-V1.

PROSPECTIVE_FROM_2026-09-28 — from-today market-state sample, NOT historical data.

License screen (recorded BEFORE first call, 2026-09-28, controller session):
  - Docs: https://docs.deribit.com/ (mirrored markdown: /articles/authentication.md,
    /articles/api-usage-policy.md, /articles/rate-limits.md)
  - Verified quote 1: "Public API methods (market data, etc.) do not require
    authentication" (Authentication article).
  - Verified quote 2: "All API traffic, whether authenticated or public, must
    follow Deribit's broader trading-integrity rules" (API Usage Policy);
    market-data polling should prefer WebSocket; excessive usage -> stricter
    rate limits.
  - Ruling: keyless public market-data access permitted under fair-use policy;
    this sampler makes <=25 sequential REST calls at >=1 s spacing, internal
    research only. No explicit redistribution clause was located in the pages
    screened — disclosure: sample is not redistributed beyond this lane's
    evidence root.

Calls (<=25 hard cap, sequential >=1 s):
  1) GET /api/v2/public/get_instruments?currency=BTC&kind=option&expired=false
     -> chain membership census (expiries, instruments, strikes per expiry).
  2) ONE nearest expiry; 5 strikes nearest the median strike x {C,P} =
     up to 10 x GET /api/v2/public/ticker?instrument_name=...

Outputs (outside git, under <outdir>):
  Deribit_sample_<ts>.json        raw responses verbatim + request log
  Deribit_sample_<ts>_rows.json   sanitized flat rows
  options_manifest.json           sha256/bytes per file
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone

import requests

LABEL = "PROSPECTIVE_FROM_2026-09-28"
BASE = "https://www.deribit.com/api/v2"
MAX_REQUESTS = 25
MIN_SPACING_S = 1.0
MIN_FREE_BYTES = 5 * 1024**3

TERMS = {
    "docs_url": "https://docs.deribit.com/",
    "auth_article": "https://docs.deribit.com/articles/authentication.md",
    "usage_policy": "https://docs.deribit.com/articles/api-usage-policy.md",
    "site_terms_url": "https://www.deribit.com/pages/terms (JS-rendered; title verified)",
    "ruling": (
        "Public API methods (market data) do not require authentication per official docs; "
        "fair-use API Usage Policy applies to all traffic; keyless, <=25 sequential calls "
        "at >=1 s, internal research only, no redistribution. Redistribution clause not "
        "located in screened pages (disclosed)."
    ),
    "screened_at_utc": None,
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def df_free_bytes(path: str) -> int:
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize


class Session:
    def __init__(self):
        self.count = 0
        self.log: list[dict] = []
        self.last = 0.0

    def get(self, path: str, params: dict | None = None) -> dict:
        if self.count >= MAX_REQUESTS:
            raise RuntimeError(f"request cap {MAX_REQUESTS} reached")
        wait = MIN_SPACING_S - (time.monotonic() - self.last)
        if wait > 0:
            time.sleep(wait)
        url = BASE + path
        t0 = time.monotonic()
        resp = requests.get(url, params=params or {}, timeout=20)
        dt = (time.monotonic() - t0) * 1000.0
        self.count += 1
        self.last = time.monotonic()
        entry = {
            "n": self.count,
            "method": "GET",
            "url": url,
            "params": params or {},
            "http_status": resp.status_code,
            "latency_ms": round(dt, 1),
            "receive_utc": utcnow_iso(),
        }
        self.log.append(entry)
        print(f"[{self.count:02d}] {resp.status_code} {round(dt,1):>7}ms {path} {params or ''}")
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} from {url}: {resp.text[:300]}")
        body = resp.json()
        if body.get("error") is not None:
            raise RuntimeError(f"Deribit error on {url}: {body['error']}")
        return body


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--outdir",
        default=os.path.expanduser("~/.my-quantitative-data/sixsource-foundation-v1/options"),
    )
    args = ap.parse_args()
    outdir = os.path.abspath(os.path.expanduser(args.outdir))
    os.makedirs(outdir, exist_ok=True)

    free = df_free_bytes(outdir)
    if free < MIN_FREE_BYTES:
        print(f"ABORT: df below floor ({free/1024**3:.2f} GiB free)")
        return 2
    TERMS["screened_at_utc"] = utcnow_iso()
    print(f"df check OK: {free/1024**3:.2f} GiB free; terms screen recorded before first call")

    sess = Session()
    doc: dict = {
        "label": LABEL,
        "law": (
            "PROSPECTIVE_FROM_2026-09-28: from-today market-state sample, NOT historical "
            "data; no backtestable-history claim permitted."
        ),
        "terms": TERMS,
        "df_free_gib": round(free / 1024**3, 2),
        "started_utc": utcnow_iso(),
        "census": None,
        "tickers": [],
        "request_log": sess.log,
        "ended_utc": None,
        "stop_reason": None,
    }

    try:
        # 1) chain membership census
        body = sess.get("/public/get_instruments", {"currency": "BTC", "kind": "option", "expired": "false"})
        instruments = body["result"]
        now_ms = int(time.time() * 1000)
        by_expiry: dict[int, list[dict]] = {}
        for ins in instruments:
            by_expiry.setdefault(int(ins["expiration_timestamp"]), []).append(ins)
        census_exp = []
        for exp in sorted(by_expiry):
            ins_list = by_expiry[exp]
            strikes = sorted({int(i["strike"]) for i in ins_list})
            census_exp.append(
                {
                    "expiration_timestamp_ms": exp,
                    "expiry_iso": datetime.fromtimestamp(exp / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
                    "instruments": len(ins_list),
                    "calls": sum(1 for i in ins_list if i.get("option_type") == "call"),
                    "puts": sum(1 for i in ins_list if i.get("option_type") == "put"),
                    "n_strikes": len(strikes),
                    "strike_min": strikes[0] if strikes else None,
                    "strike_max": strikes[-1] if strikes else None,
                    "is_past": exp < now_ms,
                }
            )
        future = [e for e in census_exp if not e["is_past"]]
        target = future[0] if future else None
        doc["census"] = {
            "currency": "BTC",
            "kind": "option",
            "expired": "false",
            "n_instruments_total": len(instruments),
            "n_expiries_total": len(census_exp),
            "expiries": census_exp,
            "selected_expiry": target,
        }
        if target is None:
            doc["stop_reason"] = "NO_FUTURE_EXPIRY_FOUND"
            raise RuntimeError("no future expiry in census")

        # 2) pick ONE nearest expiry; 5 strikes nearest median x {C,P} -> <=10 tickers
        #    Instrument names are taken VERBATIM from the census payload (no name
        #    construction — Deribit uses DDMONYY expiry tokens, e.g. BTC-28SEP26-83000-C).
        exp_ins = by_expiry[target["expiration_timestamp_ms"]]
        strikes = sorted({int(i["strike"]) for i in exp_ins})
        med = strikes[len(strikes) // 2]
        five = sorted(strikes, key=lambda k: abs(k - med))[:5]
        sel = []
        for k in sorted(five):
            for side in ("call", "put"):
                nm = next(
                    i["instrument_name"]
                    for i in exp_ins
                    if int(i["strike"]) == k and i.get("option_type") == side
                )
                sel.append(nm)
        doc["selection_rule"] = (
            "ONE nearest (soonest) future expiry; 5 strikes nearest the median strike of "
            "that expiry, each sampled for call and put; instrument names taken verbatim "
            "from the get_instruments census payload."
        )
        doc["selected_instruments"] = sel

        ticker_errors = []
        for name in sel:
            if sess.count >= MAX_REQUESTS:
                doc["stop_reason"] = "REQUEST_CAP_25"
                break
            try:
                tb = sess.get("/public/ticker", {"instrument_name": name})
            except Exception as exc:  # noqa: BLE001
                ticker_errors.append({"instrument_name": name, "error": str(exc)[:300]})
                continue
            doc["tickers"].append({"instrument_name": name, "result": tb["result"]})
        if ticker_errors:
            doc["ticker_errors"] = ticker_errors
    except Exception as exc:  # noqa: BLE001
        doc["stop_reason"] = doc["stop_reason"] or f"ERROR: {type(exc).__name__}: {exc}"
        print("ERROR:", exc)

    doc["ended_utc"] = utcnow_iso()
    doc["requests_used"] = sess.count

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = os.path.join(outdir, f"Deribit_sample_{ts}.json")
    with open(raw_path, "w") as f:
        json.dump(doc, f, indent=2)

    # sanitized flat rows
    rows = []
    for t in doc["tickers"]:
        r = t["result"]
        rows.append(
            {
                "label": LABEL,
                "instrument_name": r.get("instrument_name"),
                "receive_utc": next(
                    (e["receive_utc"] for e in doc["request_log"]
                     if e.get("params", {}).get("instrument_name") == r.get("instrument_name")),
                    None,
                ),
                "timestamp_ms": r.get("timestamp"),
                "state": r.get("state"),
                "best_bid_price": r.get("best_bid_price"),
                "best_bid_amount": r.get("best_bid_amount"),
                "best_ask_price": r.get("best_ask_price"),
                "best_ask_amount": r.get("best_ask_amount"),
                "mark_price": r.get("mark_price"),
                "mark_iv": r.get("mark_iv"),
                "bid_iv": r.get("bid_iv"),
                "ask_iv": r.get("ask_iv"),
                "greeks_delta": (r.get("greeks") or {}).get("delta"),
                "greeks_gamma": (r.get("greeks") or {}).get("gamma"),
                "greeks_vega": (r.get("greeks") or {}).get("vega"),
                "greeks_theta": (r.get("greeks") or {}).get("theta"),
                "greeks_rho": (r.get("greeks") or {}).get("rho"),
                "underlying_price": r.get("underlying_price"),
                "underlying_index": r.get("underlying_index"),
                "index_price": r.get("index_price"),
                "open_interest": r.get("open_interest"),
                "interest_rate": r.get("interest_rate"),
            }
        )
    rows_path = os.path.join(outdir, f"Deribit_sample_{ts}_rows.json")
    with open(rows_path, "w") as f:
        json.dump(rows, f, indent=2)

    manifest = {
        "label": LABEL,
        "kind": "manifest",
        "files": sorted(
            (
                {"file": fn, "bytes": os.path.getsize(os.path.join(outdir, fn)),
                 "sha256": sha256_of_file(os.path.join(outdir, fn))}
                for fn in os.listdir(outdir)
                if (fn.startswith("Deribit_sample_") or fn == "options_manifest.json")
                and fn != "options_manifest.json"
            ),
            key=lambda e: e["file"],
        ),
        "requests_used": sess.count,
        "max_requests": MAX_REQUESTS,
        "stop_reason": doc["stop_reason"],
        "written_utc": utcnow_iso(),
    }
    with open(os.path.join(outdir, "options_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("manifest written:", os.path.join(outdir, "options_manifest.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
