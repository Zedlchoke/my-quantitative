"""A9-F schedule feasibility: decision clocks, folds, warmup on the real snapshot."""

from __future__ import annotations

import json
from datetime import date

from a9f_lib import (
    FOLDS, SECTORS, S0_START, S0_END,
    load_spy_calendar, load_close, s0_sessions, fold_sessions,
    quarterly_clock, global_clock, session_at,
)

def main():
    out = {}
    cal = load_spy_calendar()
    out["calendar"] = {
        "source": "SPY_none_p1.json",
        "n_sessions_total": len(cal),
        "first": str(cal[0]),
        "last": str(cal[-1]),
    }
    s0 = s0_sessions(cal)
    out["s0"] = {"declared": "2018-04-04..2025-07-31", "n_sessions": len(s0),
                 "first": str(s0[0]), "last": str(s0[-1])}

    folds = fold_sessions(s0)
    fold_info = {}
    fold_set_map = {}
    for fid, sessions in folds.items():
        fold_info[fid] = {
            "n_sessions": len(sessions),
            "first": str(sessions[0]),
            "last": str(sessions[-1]),
            "meets_568_for_10x63": len(sessions) >= 568,
        }
        fold_set_map[fid] = set(sessions)
    out["folds"] = fold_info
    union = set().union(*fold_set_map.values())
    gap_sessions = [d for d in s0 if d not in union]
    out["fold_gaps"] = {"n_gap_sessions_in_s0": len(gap_sessions),
                        "sessions": [str(d) for d in gap_sessions]}

    # ETF leg-eligibility history (>=63 and >=252 and >=21 sessions rules)
    hist = {}
    for sym in ["SPY"] + list(SECTORS):
        px = load_close(sym)
        dts = sorted(px)
        hist[sym] = {"first": str(dts[0]), "last": str(dts[-1]),
                     "n_pre_s0": sum(1 for d in dts if d < S0_START)}
    out["etf_history"] = hist

    def n_sessions_before(sym, d):
        px = hist_dates[sym]
        return sum(1 for x in px if x < d)

    hist_dates = {sym: sorted(load_close(sym)) for sym in ["SPY"] + list(SECTORS)}

    # XLC first-eligibility dates under the three declared rules
    xlc = hist_dates["XLC"]
    out["xlc_eligibility"] = {
        "21_sessions": str(xlc[21]),
        "63_sessions": str(xlc[63]),
        "252_sessions": str(xlc[252]),
    }
    xlre = hist_dates["XLRE"]
    out["xlre_252_eligible_from"] = str(xlre[252])

    # quarterly 63-session clock (a4_h1, a4_h2, a5_h1, a5_h2): 10 ticks/fold
    qclock = quarterly_clock(folds, step=63, max_offset=567)
    qdetail = {}
    all_ticks = []
    for fid, ticks in qclock.items():
        qdetail[fid] = {"n_ticks": len(ticks), "ticks": [str(t) for t in ticks],
                        "offsets": [fold_sessions_idx for fold_sessions_idx in
                                    [folds[fid].index(t) for t in ticks]]}
        for t in ticks:
            all_ticks.append((fid, t))
    out["quarterly_clock_63"] = {
        "per_fold": qdetail,
        "total_ticks": len(all_ticks),
        "every_tick_inside_exactly_one_fold": all(
            sum(t in fs for fs in fold_set_map.values()) == 1 for _, t in all_ticks
        ),
    }

    # a5_h2 stale control needs sigma ranks at t-63 (calendar arithmetic)
    q_all = [t for _, t in all_ticks]
    out["quarterly_clock_63_stale_refs_exist"] = all(
        cal.index(t) >= 63 for t in q_all
    )

    # a4_h1 reference sessions t-252s
    ref252 = {str(t): str(session_at(cal, t, 252)) for _, t in all_ticks}
    out["quarterly_clock_63_t_minus_252_refs"] = ref252
    out["quarterly_clock_63_t_minus_252_all_pre_or_in_s0"] = all(
        S0_START <= session_at(cal, t, 252) <= S0_END or session_at(cal, t, 252) < S0_START
        for _, t in all_ticks
    )

    # a6 global 42-session clock
    g42 = global_clock(s0, step=42)
    g_assign = {}
    unassigned = []
    per_fold = {fid: 0 for fid in folds}
    for t in g42:
        owner = [fid for fid, fs in fold_set_map.items() if t in fs]
        if len(owner) == 1:
            per_fold[owner[0]] += 1
            g_assign[str(t)] = owner[0]
        else:
            unassigned.append(str(t))
    out["global_clock_42"] = {
        "n_slots": len(g42),
        "slots": [str(t) for t in g42],
        "per_fold_scored": per_fold,
        "slots_outside_all_folds": unassigned,
        "all_slots_inside_exactly_one_fold": len(unassigned) == 0,
        "meets_30_total": len(g42) - len(unassigned) >= 30,
        "meets_5_per_fold": all(v >= 5 for v in per_fold.values()),
    }

    # benchmark coverage
    spy_all = sorted(load_close("SPY", "_all_p1"))
    out["benchmark_spy_all"] = {
        "first": str(spy_all[0]), "last": str(spy_all[-1]),
        "covers_all_quarterly_ticks": all(spy_all[0] <= t <= spy_all[-1] for t in q_all),
        "covers_all_42grid_slots": all(spy_all[0] <= t <= spy_all[-1] for t in g42),
        "covers_pre_s0_252_runway_start": str(session_at(cal, s0[0], 252)),
    }

    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
