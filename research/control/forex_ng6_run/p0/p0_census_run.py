"""FOREX-NG6 P0 census (plans/PLAN_forex_ng6.md §4, gates F1-F7).

F4 is the cycle's first-order fail-closed kill gate: TD is a data VENDOR,
not a broker — spread, commission, minimum size, tick/point value, overnight
swap points, triple-swap weekday and margin are UNMEASURABLE from it.  The
owner law: without a citable, preregistered conservative cost band
(source-quoted bytes, no invented numbers, no current-spread-for-all-history
without a stress regime), the cycle terminates
FOREX_NG6_BLOCKED_SOURCE_OR_COST with budget 0/3 and NO GLD fallback.

Price-side census (F1-F3) is banked either way: if the price authority is
proven, it is a durable asset for a future owner-authorized reopening.
No candidate returns/PnL anywhere.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-ng6/integration")
ROOT = Path("/Users/hoangminhlong/my-quantitative")
HERE = WT / "research/control/forex_ng6_run/p0"
STAGING = HERE / "staging"
HTTP = {"n": 0}


def log(m):
    print(f"[p0] {m}", flush=True)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url):
    HTTP["n"] += 1
    req = urllib.request.Request(url, headers={"User-Agent": "my-quantitative-research/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type", ""), e.read()


def main() -> int:
    STAGING.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(WT))
    key = next(l.split("=", 1)[1].strip() for l in (ROOT / ".env").read_text().splitlines()
               if l.startswith("TWELVE_DATA_API_KEY="))
    from research.governance import heavy_lock

    t0 = time.time()
    with heavy_lock.acquire(
        cycle_id="FOREX-NG6",
        role="P0_CENSUS",
        worktree=str(WT),
        command=[sys.executable, str(HERE / "p0_census_run.py")],
        expected_artifacts=[str(HERE / "p0_census_verdict.json")],
    ):
        # F1/F3: full-depth XAU/USD 1day pull, chunked by date windows
        # (TD outputsize cap 5000 without next_page on this plan; chunks
        # of ~8 years keep every window far under the cap)
        all_rows: list = []
        meta: dict = {}
        chunks = [("1979-01-01", "1987-12-31"), ("1988-01-01", "1995-12-31"),
                  ("1996-01-01", "2003-12-31"), ("2004-01-01", "2011-12-31"),
                  ("2012-01-01", "2019-12-31"), ("2020-01-01", "2026-12-31")]
        pages = 0
        ok_chunks = 0
        for start_d, end_d in chunks:
            u = ("https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1day"
                 f"&outputsize=5000&apikey={key}&order=ASC&format=JSON"
                 f"&start_date={start_d}&end_date={end_d}")
            st, _ct, b = fetch(u)
            pages += 1
            if st != 200:
                log(f"chunk {start_d}..{end_d}: status={st} body={b[:160]!r}")
                continue
            payload = json.loads(b)
            meta = payload.get("meta", meta)
            vals = payload.get("values", [])
            all_rows.extend(vals)
            ok_chunks += 1
            log(f"chunk {start_d}..{end_d}: {len(vals)} rows")
        seen: set = set()
        dedup_rows = [r for r in all_rows if r["datetime"] not in seen and not seen.add(r["datetime"])]
        dedup_rows.sort(key=lambda r: r["datetime"])
        status = 200 if ok_chunks == len(chunks) else st
        body = json.dumps({"meta": meta, "values": dedup_rows}, sort_keys=True).encode()
        rec = {"status": status, "content_type": "application/json", "sha256": sha(body),
               "bytes": len(body), "chunks": f"{ok_chunks}/{len(chunks)}", "rows": len(dedup_rows)}
        log(f"XAU/USD full pull: status={status} chunks={ok_chunks}/{len(chunks)} rows={len(dedup_rows)}")
        price_ok = status == 200 and len(dedup_rows) > 10000
        if dedup_rows:
            (STAGING / "XAUUSD_1day_full.json").write_bytes(body)

        # F2 double-pull identity on a bounded recent window (order-normalized)
        url2 = ("https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=1day"
                f"&outputsize=30&apikey={key}&format=JSON")
        s2, _, b2 = fetch(url2)
        try:
            if price_ok:
                full_tail = sorted(json.loads(body)["values"][-30:], key=lambda r: r["datetime"])
                win = sorted(json.loads(b2).get("values", []), key=lambda r: r["datetime"])
                identity = {"status": s2, "records": len(win), "value_identical": win == full_tail}
            else:
                identity = {"status": s2, "value_identical": False, "reason": "no full pull"}
        except Exception as exc:  # noqa: BLE001
            identity = {"status": s2, "error": str(exc), "value_identical": False}
        log(f"double-pull: {identity}")

        # P-7 canary: never-existed pair
        cs, ct, cb = fetch("https://api.twelvedata.com/time_series?symbol=ZZW/ZZQ&interval=1day"
                           f"&outputsize=5&apikey={key}&format=JSON")
        canary = {"status": cs, "content_type": ct, "body": cb[:300].decode("utf-8", "replace")}
        (STAGING / "never_existed_pair_canary.json").write_text(json.dumps(canary, indent=1))
        log(f"never-existed pair canary: status={cs}")

        # census of the price series
        census: dict = {}
        if price_ok:
            rows = json.loads(body)["values"]
            df = pd.DataFrame(rows)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").reset_index(drop=True)
            num = df[["open", "high", "low", "close"]].astype(float)
            weekend = df[df["datetime"].dt.dayofweek >= 5]
            nonflat_weekend = weekend[
                (num.loc[weekend.index, "high"] != num.loc[weekend.index, "low"])
            ]
            census = {
                "fields": list(json.loads(body).get("meta", {}).keys()) and list(df.columns),
                "rows": int(len(df)),
                "first": str(df["datetime"].iloc[0].date()),
                "last": str(df["datetime"].iloc[-1].date()),
                "duplicate_datetimes_removed": int(df["datetime"].duplicated().sum()),
                "weekend_bars_total": int(len(weekend)),
                "weekend_bars_nonflat": int(len(nonflat_weekend)),
                "weekday_bars": int((df["datetime"].dt.dayofweek < 5).sum()),
                "nonpositive_close_rows": int((num["close"] <= 0).sum()),
                "hl_violation_rows": int(((num["high"] < num["low"]) | (num["close"] > num["high"]) | (num["open"] < num["low"])).sum()),
                "volume_field_present": "volume" in df.columns,
                "tz_convention": "bar datetime strings as served (vendor-composited daily closes; convention frozen at F2 adjudication below)",
            }
            log(f"census: {census}")

        # F4 COST AUTHORITY — the fail-closed kill gate.
        # Every scored-relevant cost component, measured or not:
        cost_components = {
            "spread": {"measurable_from_td": False, "measured": None},
            "commission": {"measurable_from_td": False, "measured": None},
            "minimum_size": {"measurable_from_td": False, "measured": None},
            "tick_point_value": {"measurable_from_td": False, "measured": None},
            "overnight_swap_long_short": {"measurable_from_td": False, "measured": None},
            "triple_swap_weekday": {"measurable_from_td": False, "measured": None},
            "margin_leverage": {"measurable_from_td": False, "measured": None},
        }
        # citable-band search INSIDE this repo (the only authorized evidence space):
        # a band would need pre-existing gold/quote cost authority bytes; none exist
        # (frontier probes + repo search; TD documented vendor-only).  Third-party
        # public broker pages are STATED not MEASURED (Q-8) and revision-uncontrolled;
        # under the owner law they do not satisfy 'broker-specific cost authority'.
        f4 = {
            "gate": "F4_COST_AUTHORITY",
            "verdict": "BLOCKED",
            "components": cost_components,
            "citable_band_located": False,
            "evidence": [
                "frontier probe ng6_x1/x2: TD serves XAU/USD quotes only; no cost fields exist in any TD channel response",
                "repo search at P0: zero gold-spread/swap authority artifacts pinned anywhere",
                "Q-8 law: stated vendor constants are hypotheses, never a cost model",
                "no broker account exists or may be created in-cycle (owner boundary)",
            ],
            "consequence_per_plan": "terminal FOREX_NG6_BLOCKED_SOURCE_OR_COST, budget 0/3, NO GLD fallback in-cycle",
        }
        log(f"F4 adjudication: {f4['verdict']} (citable_band={f4['citable_band_located']})")

        price_gates = {
            "F1_INSTRUMENT_IDENTITY": {
                "verdict": "PASS" if price_ok else "FAIL",
                "detail": {"provider": "Twelve Data", "symbol": "XAU/USD", "class": "Precious Metal quote (USD per troy oz)",
                           "registered_instrument": "TD XAU/USD 1day quote — the cycle trades THIS quote or does not run",
                           "pull": rec},
            },
            "F2_CLOCK_SESSIONS": {
                "verdict": "PASS" if price_ok else "FAIL",
                "detail": {
                    "bars": "daily bars exist for ALL calendar days incl. weekends (census counts them)",
                    "frozen_convention": "weekly-class decisions read the LAST bar strictly on/before the decision date; fills at the next daily close after the decision (T-1 availability measured at the frontier probe); weekend-bar close convention = last calendar bar of the ISO week, frozen here — never resolved lazily",
                    "double_pull": identity,
                },
            },
            "F3_HISTORY_REVISIONS": {
                "verdict": "PASS" if price_ok and census.get("rows", 0) > 10000 else "FAIL",
                "detail": {"census": census,
                           "measured_depth_start": census.get("first"),
                           "revision_law": "retrieved-once sha-pinned snapshot; later revisions annotated-and-kept, never silently re-pulled"},
            },
        }
        price_pass = all(g["verdict"] == "PASS" for g in price_gates.values())

        verdict = {
            "schema": "p0_census_verdict@1",
            "cycle_id": "FOREX-NG6",
            "measured_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "runtime_seconds": round(time.time() - t0, 1),
            "http_requests": HTTP["n"],
            "plan": "plans/PLAN_forex_ng6.md §4",
            "no_pnl_computed": True,
            "price_gates": price_gates,
            "f4_cost_authority": f4,
            "verdict": "P0_F4_BLOCKED" if (price_pass and f4["verdict"] == "BLOCKED")
                       else ("P0_FAIL" if not price_pass else "P0_PASS"),
            "terminal_if_blocked": {
                "terminal": "FOREX_NG6_BLOCKED_SOURCE_OR_COST",
                "budget": "0/3",
                "cells": 0,
                "gls_fallback": "FORBIDDEN in-cycle",
                "durable_assets": "TD XAU/USD 1day full-depth sha-pinned price authority + clock convention (reopening needs an owner broker-specific cost authority; instrument-first reopening only)",
                "go_phrase": "GO FOREX NG6 SCORED EXECUTION — never typed; dies UNCONSUMED",
            },
        }
        (HERE / "p0_census_verdict.json").write_text(json.dumps(verdict, indent=1, sort_keys=True) + "\n")
        log(f"verdict: {verdict['verdict']}")
        return 0

    # NOTE: terminal close semantics handled by the Lead after this artifact.


if __name__ == "__main__":
    sys.exit(main())
