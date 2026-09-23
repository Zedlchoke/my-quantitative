"""STOCKS-AMIHUD-V1 golden tests (plan §8) — synthetic fixtures only, no
production outcomes, no real staging data."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))

from samv1 import engine as E                      # noqa: E402
from samv1.panel import NameSeries, GuardCounters  # noqa: E402
from samv1.portfolio import (simulate, assert_no_outcome_fields,  # noqa: E402
                             _exit_at, _fold_exit)
from samv1 import evaluate as EV                   # noqa: E402


def weekdays(start: str, end: str) -> list[str]:
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    out = []
    while d0 <= d1:
        if d0.weekday() < 5:
            out.append(d0.isoformat())
        d0 += dt.timedelta(days=1)
    return out


SESSIONS = weekdays("2018-01-01", "2022-12-30")
SESS_IDX = {s: i for i, s in enumerate(SESSIONS)}


def synth(code: str, n: int, adj0: float = 50.0, vol: float = 1e6,
          ret: float = 0.0005, sessions: list[str] = SESSIONS,
          end_date: str | None = None, adj_override: dict[str, float] | None = None,
          vol_override: dict[str, float] | None = None) -> NameSeries:
    ns = NameSeries(code)
    adj = adj0
    for i, d in enumerate(sessions):
        if i >= n and end_date is None:
            break
        if end_date is not None and d > end_date:
            break
        prev = adj
        adj = adj * (1.0 + ret)
        a = adj_override.get(d, adj) if adj_override else adj
        v = vol_override.get(d, vol) if vol_override else vol
        broken = not (a > 0.0 and a == a)  # NaN or <=0
        dv = (a * v) if (not broken and a * v > 0.0) else 0.0
        ns.dates.append(d); ns.idx[d] = len(ns.dates) - 1
        ns.open_raw.append(a * 1.0); ns.close_raw.append(a)
        ns.adj.append(a if not broken else float("nan"))
        ns.vol.append(v); ns.dv.append(dv); ns.adj_ok.append(not broken)
    return ns


def eligible_panel(count: int, **kw) -> dict[str, NameSeries]:
    return {f"N{i:03d}": synth(f"N{i:03d}", 10**9, ret=0.0001 * (i + 1), **kw)
            for i in range(count)}


# --- T1 no-lookahead: formation/eligibility at t invariant to post-t data
def test_no_lookahead():
    ns = synth("X", 10**9)
    t = SESS_IDX["2019-06-03"]
    g1, g2 = E.Guards(), E.Guards()
    before = E.illiq(ns, t, 21, g1)
    m1 = E.dvmed60(ns, t)
    # mutate everything AFTER t
    for i in range(t + 1, len(ns.dates)):
        ns.adj[i] *= 3.0
        ns.vol[i] *= 7.0
        ns.dv[i] = ns.adj[i] * ns.vol[i]
    assert E.illiq(ns, t, 21, g2) == before
    assert E.dvmed60(ns, t) == m1


# --- T2 next-bar execution: entry fill at t+1 ADJUSTED open
def test_next_bar_execution():
    panel = eligible_panel(60)
    sim = simulate(panel, SESSIONS, "illiq21", scored=False)
    h0 = next(h for h in sim["holds"] if h.fold == "F1_2019")
    ns = panel[h0.code]
    fi = ns.idx[h0.entry_fill_date]
    assert h0.entry_fill_date > h0.entry_decision
    assert h0.entry_px == pytest.approx(ns.adj_open(fi), rel=1e-12)


# --- T3 fold force-flat at fold LAST session close
def test_fold_force_flat():
    panel = eligible_panel(60)
    sim = simulate(panel, SESSIONS, "illiq21", scored=False)
    f1_last = [s for s in SESSIONS if "2019-01-01" <= s <= "2019-12-31"][-1]
    leftovers = [h for h in sim["holds"]
                 if h.fold == "F1_2019" and h.exit.kind == "fold"]
    assert leftovers, "expected fold exits in F1"
    for h in leftovers:
        ns = panel[h.code]
        assert h.exit.fill_date == f1_last
        assert h.exit.fill_px == pytest.approx(ns.adj[ns.idx[f1_last]], rel=1e-12)


# --- T4 cost exactly once per fill (entry once + exit once)
def test_cost_once():
    panel = eligible_panel(60)
    sim = simulate(panel, SESSIONS, "illiq21", scored=True)
    for h in sim["holds"]:
        w = h.weight
        band = E.band_bps(5e7)  # all synth names: adj~50 x 1e6 = 5e7 -> band A
        assert h.entry_cost == pytest.approx(band * 1e-4 * h.notional, rel=1e-9)
        assert h.exit_cost == pytest.approx(h.exit.band_bps * 1e-4 * h.notional,
                                            rel=1e-9)


# --- T5 participation-cap arithmetic + inertness at AUM_ref
def test_cap_arithmetic():
    book = ["A", "B"] + [f"C{i}" for i in range(8)]
    dvmeds = {c: 2_000_000.0 for c in book}
    w = E.weights_for(book, dvmeds)
    for c in book:
        assert w[c] == pytest.approx(min(0.1, 0.15 * 2e6 / 1e6), rel=1e-12)  # 0.1
    dvmeds2 = {c: 1e12 for c in book}
    w2 = E.weights_for(book, dvmeds2)
    assert all(w2[c] == pytest.approx(0.1, rel=1e-12) for c in book)  # cap inert


# --- T6/T7 guard classes i & ii: excluded + counted, never raise
def test_guard_class_i_and_ii():
    ns = synth("X", 10**9, adj_override={"2019-03-05": 0.0},   # class i
               vol_override={"2019-03-11": 0.0})               # class ii
    t = SESS_IDX["2019-03-20"]
    g = E.Guards()
    val = E.illiq(ns, t, 21, g)
    assert val is not None
    assert g.formation_skip_ret >= 1          # the adj==0 day excluded
    assert g.formation_skip_dv >= 1           # the zero-volume day excluded


# --- T8 classes iii/iv FAIL LOUD
def test_class_iii_fails_loud():
    with pytest.raises(E.FailLoud):
        E.weights_for([], {})
    with pytest.raises(E.FailLoud):
        EV.fold_summary([], "F1_2019")


# --- T9 death contract: mid-hold death -> final served close, counted
def test_death_contract():
    panel = eligible_panel(60)
    # fixture ILLIQ = ret*(1+ret)^-k peaks near ret~1/266 (i~36): the first
    # book is N034..N045; pick a confirmed in-book member as the victim
    victim = panel["N039"]
    # N000 stops trading mid-2019 (after entering the book is possible)
    grid = E.build_grid(SESSIONS)
    # truncate victim right after the first grid date's fill
    t0 = grid[0]
    fill0 = SESSIONS[SESS_IDX[t0] + 1]
    dates = [d for d in victim.dates if d <= fill0]
    keep = len(dates)
    for attr in ("dates", "open_raw", "close_raw", "adj", "vol", "dv", "adj_ok"):
        getattr(victim, attr)[:] = getattr(victim, attr)[:keep]
    victim.idx = {d: i for i, d in enumerate(victim.dates)}
    sim = simulate(panel, SESSIONS, "illiq21", scored=False)
    deaths = [h for h in sim["holds"] if h.exit.kind == "death"]
    assert any(h.code == "N039" for h in deaths)
    for h in deaths:
        ns = panel[h.code]
        last_ok = max(i for i in range(len(ns.dates)) if ns.adj_ok[i])
        assert h.exit.fill_px == pytest.approx(ns.adj[last_ok], rel=1e-12)
    assert sim["guards"].death_exits == len(deaths)


# --- T10 bookability floor: 45 unbookable / 46 bookable
def test_bookability_floor():
    p45 = eligible_panel(45)
    sim45 = simulate(p45, SESSIONS, "illiq21", scored=False)
    assert all(not d["bookable"] for d in sim45["per_date"])
    p46 = eligible_panel(46)
    sim46 = simulate(p46, SESSIONS, "illiq21", scored=False)
    assert any(d["bookable"] for d in sim46["per_date"])
    bookable = [d for d in sim46["per_date"] if d["bookable"]]
    assert all(d["n_book"] == 10 for d in bookable)  # ceil(46/5)=10


# --- T11 rank-count quintile + lexicographic tie-break
def test_rank_count_quintile():
    scores = {f"A{i:03d}": float(i) for i in range(100)}
    book = E.rank_book(scores)
    assert len(book) == 20 and book[0] == "A099" and "A080" in book \
        and "A079" not in book
    scores_tie = {c: 1.0 for c in ("B", "A", "C")}
    assert E.rank_book(scores_tie) == ["A"]  # ceil(3/5)=1; tie -> lexicographic


# --- T12 determinism
def test_determinism():
    p1 = eligible_panel(50)
    p2 = eligible_panel(50)
    s1 = simulate(p1, SESSIONS, "illiq21", scored=False)
    s2 = simulate(p2, SESSIONS, "illiq21", scored=False)
    assert repr(s1["per_date"]) == repr(s2["per_date"])
    assert repr([(h.code, h.entry_px, h.exit) for h in s1["holds"]]) == \
           repr([(h.code, h.entry_px, h.exit) for h in s2["holds"]])


# --- T13 S1 refusal + T14 exactly-3-cells
def test_s1_refusal_and_cells():
    from samv1 import run_cells
    assert len(run_cells.CELLS) == 3
    assert len({c for c, _ in run_cells.CELLS}) == 3
    argv_backup = sys.argv
    try:
        sys.argv = ["run_cells.py", "--mode", "dry-run", "--s1"]
        assert run_cells.main() == 9
    finally:
        sys.argv = argv_backup


# --- T15 split-basis: DV continuity across a 2:1 split under EODHD basis
def test_split_basis_dv():
    # raw close halves; adjusted smooth; volume (split-adjusted) unchanged
    ns = synth("X", 10**9, adj0=100.0, vol=1e6)
    split_i = SESS_IDX["2020-08-31"]
    for i in range(split_i, len(ns.dates)):
        ns.close_raw[i] = ns.close_raw[i] / 2.0     # raw basis drops
        ns.open_raw[i] = ns.open_raw[i] / 2.0
        # adj & vol (EODHD basis) stay smooth -> DV continuous
    dv_before = ns.dv[split_i - 1]
    dv_after = ns.dv[split_i]
    assert dv_after == pytest.approx(dv_before * (1 + 0.0005), rel=1e-9)
    # the frozen pair is adj*vol by construction in the loader; assert identity
    assert ns.dv[split_i] == pytest.approx(ns.adj[split_i] * ns.vol[split_i],
                                           rel=1e-12)


# --- T16 dry-run leak scan catches forbidden keys at any depth
def test_dryrun_leak_scan():
    with pytest.raises(E.FailLoud):
        assert_no_outcome_fields({"a": {"nested": [{"pnl": 1.0}]}})
    assert_no_outcome_fields({"a": {"n_book": 3}})  # clean passes
