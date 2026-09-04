#!/usr/bin/env python3
"""V14 P1 A3 follow-up probes (continues evidence numbering at 0399).

Scope (three targeted items left open by probe_binance_sources.py):
1. /fapi/v1/indexPriceKlines documents a `pair` parameter (not `symbol`);
   the first pass used `symbol` and returned HTTP 400. Re-probe with `pair`.
2. /futures/data/basis MEASURED depth contradicts its documented 30-day bound
   (screen-window point anchors returned rows at 2025-08-22 for all four
   symbols). Bracket the true origin with coarse point anchors and add
   window-end (2026-08-21) + 15m screen-start anchors.
3. The backward walk is NOT a valid depth instrument for /futures/data/basis
   (the endpoint repeats the latest page once endTime precedes the oldest
   bucket); point anchors honoring startTime/endTime are used instead —
   verified from archived row timestamps.

Budget: this script makes at most 21 requests (cumulative total <= 419).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import probe_binance_sources as P  # noqa: E402

runner = P.ProbeRunner()
runner.count = 398  # continue the lane's global probe numbering


def main() -> int:
    results: dict = {"schema": "v14_p1_a3_probe_followup_v1", "started_utc": P.now_utc_iso(),
                     "finished_utc": None, "items": {}}

    # ---- 1. indexPriceKlines with the documented `pair` param ---------------
    block = {"endpoint": "/fapi/v1/indexPriceKlines", "param_style": "pair", "symbols": {}}
    for symbol in P.SYMBOLS:
        rec = runner.get(f"index_price_klines_{symbol}_pair_semantics",
                         "/fapi/v1/indexPriceKlines",
                         {"pair": symbol, "interval": "15m", "limit": 3},
                         archive_rows=3, first_ts_key=None, last_ts_key=None)
        entry = {"semantics": {"probe_id": rec["probe_id"], "http_status": rec["http_status"],
                               "latest_row_ms": rec["last_row_ms"],
                               "latest_row_utc": rec["last_row_utc"]}}
        if symbol == "BTCUSDT":
            listing = runner.get("index_price_klines_BTCUSDT_pair_listing",
                                 "/fapi/v1/indexPriceKlines",
                                 {"pair": symbol, "interval": "15m",
                                  "startTime": P.LISTING_PROBE_MS, "limit": 2},
                                 archive_rows=2, first_ts_key=None, last_ts_key=None)
            rows = [int(r[0]) for r in (listing.get("archived_response") or []) if isinstance(r, list)]
            entry["listing_probe"] = {"probe_id": listing["probe_id"],
                                      "http_status": listing["http_status"],
                                      "first_row_ms": rows[0] if rows else None,
                                      "first_row_utc": P.utc_iso(rows[0]) if rows else None}
            wend = runner.get("index_price_klines_BTCUSDT_pair_windowend",
                              "/fapi/v1/indexPriceKlines",
                              {"pair": symbol, "interval": "15m",
                               "startTime": P.SCREEN_END_MS - P.PERIOD_MS["15m"],
                               "endTime": P.SCREEN_END_MS, "limit": 2},
                              archive_rows=2, first_ts_key=None, last_ts_key=None)
            entry["screen_end_coverage"] = {"probe_id": wend["probe_id"],
                                            "exists": bool(wend.get("row_count")),
                                            "row_ms": wend.get("first_row_ms")}
        wstart = runner.get(f"index_price_klines_{symbol}_pair_windowstart",
                            "/fapi/v1/indexPriceKlines",
                            {"pair": symbol, "interval": "15m",
                             "startTime": P.SCREEN_START_MS,
                             "endTime": P.SCREEN_START_MS + P.PERIOD_MS["15m"], "limit": 2},
                            archive_rows=2, first_ts_key=None, last_ts_key=None)
        entry["screen_start_coverage"] = {"probe_id": wstart["probe_id"],
                                          "exists": bool(wstart.get("row_count")),
                                          "row_ms": wstart.get("first_row_ms")}
        block["symbols"][symbol] = entry
    results["items"]["index_price_klines_pair"] = block

    # ---- 2./3. basis true-depth brackets and window anchors -----------------
    block = {"endpoint": "/futures/data/basis", "method": "point_anchor", "anchors": {}}
    def basis_anchor(slug, symbol, period, at_ms):
        res = P.anchor_exists(runner, "basis", "/futures/data/basis", "pair", symbol,
                              period, at_ms)
        block["anchors"].setdefault(slug, {})[symbol] = res
    # coarse origin brackets on BTCUSDT 5m
    for slug, at in [
        ("authorized_start_2024_08_20", P.AUTH_START_MS),
        ("2023_01_01", int(P.datetime(2023, 1, 1, tzinfo=P.timezone.utc).timestamp() * 1000)),
        ("2019_12_01", int(P.datetime(2019, 12, 1, tzinfo=P.timezone.utc).timestamp() * 1000)),
    ]:
        basis_anchor(slug, "BTCUSDT", "5m", at)
    # window-end anchors (blind-S0 screen end) at 5m, all symbols
    for symbol in P.SYMBOLS:
        basis_anchor("screen_end_2026_08_21_5m", symbol, "5m", P.SCREEN_END_MS)
    # 15m screen-start anchors, all symbols
    for symbol in P.SYMBOLS:
        basis_anchor("screen_start_2025_08_22_15m", symbol, "15m", P.SCREEN_START_MS)
    results["items"]["basis_depth_brackets"] = block

    results["finished_utc"] = P.now_utc_iso()
    results["request_budget"] = {"this_script": runner.count - 398,
                                 "cumulative_lane": runner.count,
                                 "hard_cap": P.HARD_CAP}
    out = Path(__file__).resolve().parent / "probe_results_followup.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"request_budget": results["request_budget"], "output": str(out)},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
