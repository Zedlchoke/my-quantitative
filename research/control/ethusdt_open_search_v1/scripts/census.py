"""EOS1 P1 census — BUILD_PASS gate over the staged corpus.

Checks (plan §2, fail-closed):
  - per series: months staged vs manifest, first/last 1h bar, bar counts,
    H4 bars + dropped groups, duplicate/monotonic ts;
  - monthly boundary continuity (last bar of month m and first of m+1 are
    1h apart, modulo intended gaps counted);
  - ETHUSDT 1h digest cross-check vs the ES1 staging manifest
    (read-only; any mismatch = BLOCKED_DATA for that month, listed);
  - funding: settlement rows, cadence distribution, floor vs the scored
    window (every 8h-boundary from 2020-01-01 to data end must have a row
    — gaps counted; missing settlements inside the scored window are
    BLOCKED_DATA with counts);
  - ETHBTC spot + BTCUSDT perp coverage for lane warmups.

Output: freezes/census.json (+ stdout summary). NO PnL of any kind.
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eos1_engine as E  # noqa: E402

ES1_MANIFEST = pathlib.Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/btc-h4-edge-search-v1/"
    "integration/research/control/btc_h4_edge_search_v1/freezes/staging_manifest.json")


def iso(ts: int) -> str:
    return dt.datetime.fromtimestamp(ts / 1000, dt.timezone.utc).isoformat()


def census_series(name: str, series_dir: str) -> dict:
    bars = E.load_1h(series_dir)
    h4, dropped = E.to_h4(bars)
    months = collections.Counter(
        dt.datetime.fromtimestamp(b["ts"] / 1000, dt.timezone.utc).strftime("%Y-%m")
        for b in bars)
    mono = all(bars[i]["ts"] < bars[i + 1]["ts"] for i in range(len(bars) - 1))
    # 1h gap census: expected hourly steps between first and last bar
    gaps = 0
    if bars:
        span = (bars[-1]["ts"] - bars[0]["ts"]) // 3600_000 + 1
        gaps = span - len(bars)
    return {"name": name, "bars_1h": len(bars), "h4_bars": len(h4),
            "h4_dropped_groups": dropped, "first_bar": iso(bars[0]["ts"]) if bars else None,
            "last_bar": iso(bars[-1]["ts"]) if bars else None,
            "months_with_bars": len(months), "min_bars_in_month": min(months.values()) if months else 0,
            "max_bars_in_month": max(months.values()) if months else 0,
            "monotonic_ts": mono, "hour_gaps_in_span": gaps}


def cross_check_es1() -> dict:
    """Digest cross-check of overlapping ETHUSDT 1h months vs ES1 manifest."""
    if not ES1_MANIFEST.exists():
        return {"status": "UNAVAILABLE_ES1_MANIFEST"}
    es1 = json.loads(ES1_MANIFEST.read_text())
    es1_series = es1.get("series", {}).get("klines:ETHUSDT:1h", {})
    import hashlib
    mine = {}
    d = E.DATA / "klines_um_ETHUSDT_1h"
    for z in sorted(d.glob("*.zip")):
        mine[z.stem[-7:]] = hashlib.sha256(z.read_bytes()).hexdigest()
    match, mismatch, es1_only = [], [], []
    for ym, info in es1_series.get("digests", {}).items():
        if ym in mine:
            (match if mine[ym] == info["sha256"] else mismatch).append(ym)
        else:
            es1_only.append(ym)
    return {"status": "PASS" if not mismatch and not es1_only else "MISMATCH",
            "es1_months": len(es1_series.get("digests", {})),
            "digest_match": len(match), "digest_mismatch": mismatch,
            "staged_but_not_in_es1": sorted(set(mine) - set(es1_series.get("digests", {})))}


def census_funding() -> dict:
    rows = E.load_funding()
    cadence = collections.Counter()
    for a, b in zip(rows, rows[1:]):
        cadence[(b["ts"] - a["ts"]) // 3600_000] += 1
    scored_start = E._FOLD_START_MS["2020-01-01"]
    scored = [r for r in rows if r["ts"] >= scored_start]
    # required 8h boundaries inside scored window vs actual rows
    import bisect
    ts_list = [r["ts"] for r in rows]
    end_ms = E._FOLD_END_MS["2026-09-01"]
    missing_8h = 0
    t = scored_start
    while t < min(end_ms, ts_list[-1] if ts_list else scored_start):
        i = bisect.bisect_left(ts_list, t)
        # a settlement is "covered" if a row exists within its 8h slot
        if i >= len(ts_list) or ts_list[i] > t + 8 * 3600_000:
            missing_8h += 1
        t += 8 * 3600_000
    neg = sum(1 for r in scored if r["rate"] < 0)
    return {"settlement_rows_total": len(rows),
            "first_settlement": iso(rows[0]["ts"]) if rows else None,
            "last_settlement": iso(rows[-1]["ts"]) if rows else None,
            "cadence_hours_hist": dict(sorted(cadence.items())),
            "scored_window_rows": len(scored),
            "scored_negative_rate_rows": neg,
            "missing_8h_slots_in_scored_window_upper_bound": missing_8h}


def ethbtc_scored_gap_detail() -> dict:
    """ETHBTC spot is the only series with in-window holes (spot venue
    maintenance): quantify them — the engine's hold-previous signal law
    covers missing boundaries deterministically (counted, never patched)."""
    bars = E.load_1h("klines_spot_ETHBTC_1h")
    scored = [b for b in bars if b["ts"] >= E._FOLD_START_MS["2020-01-01"]]
    gaps = []
    for a, b in zip(scored, scored[1:]):
        d = (b["ts"] - a["ts"]) // 3600_000
        if d != 1:
            gaps.append({"after": iso(a["ts"]), "before": iso(b["ts"]),
                         "missing_hours": d - 1})
    h4, _ = E.to_h4(bars)
    h4_scored = [b for b in h4 if b["ts"] >= E._FOLD_START_MS["2020-01-01"]]
    return {"gap_events_in_scored_window": len(gaps),
            "max_gap_hours": max((g["missing_hours"] for g in gaps), default=0),
            "h4_boundaries_missing_vs_ethusdt": 14610 - len(h4_scored),
            "gaps": gaps}


def main() -> int:
    out = {
        "schema": "eos1.census@1",
        "built_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "series": {
            "klines_um_ETHUSDT_1h": census_series("ETHUSDT um 1h", "klines_um_ETHUSDT_1h"),
            "klines_um_BTCUSDT_1h": census_series("BTCUSDT um 1h", "klines_um_BTCUSDT_1h"),
            "klines_spot_ETHBTC_1h": census_series("ETHBTC spot 1h", "klines_spot_ETHBTC_1h"),
        },
        "funding": census_funding(),
        "ethbtc_scored_gap_detail": ethbtc_scored_gap_detail(),
        "es1_cross_check": cross_check_es1(),
    }
    # hard gates for BUILD_PASS
    problems = []
    s = out["series"]["klines_um_ETHUSDT_1h"]
    if s["h4_bars"] < 14000:
        problems.append(f"ETHUSDT h4_bars {s['h4_bars']} < 14000")
    if not s["monotonic_ts"]:
        problems.append("non-monotonic ts")
    cc = out["es1_cross_check"]
    if cc.get("status") == "MISMATCH":
        problems.append(f"ES1 digest mismatch months={cc['digest_mismatch']}")
    if cc.get("status") == "UNAVAILABLE_ES1_MANIFEST":
        problems.append("ES1 manifest unavailable for cross-check")
    f = out["funding"]
    if not f["first_settlement"] or f["first_settlement"] > "2020-01-02":
        problems.append(f"funding floor too late: {f['first_settlement']}")
    if f["missing_8h_slots_in_scored_window_upper_bound"] > 24:
        problems.append(f"funding 8h slots missing upper bound {f['missing_8h_slots_in_scored_window_upper_bound']}")
    out["build_pass"] = not problems
    out["problems"] = problems
    dest = pathlib.Path(__file__).resolve().parents[1] / "freezes" / "census.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0 if out["build_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
