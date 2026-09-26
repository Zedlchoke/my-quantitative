"""ERP1-TRACKA-COHORT-2 — F-6 fold-population CENSUS (COUNTS ONLY).

For each anchor (P3-A home AUDUSD / replicate USDCAD; P3-B home USDCAD /
replicate AUDUSD), per fold F1..F6 (frozen traded-day-count fold table from
t2_planes_manifest.json) and the last-6-months dev window (2025-07-01..
2025-12-31):
  - n_decision_bars  (law decision opportunities in the window)
  - n_occupied_bars  (target array != 0 in the window)
  - n_round_trips    (engine.run_strategy on the dev plane with the anchor
                      target; warmup honored; counts + entry/exit timestamps
                      ONLY — the engine's pips/px/equity outputs are stripped
                      at source and never persisted, and no PnL field exists
                      anywhere in this file's output)
  - fill-hour histogram (UTC entry hour -> count) for the gated (anchor)
    entries — feeds lane-C conditional-bucket cost pricing.

Adjudication floors (counts only, reported not judged): >= 100 round trips
total and >= 6 months of entries.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))

import dev_plane2  # noqa: E402
import engine as t2_engine  # noqa: E402
import tracka_lib as T  # noqa: E402
from build_t2_planes import attach_m1agg  # noqa: E402
from qcrd_dinv_lib import (  # noqa: E402
    dinv_day_table, epoch_secs, session_day_ordinals, WARMUP_TRADED_DAYS,
)

DERIVED = LANE / "data_local" / "derived"
OUT = LANE / "falsifier" / "F6_census_counts.json"

ALLOWED_TRADE_KEYS = {"entry_ts", "exit_ts", "dir", "hold_bars", "exit_kind"}
BANNED_KEYS = {"pips", "entry_px", "exit_px", "equity", "net", "pf", "hit",
               "pnl", "profit", "maxdd", "maxdd_pips", "dd", "cum", "return"}
K = 1.0
LAST6M_FIRST_DAY = "2025-07-01"
LAST6M_LAST_DAY = "2025-12-31"


def _assert_clean(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if any(b in kl for b in ("pips", "pnl", "profit", "equity", "px",
                                     "drawdown")):
                raise AssertionError(f"PnL-class field in output: {path}.{k}")
            _assert_clean(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for j, v in enumerate(obj):
            _assert_clean(v, f"{path}[{j}]")
    return True


def _day_epoch_of(entry_ts: int) -> int:
    return int(entry_ts) // 86400


def census_one(anchor: str, sym: str, folds: dict,
               warmup_idx: int, k: float = K) -> dict:
    import pandas as pd  # local: keep module import light

    dev1h = dev_plane2.load_bars("bars1h_ANC", sym)
    if anchor == "P3A":
        df = attach_m1agg(dev1h, sym)
    else:
        df = dev1h
    tgt = np.load(DERIVED / f"t2_{anchor.lower()}_{sym}_anchor.npy")
    sha = hashlib.sha256(
        (DERIVED / f"t2_{anchor.lower()}_{sym}_anchor.npy").read_bytes()
    ).hexdigest()
    man = json.loads((DERIVED / "t2_planes_manifest.json").read_text())
    expect = man["pairs"][sym]["targets"][f"{anchor.lower()}_anchor"]["sha256"]
    if sha != expect:
        raise SystemExit(f"FAIL_CLOSED target sha mismatch {anchor}/{sym}")

    plane = T.SignalPlane(df, pip_mult=1e4)
    trades_raw, equity = t2_engine.run_strategy(
        plane, tgt, k, warmup_end_idx=warmup_idx)
    del equity  # NO PnL: engine equity curve discarded unwritten, unread
    trips = [{k2: t[k2] for k2 in ("entry_ts", "exit_ts", "dir", "hold_bars")}
             for t in trades_raw]
    del trades_raw
    for t in trips:
        assert set(t) <= ALLOWED_TRADE_KEYS

    ts = epoch_secs(df)
    hour = (ts // 3600) % 24
    day = ts // 86400
    _, dord, _ = session_day_ordinals(ts)

    if anchor == "P3A":
        decision_bars = (hour >= 0) & (hour <= 18) & (dord >= WARMUP_TRADED_DAYS)
    else:
        rows, _, _, _ = dinv_day_table(df)
        dec_idx = np.array(
            [r["i_close"] for r in rows
             if r["dec_capable"] and r["i_close"] >= 0
             and r["ord"] >= WARMUP_TRADED_DAYS], dtype=int)
        decision_bars = np.zeros(len(ts), dtype=bool)
        if len(dec_idx):
            decision_bars[dec_idx] = True

    occupied = tgt != 0
    windows = {fid: (int(v["first_day_epoch"]), int(v["last_day_epoch"]))
               for fid, v in folds.items()}
    import datetime as _dt
    d0 = int(_dt.datetime.strptime(LAST6M_FIRST_DAY, "%Y-%m-%d")
             .replace(tzinfo=_dt.timezone.utc).timestamp()) // 86400
    d1 = int(_dt.datetime.strptime(LAST6M_LAST_DAY, "%Y-%m-%d")
             .replace(tzinfo=_dt.timezone.utc).timestamp()) // 86400
    windows["last6m"] = (d0, d1)

    out_windows = {}
    for fid, (da, db) in windows.items():
        w = (day >= da) & (day <= db)
        etr = np.array([_day_epoch_of(t["entry_ts"]) for t in trips])
        in_w = (etr >= da) & (etr <= db) if len(etr) else np.zeros(0, bool)
        hist = {}
        for t, keep in zip(trips, in_w):
            if keep:
                h = (int(t["entry_ts"]) // 3600) % 24
                hist[str(h)] = hist.get(str(h), 0) + 1
        out_windows[fid] = {
            "window_days": [dt_date_str(da), dt_date_str(db)],
            "n_decision_bars": int((decision_bars & w).sum()),
            "n_occupied_bars": int((occupied & w).sum()),
            "n_round_trips": int(in_w.sum()),
            "fill_hour_hist_entries": dict(sorted(
                hist.items(), key=lambda kv: int(kv[0]))),
        }
    total = {
        "n_decision_bars": int(decision_bars.sum()),
        "n_occupied_bars": int(occupied.sum()),
        "n_round_trips": len(trips),
        "fill_hour_hist_entries": dict(sorted(
            ({h: sum(1 for t in trips if (int(t["entry_ts"]) // 3600) % 24 == int(h))
              for h in {str((int(t["entry_ts"]) // 3600) % 24) for t in trips}}
            ).items(), key=lambda kv: int(kv[0]))),
        "first_entry_day": dt_date_str(min((_day_epoch_of(t["entry_ts"])
                                            for t in trips), default=0)),
        "last_entry_day": dt_date_str(max((_day_epoch_of(t["entry_ts"])
                                           for t in trips), default=0)),
        "n_distinct_entry_days": len({_day_epoch_of(t["entry_ts"])
                                      for t in trips}),
    }
    total["floor_ge_100_rt"] = bool(total["n_round_trips"] >= 100)
    span_days = (max((_day_epoch_of(t["entry_ts"]) for t in trips), default=0)
                 - min((_day_epoch_of(t["entry_ts"]) for t in trips), default=0))
    total["entry_span_days"] = int(span_days)
    total["floor_ge_6_months"] = bool(span_days >= 180)
    return {
        "anchor": anchor, "pair": sym, "k": k,
        "warmup_index": warmup_idx,
        "engine": "scripts/engine.py run_strategy (schedule; equity/pips "
                  "discarded at source)",
        "target_sha256": sha,
        "windows": out_windows,
        "total": total,
    }


def dt_date_str(day_epoch: int) -> str:
    import datetime as _dt
    return _dt.datetime.fromtimestamp(int(day_epoch) * 86400,
                                      tz=_dt.timezone.utc).date().isoformat()


def main() -> int:
    man = json.loads((DERIVED / "t2_planes_manifest.json").read_text())
    books = [("P3A", "AUDUSD"), ("P3A", "USDCAD"),
             ("P3B", "USDCAD"), ("P3B", "AUDUSD")]
    out = {
        "schema": "tracka2.f6_census_counts@1",
        "counts_only_law": "no PnL field exists in this artifact; engine "
                           "pips/px/equity outputs stripped at source",
        "floors": {"n_round_trips_total": 100, "months": 6},
        "books": {},
    }
    for anchor, sym in books:
        folds = man["pairs"][sym]["fold_table"]
        warmup_idx = man["pairs"][sym]["warmup_index"]
        res = census_one(anchor, sym, folds, warmup_idx)
        out["books"][f"{anchor}/{sym}"] = res
        print(json.dumps({f"{anchor}/{sym}": {
            "total_rt": res["total"]["n_round_trips"],
            "floor_100": res["total"]["floor_ge_100_rt"],
            "floor_6m": res["total"]["floor_ge_6_months"],
            "per_fold_rt": {fid: w["n_round_trips"]
                            for fid, w in res["windows"].items()},
        }}, indent=1), flush=True)
    _assert_clean(out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({"out": str(OUT)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
