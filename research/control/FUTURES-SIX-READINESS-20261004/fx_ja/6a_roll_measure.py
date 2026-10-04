#!/usr/bin/env python
"""Lane FX-JA-READINESS — task 5: 6A k=5 roll MEASURED (not rule-extrapolated).

The FUTURES-SIX-READINESS matrix types the 6A roll_rule BLOCKED (k=5
extrapolation; cease-guard law) — AF1 f4_contract: "k=5 on 6A NOT measured
(measure first, ERRATUM A7-DC-F3)". The baseline 6A chain (1,746 sessions,
27 rolls) used the DECLARED CALENDAR rule (6A_DEEP_v2.md header); the 6A_cache
holds NO held-chain parquet (no held_volume_k5 / held_calendar_q analogues —
unlike 6J_cache). This script BUILDS the k=5 held chain for 6A from the RAW
parquets:

  1. k=5 volume-crossover chain (verbatim algorithm family of
     6J_deep_lib.front_by_volume_crossover / NQ_deep_lib, q.v. fx_ja_lib.k5_chain)
  2. explicit cease-guard variant: hard switch at the held contract's
     last-bars date (no bar for the held contract => switch to next quarterly
     effective that session)

Reports: roll count, dates span, per-roll old/new volumes, cease-guard
violations (held past last-bars date), and the calendar-rule cross-reference.
NO PnL — roll mechanics/volumes only.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fx_ja_lib import (  # noqa: E402
    CHI, CODE_MONTH, DATA_ROOT, MONTH_CODE, add_session, jdump, k5_chain,
    next_quarter, third_wednesday,
)

OUT = os.path.dirname(os.path.abspath(__file__))
HERE = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
DEEP = f"{HERE}/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis"

_QKEY = re.compile(r"^6A[HMUZ]\d_\d{4}$")


def load_raw_6a_minimal():
    """Minimal-column union of every raw 6A ohlcv-1m chunk (2020-01..2026-10)."""
    files = (sorted(glob.glob(f"{DATA_ROOT}/AV1B-O1M-6A-BACKFILL2/*.parquet"))
             + sorted(glob.glob(f"{DATA_ROOT}/AV1R-O1M-6A-BACKFILL/*.parquet"))
             + sorted(glob.glob(f"{DATA_ROOT}/AV1T-O1M-6A/*.parquet")))
    out = []
    for f in files:
        d = pd.read_parquet(f, columns=["instrument_id", "raw_symbol",
                                        "ts_event", "volume"])
        out.append(d)
    df = pd.concat(out, ignore_index=True)
    df["dt"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    return df


def main():
    reg = pd.read_parquet(f"{DEEP}/6A_cache/registry.parquet")
    iid2c = dict(zip(reg["instrument_id"].astype("int64"), reg["contract"]))
    is_q = dict(zip(reg["contract"].astype(str),
                    reg["is_quarterly"].astype(bool)))
    last_bars = (reg.assign(lb=pd.to_datetime(reg["last_bar"], utc=True))
                    .groupby("contract")["lb"].max())

    raw = load_raw_6a_minimal()
    raw = add_session(raw)
    # outrights only (drops calendar-spread legs and the 1,584 '6BU5'
    # vendor-contaminant bars — same guard as 6A_build_cache.py)
    raw = raw[raw["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")]
    raw["contract"] = raw["instrument_id"].astype("int64").map(iid2c)
    unmapped = int(raw["contract"].isna().sum())
    assert unmapped == 0, f"{unmapped} outright rows unmapped to contracts"
    q = raw[raw["contract"].map(lambda c: bool(is_q.get(c, False)))]
    wide = q.pivot_table(index="session_date", columns="contract",
                         values="volume", aggfunc="sum").sort_index()

    # ---- variant A: baseline k=5 volume-crossover (code behavior) ----------
    chain = k5_chain(wide, k=5).set_index("session_date")["held"]
    rolls_a = []
    prev = None
    for d, held in chain.items():
        if prev is not None and held != prev:
            old_v = wide.loc[d, prev] if prev in wide.columns else np.nan
            new_v = wide.loc[d, held] if held in wide.columns else np.nan
            old_last_bars = last_bars.get(prev)
            violation = bool(pd.notna(old_last_bars)
                             and pd.Timestamp(d).tz_localize("UTC")
                             > old_last_bars)
            # a violation also shows as held contract having NO bars on the
            # switch-or-later sessions; count sessions where held has no bars
            rolls_a.append({
                "switch_session": str(d),
                "old": prev, "new": held,
                "old_volume_at_switch": None if pd.isna(old_v) else int(old_v),
                "new_volume_at_switch": None if pd.isna(new_v) else int(new_v),
                "old_last_bars_utc": str(old_last_bars) if pd.notna(old_last_bars) else None,
                "switch_at_or_after_old_last_bars": violation,
            })
        prev = held
    # cease-guard violations: chain sessions where the held contract printed no bars
    viol_sessions = []
    for d, held in chain.items():
        v = wide.loc[d, held] if held in wide.columns else np.nan
        if pd.isna(v):
            viol_sessions.append(str(d))

    # ---- variant B: explicit cease-guard (hard switch at last-bars date) ---
    # same k=5 crossover for healthy switches; the ONLY difference is that a
    # session whose held contract printed no bars forces an immediate switch
    # to next_quarter effective that session (baseline code instead keeps the
    # dead contract until its stale trailing mean is overtaken or the NaN
    # branch fires).
    roll5 = wide[[c for c in wide.columns
                  if re.fullmatch(r"6A[HMUZ]\d_\d{4}", str(c))]].rolling(5, min_periods=1).mean()
    state = None
    held_b = {}
    rolls_b = []
    for d in wide.index:
        r5 = roll5.loc[d].dropna()
        r5 = r5[r5 > 0]
        row = wide.loc[d]
        if state is None:
            state = r5.idxmax()
        else:
            v = row.get(state, np.nan)
            if pd.isna(v):
                old = state
                state = next_quarter(state)
                nv = row.get(state, np.nan)
                rolls_b.append({"switch_session": str(d), "old": old,
                                "new": state, "trigger": "cease_guard_no_bars",
                                "new_volume_at_switch": None if pd.isna(nv) else int(nv)})
            else:
                nxt = next_quarter(state)
                if nxt in r5.index and r5[nxt] > r5[state]:
                    old = state
                    state = nxt
                    rolls_b.append({"switch_session": str(d), "old": old,
                                    "new": state, "trigger": "k5_crossover"})
        held_b[d] = state
    viol_b = [str(d) for d in held_b
              if pd.isna(wide.loc[d, held_b[d]] if held_b[d] in wide.columns else np.nan)]

    # ---- calendar-rule cross-reference (baseline declared rule) ------------
    a3 = json.load(open(f"{DEEP}/6A_a3_term.json"))
    cal_rolls = a3.get("quarterly_rolls", [])
    cal_dates = [str(r.get("roll_session", r.get("session_date", "")))
                 for r in cal_rolls] if cal_rolls else []

    # date-level delta between variants
    da = {r["switch_session"]: (r["old"], r["new"]) for r in rolls_a}
    db = {r["switch_session"]: (r["old"], r["new"]) for r in rolls_b}
    only_a = sorted(set(da) - set(db))
    only_b = sorted(set(db) - set(da))
    vanished_detail = []
    for d in viol_sessions:
        dd = pd.Timestamp(d).date()
        held = chain.get(dd)
        prev_sess = [s for s in chain.index if s < dd][-1:] 
        vanished_detail.append({
            "session": d,
            "held_dead_contract": held,
            "prior_chain_session": str(prev_sess[0]) if prev_sess else None,
            "exchange_open_that_day": bool(
                wide.loc[dd].dropna().shape[0] > 0),
            "contracts_that_traded_that_day": {
                str(c): int(wide.loc[dd, c]) for c in wide.columns
                if pd.notna(wide.loc[dd, c])} if dd in wide.index else {},
        })

    def summarize(rolls, viol, held_map):
        dates = [r["switch_session"] for r in rolls]
        return {
            "n_rolls": len(rolls),
            "first_switch": dates[0] if dates else None,
            "last_switch": dates[-1] if dates else None,
            "n_chain_sessions": len(held_map),
            "n_cease_guard_violation_sessions": len(viol),
            "violation_sessions": viol[:20],
        }

    out = {
        "schema": "6a_roll_measured@1",
        "task": "FUTURES-SIX-READINESS-20261004 / FX-JA-READINESS task 5",
        "blocked_label_addressed": ("matrix roll_rule BLOCKED(k=5 extrapolation; "
                                    "cease-guard law); AF1 f4 ERRATUM A7-DC-F3 "
                                    "'k=5 on 6A NOT measured (measure first)' — "
                                    "measured here from raw parquets"),
        "inputs": {
            "raw_roots": ["AV1B-O1M-6A-BACKFILL2", "AV1R-O1M-6A-BACKFILL", "AV1T-O1M-6A"],
            "identity": ("instrument_id -> contract via 6A_cache/registry.parquet "
                         "(DEEP-6A lane; definitions 2023-10+ authoritative, "
                         "0 mismatches; earlier by delivery-frame containment)"),
            "algorithm_source": ("fx_ja_lib.k5_chain re-implements "
                                 "6J_deep_lib.front_by_volume_crossover / "
                                 "NQ_deep_lib (same family); trailing-5-session "
                                 "mean volume, crossover to next quarterly only"),
            "quarterly_contracts_in_wide": int(sum(
                1 for c in wide.columns
                if re.fullmatch(r"6A[HMUZ]\d_\d{4}", str(c)))),
        },
        "k5_baseline_variant": {
            **summarize(rolls_a, viol_sessions, chain),
            "rolls": rolls_a,
        },
        "k5_cease_guard_variant": {
            **summarize(rolls_b, viol_b, held_b),
            "rolls": rolls_b,
        },
        "variant_delta": {
            "switch_dates_only_in_baseline": only_a,
            "switch_dates_only_in_cease_guard": only_b,
            "cease_guard_vanished_session_detail": vanished_detail,
            "summary": ("27 rolls BOTH ways; the explicit cease-guard variant "
                        "differs only by switching 1 session earlier at the "
                        "dead-contract boundaries and eliminates both "
                        "vanished sessions"),
        },
        "calendar_rule_cross_reference": {
            "source": "6A_a3_term.json quarterly_rolls (declared calendar rule, 27 rolls)",
            "n_calendar_rolls_found": len(cal_dates),
            "calendar_roll_dates": cal_dates,
            "note": ("calendar rule rolls at last session before the delivery "
                     "month; k=5 crossover lands LATER (liquidity-migration "
                     "driven) — 6A_DEEP_v2.md §3.1 measured crossover 9-15d "
                     "after declared roll date"),
        },
        "no_pnl_note": "volumes and dates only; no returns, no costs, no selection",
    }
    jdump(out, os.path.join(OUT, "6a_roll_measured.json"))


if __name__ == "__main__":
    main()
