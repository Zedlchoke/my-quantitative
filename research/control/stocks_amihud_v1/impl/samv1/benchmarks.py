"""STOCKS-AMIHUD-V1 benchmarks (evaluation context, NOT scored cells).

1. SPY exposure-matched twin: SPY bought/sold on the SAME grid dates and
   fill conventions as the anchor book (t+1 adj-open entries/exits, fold
   force-flat at fold-last close), band-A costs (SPY >= $50M DV).
2. Random-timing twin: PCG64 seed 20260923, 200 random calendars (per fold:
   random start offset 0..20 then step 21), SPY round trips, distribution
   reported. Same cost kernel.
3. Matched-characteristic book: for each anchor member at each grid date,
   the nearest eligible NON-member by |log DVmed60| within the same
   realized-vol tercile and price tier; fallback: same vol tercile only;
   else CASH. EW 1/N_book, same AUM_ref, same kernel, same exits law.
All constructions frozen in impl_contract.json BEFORE any PnL.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import engine as E
from .panel import NameSeries
from .portfolio import HoldRec, _exit_at, _fold_exit

RNG_SEED = 20260923
N_RANDOM_CALENDARS = 200


def spy_twin(spy: NameSeries, sessions: list[str], scored: bool) -> dict:
    """SPY traded on the anchor grid — full-cycle single-position book."""
    guards = E.Guards()
    sess_idx = {s: i for i, s in enumerate(sessions)}
    grid_all = E.build_grid(sessions)
    holds: list[HoldRec] = []
    for fold, (fa, fb) in E.FOLDS.items():
        fold_sessions = [s for s in sessions if fa <= s <= fb]
        fold_last = fold_sessions[-1]
        grid = [s for s in grid_all if fa <= s <= fb]
        open_h: list[HoldRec] = []
        for t in grid:
            for h in open_h:
                if h.exit is None:
                    h.exit = _exit_at(spy, t, fold_last, guards)
            open_h = [h for h in open_h if h.exit is None]
            t_i = sess_idx[t]
            t1 = sessions[t_i + 1] if t_i + 1 < len(sessions) else None
            if t1 is None or not (fa <= t1 <= fb):
                continue
            if spy.idx.get(t) is None or spy.idx.get(t1) is None:
                continue
            m = E.dvmed60(spy, spy.idx[t])
            fi = spy.idx[t1]
            band = E.band_bps(m or E.DV_FLOOR)
            cost = band * 1e-4 * E.AUM_REF
            h = HoldRec("SPY", fold, t, t1, spy.adj_open(fi), 1.0,
                        E.AUM_REF, cost)
            holds.append(h)
            open_h.append(h)
            guards.entries += 1
        for h in open_h:
            h.exit = _fold_exit(spy, fold_last, guards)
    if scored:
        for h in holds:
            h.exit_cost = h.exit.band_bps * 1e-4 * h.notional
    return {"holds": holds, "guards": guards}


def random_timing_twins(spy: NameSeries, sessions: list[str]) -> list[dict]:
    """200 random calendars; per fold: offset = rng.integers(0,21), step 21.
    Schedules only in dry-run contexts; caller aggregates in scored mode."""
    import numpy as np
    rng = np.random.Generator(np.random.PCG64(RNG_SEED))
    sess_idx = {s: i for i, s in enumerate(sessions)}
    calendars = []
    for k in range(N_RANDOM_CALENDARS):
        holds: list[HoldRec] = []
        guards = E.Guards()
        for fold, (fa, fb) in E.FOLDS.items():
            fold_sessions = [s for s in sessions if fa <= s <= fb]
            if not fold_sessions:
                continue
            fold_last = fold_sessions[-1]
            start = sess_idx[fold_sessions[0]] + int(rng.integers(0, 21))
            grid = sessions[start::E.GRID_STEP]
            grid = [s for s in grid if fa <= s <= fb]
            open_h: list[HoldRec] = []
            for t in grid:
                for h in open_h:
                    if h.exit is None:
                        h.exit = _exit_at(spy, t, fold_last, guards)
                open_h = [h for h in open_h if h.exit is None]
                t_i = sess_idx[t]
                t1 = sessions[t_i + 1] if t_i + 1 < len(sessions) else None
                if t1 is None or not (fa <= t1 <= fb):
                    continue
                if spy.idx.get(t) is None or spy.idx.get(t1) is None:
                    continue
                fi = spy.idx[t1]
                m = E.dvmed60(spy, spy.idx[t])
                band = E.band_bps(m or E.DV_FLOOR)
                h = HoldRec("SPY", fold, t, t1, spy.adj_open(fi), 1.0,
                            E.AUM_REF, band * 1e-4 * E.AUM_REF)
                holds.append(h)
                open_h.append(h)
                guards.entries += 1
            for h in open_h:
                h.exit = _fold_exit(spy, fold_last, guards)
        calendars.append({"calendar_index": k, "holds": holds, "guards": guards})
    return calendars


def _vol60(ns: NameSeries, t_i: int) -> float | None:
    lo = max(0, t_i - 60, 1)
    rets = []
    for i in range(lo, t_i + 1):
        if ns.adj_ok[i] and ns.adj_ok[i - 1] and ns.adj[i - 1] > 0:
            rets.append(ns.adj[i] / ns.adj[i - 1] - 1.0)
    if len(rets) < 30:
        return None
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / (len(rets) - 1)  # class iv: len>=30
    return math.sqrt(var)


def _price_tier(p: float) -> int:
    for i, lo in enumerate((1.0, 5.0, 20.0, 100.0)):
        if p < (1.0, 5.0, 20.0, 100.0, float("inf"))[i + 1]:
            return i
    return 3


def matched_book(anchor_per_date: list[dict], panel: dict[str, NameSeries],
                 sessions: list[str], scored: bool) -> dict:
    """EW book of nearest-characteristic non-members on the anchor's dates."""
    sess_idx = {s: i for i, s in enumerate(sessions)}
    guards = E.Guards()
    holds: list[HoldRec] = []
    per_date_info = [d for d in anchor_per_date if d["bookable"]]
    # eligibility cache at each anchor decision date
    for fold, (fa, fb) in E.FOLDS.items():
        fold_sessions = [s for s in sessions if fa <= s <= fb]
        fold_last = fold_sessions[-1]
        dates = [d for d in per_date_info if d["fold"] == fold]
        open_h: list[HoldRec] = []
        for drec in dates:
            t = drec["date"]
            t_i = sess_idx[t]
            t1 = sessions[t_i + 1] if t_i + 1 < len(sessions) else None
            for h in open_h:
                if h.exit is None:
                    h.exit = _exit_at(panel[h.code], t, fold_last, guards)
            open_h = [h for h in open_h if h.exit is None]
            if t1 is None or not (fa <= t1 <= fb):
                continue
            # eligibility + characteristics at t
            cands: list[dict] = []
            for code in sorted(panel):
                ns = panel[code]
                bi = ns.idx.get(t)
                if bi is None or t1 is None or ns.idx.get(t1) is None:
                    continue
                m = E.dvmed60(ns, bi)
                if not E.eligible_at(ns, bi, ns.idx[t1], m, sessions):
                    continue
                v = _vol60(ns, bi)
                if v is None:
                    continue
                cands.append({"code": code, "dv": m, "vol": v,
                              "tier": _price_tier(ns.adj[bi])})
            anchor_members = set(drec.get("book_codes", []))
            if not anchor_members:
                continue
            anchor_chars = [c for c in cands if c["code"] in anchor_members]
            if not anchor_chars:
                continue
            vols = sorted(c["vol"] for c in cands)
            def tercile(v: float) -> int:
                k = len(vols)
                return min(2, int(3 * sum(1 for x in vols if x <= v) / k))
            non_members = [c for c in cands if c["code"] not in anchor_members]
            picks: list[str] = []
            for a in anchor_chars:
                pool = [c for c in non_members
                        if c["code"] not in picks
                        and tercile(c["vol"]) == tercile(a["vol"])
                        and c["tier"] == a["tier"]]
                if not pool:
                    pool = [c for c in non_members
                            if c["code"] not in picks
                            and tercile(c["vol"]) == tercile(a["vol"])]
                if not pool:
                    continue
                best = min(pool, key=lambda c: (abs(math.log(c["dv"] / a["dv"])), c["code"]))
                picks.append(best["code"])
            if len(picks) < 10:      # same bookability floor as anchor
                continue
            n = len(picks)
            total_w = 0.0
            entries_here = []
            for code in picks:
                ns = panel[code]
                m = next(c["dv"] for c in cands if c["code"] == code)
                w = min(1.0 / n, E.CAP_FRAC * m / E.AUM_REF)
                fi = ns.idx[t1]
                band = E.band_bps(m)
                cost = band * 1e-4 * (w * E.AUM_REF)
                h = HoldRec(code, fold, t, t1, ns.adj_open(fi), w,
                            w * E.AUM_REF, cost)
                holds.append(h)
                open_h.append(h)
                total_w += w
                guards.entries += 1
        for h in open_h:
            h.exit = _fold_exit(panel[h.code], fold_last, guards)
    if scored:
        for h in holds:
            h.exit_cost = h.exit.band_bps * 1e-4 * h.notional
    return {"holds": holds, "guards": guards}
