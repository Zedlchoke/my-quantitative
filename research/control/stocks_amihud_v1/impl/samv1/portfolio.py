"""STOCKS-AMIHUD-V1 portfolio simulation on the frozen contracts.

Clean state machine per fold:
  grid date t -> (1) exit holds entered at EARLIER grid dates per exit law
                (2) score/eligibility at t
                (3) bookable: enter at t+1 adj-open; unbookable: flatten
  fold end    -> force-flat leftovers at the fold's last session close.
Dry-run mode (`scored=False`): identical plumbing; the single price-ratio
computation that would produce PnL is never executed and never written.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import engine as E
from .panel import NameSeries

FORBIDDEN_OUTCOME_KEYS = {"pnl", "net_pnl", "gross_pnl", "pf", "profit_factor",
                          "sharpe", "drawdown", "mdd", "expectancy",
                          "break_even", "stress_pnl", "return_pct",
                          "hold_return", "gross", "net"}


def assert_no_outcome_fields(obj, path: str = "root") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and k.lower() in FORBIDDEN_OUTCOME_KEYS:
                raise E.FailLoud(f"dry-run leak: {path}.{k}")
            assert_no_outcome_fields(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_no_outcome_fields(v, f"{path}[{i}]")


@dataclass
class ExitRec:
    kind: str              # rebalance | unbookable_flat | fold | death
    decision_date: str
    fill_date: str
    fill_px: float         # adjusted basis
    band_bps: float


@dataclass
class HoldRec:
    code: str
    fold: str
    entry_decision: str
    entry_fill_date: str
    entry_px: float        # adjusted basis
    weight: float
    notional: float
    entry_cost: float
    exit: ExitRec | None = None
    exit_cost: float | None = None  # set only in scored mode


def _last_ok_index(ns: NameSeries, upto: str | None = None) -> int | None:
    best = None
    for i in range(len(ns.dates)):
        if not ns.adj_ok[i]:
            continue
        if upto is not None and ns.dates[i] > upto:
            break
        best = i
    return best


def _exit_at(ns: NameSeries, decision_date: str, fold_last: str,
             guards: E.Guards) -> ExitRec:
    """Exit law: next served bar AFTER the decision date, at its OPEN, if it
    exists in-fold (covers t+1 and multi-session halts alike); else the
    name never trades again in-fold -> death contract: final served close
    <= fold end; else FAIL LOUD."""
    di = ns.idx.get(decision_date)
    start = (di + 1) if di is not None else 0
    j = start
    while j < len(ns.dates) and ns.dates[j] <= decision_date:
        j += 1
    while j < len(ns.dates):
        if ns.adj_ok[j] and ns.dates[j] <= fold_last:
            band_src = E.dvmed60(ns, max(0, j - 1)) or E.DV_FLOOR
            return ExitRec("rebalance", decision_date, ns.dates[j],
                           ns.adj_open(j), E.band_bps(band_src))
        if ns.dates[j] > fold_last:
            break
        j += 1
    last_ok = _last_ok_index(ns, upto=fold_last)
    if last_ok is None:
        raise E.FailLoud(
            f"unexitable hold {ns.code} (no served bar <= {fold_last})")
    guards.death_exits += 1
    band_src = E.dvmed60(ns, max(0, last_ok - 1)) or E.DV_FLOOR
    return ExitRec("death", decision_date, ns.dates[last_ok], ns.adj[last_ok],
                   E.band_bps(band_src))


def simulate(panel: dict[str, NameSeries], sessions: list[str],
             axis: str, scored: bool) -> dict:
    guards = E.Guards()
    sess_idx = {s: i for i, s in enumerate(sessions)}
    grid_all = E.build_grid(sessions)
    holds: list[HoldRec] = []
    per_date: list[dict] = []

    for fold, (fa, fb) in E.FOLDS.items():
        fold_sessions = [s for s in sessions if fa <= s <= fb]
        fold_last = fold_sessions[-1]
        grid = [s for s in grid_all if fa <= s <= fb]
        open_holds: list[HoldRec] = []

        for t in grid:
            t_i = sess_idx[t]
            t1 = sessions[t_i + 1] if t_i + 1 < len(sessions) else None
            t1_in_fold = t1 is not None and fa <= t1 <= fb

            # (1) exit holds entered at earlier grid dates
            for h in open_holds:
                if h.exit is not None:
                    continue
                ns = panel[h.code]
                di = ns.idx.get(t)
                if di is not None and t1_in_fold:
                    h.exit = _exit_at(ns, t, fold_last, guards)
                    guards.rebalance_exits += 1
                elif di is not None and not t1_in_fold:
                    # last grid date of the fold with t+1 beyond fold: fold law
                    h.exit = _fold_exit(ns, fold_last, guards)
                else:
                    h.exit = _exit_at(ns, t, fold_last, guards)
                    guards.rebalance_exits += 1
            open_holds = [h for h in open_holds if h.exit is None]

            # (2) scores over eligible names at t (needs t and t+1 served)
            scores: dict[str, float] = {}
            dvmeds: dict[str, float] = {}
            for code in sorted(panel):
                ns = panel[code]
                bi = ns.idx.get(t)
                if bi is None:
                    continue
                if t1 is None or ns.idx.get(t1) is None:
                    guards.names_skipped_no_t1 += 1
                    continue
                m = E.dvmed60(ns, bi)
                if not E.eligible_at(ns, bi, ns.idx[t1], m, sessions):
                    continue
                sc = None
                if axis == "illiq21":
                    sc = E.illiq(ns, bi, 21, guards)
                elif axis == "illiq63":
                    sc = E.illiq(ns, bi, 63, guards)
                elif axis == "reversal5":
                    r5 = E.past_ret5(ns, bi, guards)
                    sc = -r5 if r5 is not None else None
                else:
                    raise E.FailLoud(f"unknown axis {axis}")
                if sc is not None:
                    scores[code] = sc
                    dvmeds[code] = m

            # (3) book or flatten
            book = E.rank_book(scores)
            bookable = len(scores) >= 46 and len(book) >= 10 and t1_in_fold
            if bookable:
                w = E.weights_for(book, dvmeds)
                for code in book:
                    ns = panel[code]
                    fi = ns.idx[t1]
                    band = E.band_bps(dvmeds[code])
                    cost = band * 1e-4 * (w[code] * E.AUM_REF)
                    h = HoldRec(code, fold, t, t1, ns.adj_open(fi), w[code],
                                w[code] * E.AUM_REF, cost)
                    holds.append(h)
                    open_holds.append(h)
                    guards.entries += 1
                per_date.append({"date": t, "fold": fold,
                                 "n_elig": len(scores), "n_book": len(book),
                                 "bookable": True})
            else:
                if open_holds:
                    for h in open_holds:
                        ns = panel[h.code]
                        h.exit = _exit_at(ns, t, fold_last, guards)
                    open_holds = []
                guards.unbookable_dates += 1
                per_date.append({"date": t, "fold": fold,
                                 "n_elig": len(scores), "n_book": 0,
                                 "bookable": False})

        # fold force-flat
        for h in open_holds:
            h.exit = _fold_exit(panel[h.code], fold_last, guards)
        open_holds = []

    if scored:
        for h in holds:
            h.exit_cost = h.exit.band_bps * 1e-4 * h.notional
    return {"holds": holds, "per_date": per_date, "guards": guards}


def _fold_exit(ns: NameSeries, fold_last: str, guards: E.Guards) -> ExitRec:
    bi = ns.idx.get(fold_last)
    if bi is not None and ns.adj_ok[bi]:
        guards.fold_exits += 1
        return ExitRec("fold", fold_last, fold_last, ns.adj[bi],
                       E.band_bps(E.dvmed60(ns, bi) or E.DV_FLOOR))
    back = _last_ok_index(ns, upto=fold_last)
    if back is None:
        raise E.FailLoud(f"unexitable fold hold {ns.code}")
    kind = "death" if ns.dates[back] < fold_last else "fold"
    if kind == "death":
        guards.death_exits += 1
    else:
        guards.fold_exits += 1
    return ExitRec(kind, fold_last, ns.dates[back], ns.adj[back],
                   E.band_bps(E.dvmed60(ns, max(0, back - 1)) or E.DV_FLOOR))
