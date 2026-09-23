"""STOCKS-AMIHUD-V1 P0 F4 census: cohort/coverage/death/warmup/eligibility.

Reads the v2 CSV staging + census; produces f4_cohort_census.json. Census
ONLY — no PnL, PF, Sharpe, drawdown, survivor, or any candidate outcome.
Guard law applies here too: every division guarded (adjusted_close>0 etc.).
"""
from __future__ import annotations

import csv
import io
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGING = HERE / "staging_eod_csv"
OUT = HERE / "f4_cohort_census.json"

FOLDS = {"F1_2019": ("2019-01-01", "2019-12-31"),
         "F2_2020": ("2020-01-01", "2020-12-31"),
         "F3_2021_22": ("2021-01-01", "2022-12-31")}
WINDOW = ("2017-07-01", "2022-12-31")
GRID_START = "2019-01-02"
GRID_STEP = 21
PRICE_FLOOR = 1.00
DV_FLOOR = 2_000_000.0
DV_WINDOW = 60


def load_name(code: str) -> list[dict]:
    p = STAGING / f"{code}.csv"
    if not p.exists():
        return []
    rows = []
    with p.open(newline="") as f:
        for rec in csv.DictReader(f):
            try:
                rows.append({
                    "date": rec["Date"],
                    "close": float(rec["Close"]),
                    "adj": float(rec["Adjusted_close"]),
                    "vol": float(rec["Volume"]),
                })
            except (ValueError, KeyError, TypeError):
                continue
    rows.sort(key=lambda r: r["date"])
    return rows


def main() -> None:
    uni = json.loads((HERE / "universe_frozen.json").read_text())
    codes = sorted(uni["codes"].keys()) + ["SPY", "AAPL", "TSLA"]
    spy = load_name("SPY")
    sessions = [r["date"] for r in spy if WINDOW[0] <= r["date"] <= WINDOW[1]]
    out = {"schema": "f4_cohort_census/stocks_amihud_v1@1",
           "measured_utc": datetime.now(timezone.utc).isoformat(),
           "ny_sessions_from_spy": len(sessions),
           "session_first_last": (sessions[0], sessions[-1]) if sessions else None,
           "dv_pair": "adjusted_close x volume (F3a frozen verdict)",
           "guard_counters": {"adj_nonpositive": 0, "adj_nonfinite": 0,
                              "dv_zero_or_nonpositive": 0, "ohlc_violations": 0,
                              "duplicate_dates": 0, "rows_total": 0},
           "names": {}}
    names = out["names"]
    in_window = 0
    for code in codes:
        rows = load_name(code)
        if not rows:
            names[code] = {"in_window": False, "reason": "no_served_rows"}
            continue
        seen = set()
        dups = 0
        bad_adj = bad_dv = ohlc_bad = 0
        sidx = {d: i for i, d in enumerate(sessions)}
        served = []
        for r in rows:
            if r["date"] in seen:
                dups += 1
                continue
            seen.add(r["date"])
            if not math.isfinite(r["adj"]) or r["adj"] <= 0:
                bad_adj += 1
                continue  # excluded name-day (guard class i), counted
            dv = r["adj"] * r["vol"]  # frozen pair; vol>=0 always
            if not math.isfinite(dv) or dv <= 0:
                bad_dv += 1  # excluded from formation means later (class ii)
            served.append(r)
        out["guard_counters"]["adj_nonpositive"] += bad_adj
        out["guard_counters"]["duplicate_dates"] += dups
        out["guard_counters"]["rows_total"] += len(rows)
        if not served:
            names[code] = {"in_window": False, "reason": "all_rows_guard_excluded",
                           "bad_adj": bad_adj}
            continue
        first, last = served[0]["date"], served[-1]["date"]
        iw = first <= WINDOW[1] and last >= GRID_START
        # gaps: stretches of missing NY sessions inside [first, last]
        gaps = 0
        idxs = [sidx[d] for d in (r["date"] for r in served) if d in sidx]
        if len(idxs) > 1:
            for a, b in zip(idxs, idxs[1:]):
                if b - a > 1:
                    gaps += (b - a - 1)
        # served sessions before grid start (warmup)
        pre = sum(1 for r in served if r["date"] < GRID_START and r["date"] in sidx)
        # in-horizon deaths per fold (BC-7a): last served bar strictly inside fold
        death_fold = None
        for fname, (a, b) in FOLDS.items():
            if a <= last <= b:
                death_fold = fname
                break
        if iw:
            in_window += 1
        names[code] = {
            "in_window": iw, "first": first, "last": last,
            "served_rows": len(served), "gap_sessions": gaps,
            "warmup_pre_grid_sessions": pre,
            "warmup_ok_252": pre >= 252,
            "death_fold_in_horizon": death_fold,
            "bad_adj_rows": bad_adj, "bad_dv_rows": bad_dv,
        }

    # decision grid + eligibility census (per bookable date)
    grid = [d for d in sessions if d >= GRID_START][::GRID_STEP]
    elig_per_date = {}
    dvmed_cache: dict[str, dict[str, float]] = {}
    for code, meta in names.items():
        if not meta.get("in_window") or not meta.get("warmup_ok_252"):
            continue
        rows = load_name(code)
        meds = {}
        by_date = {r["date"]: r for r in rows}
        for i, d in enumerate(sessions):
            if d not in by_date:
                continue
            window = [by_date[x]["adj"] * by_date[x]["vol"]
                      for x in sessions[max(0, i - DV_WINDOW + 1):i + 1]
                      if x in by_date and by_date[x]["adj"] > 0
                      and (by_date[x]["adj"] * by_date[x]["vol"]) > 0]
            if len(window) >= DV_WINDOW // 2:
                meds[d] = statistics.median(window)
        dvmed_cache[code] = meds
    for d in grid:
        n_elig = 0
        for code, meds in dvmed_cache.items():
            m = meds.get(d)
            if m is None:
                continue
            meta = names[code]
            rows_first_last = meta["first"] <= d <= meta["last"]
            if rows_first_last and m >= DV_FLOOR:
                n_elig += 1
        elig_per_date[d] = n_elig
    bookable = {f: sum(1 for d, n in elig_per_date.items()
                       if a <= d <= b and n >= 46)
                for f, (a, b) in FOLDS.items()}
    out["decision_grid"] = {"dates": grid, "n_dates": len(grid),
                            "step_sessions": GRID_STEP}
    out["eligibility_census"] = {
        "floors": {"adjclose_ge": PRICE_FLOOR, "dvmed60_ge": DV_FLOOR},
        "eligible_names_per_date": elig_per_date,
        "bookable_dates_per_fold_ge46eligible": bookable,
        "fold_floor_6_dates": {k: (v >= 6, v) for k, v in bookable.items()},
    }
    out["population_summary"] = {
        "universe_codes": len(codes), "in_window": in_window,
        "warmup_ok": sum(1 for m in names.values() if m.get("warmup_ok_252")),
        "deaths_per_fold": {f: sum(1 for m in names.values()
                                   if m.get("death_fold_in_horizon") == f)
                            for f in FOLDS},
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({"ny_sessions": out["ny_sessions_from_spy"],
                      "population": out["population_summary"],
                      "bookable_dates_per_fold": bookable,
                      "guard_counters": out["guard_counters"],
                      "grid_dates": len(grid)}, indent=1))


if __name__ == "__main__":
    main()
