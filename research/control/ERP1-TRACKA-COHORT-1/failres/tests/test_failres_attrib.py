"""failres-attrib tests — ERP1-TRACKA-COHORT-1 (ATTRIBUTION lane).

DIAGNOSTIC_OUTCOME_EXPOSED · FAILURE_ROOT_CAUSE_RESEARCH · PAPER_TIER.

Asserts (dispatch minimum + identity laws):
  1. fold reconciliation: EURUSD R-DAEMON per-fold nets (k=1.0, trades
     ENTERED in each falsifier FOLD_TABLE fold) reproduce the diag lane's
     DIAG_DAEMON_REPORT §3.2 numbers exactly (tolerance 0.05 pips), plus
     the §3.1 full-panel totals for all 5 EURUSD books and the GBPUSD
     R-DAEMON total / F3;
  2. gross + cost == net identity on 100 sampled trades of each pair
     (cost decomposition = SAME book re-run at k=0.0);
  3. daily join table sums == trade-table sums (per book, full panel and
     per fold).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest
     research/control/ERP1-TRACKA-COHORT-1/failres/tests/test_failres_attrib.py -q
(from the failres-attrib worktree root)
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
import pytest

FAILRES = (Path(__file__).resolve().parent.parent)
COHORT = FAILRES.parent
for p in (str(COHORT / "scripts"), str(COHORT / "diag" / "scripts"),
          str(FAILRES / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import failres_attrib_lib as L  # noqa: E402
import tracka_lib as T  # noqa: E402
import engine as E  # noqa: E402
import scored_lib as S  # noqa: E402
from falsifier_run import FOLD_TABLE  # noqa: E402

TOL = 0.05
FOLD_IDS = [f for f, _, _ in FOLD_TABLE]

# ---- diag reconciliation targets (DIAG_DAEMON_REPORT §3.1/§3.2) -------------
EURUSD_RDAEMON_FOLDS = {"F1": -188.8, "F2": -884.4, "F3": 1049.8,
                        "F4": 348.3, "F5": -191.5, "F6": 257.0}
EURUSD_TOTALS = {"R-DAEMON": 812.2, "R-ORIG": 7322.7, "R-ANCHOR": 1052.7,
                 "SHORT_ALWAYS": 704.6, "LONG_ALWAYS": -1665.5}
GBPUSD_RDAEMON_TOTAL = -1708.9
GBPUSD_RDAEMON_F3 = -1272.7


# ------------------------------------------------------------------ helpers --

def rebuild_k1(pair: str):
    """Rebuild the 5 books at k=1.0 only, via the authoritative law
    functions + committed engine (identical to build_books k=1.0 path)."""
    p = L.load_plane(pair)
    sess = ((~p.skip) & (p.hour >= 7) & (p.hour <= 18)).astype(np.int8)
    tgt_d, _, _ = T.f_rangeexp_daemon(p)
    tgts = {"R-DAEMON": tgt_d,
            "R-ORIG": T.f_rangeexp_orig(p),
            "R-ANCHOR": T.f_rangeexp_anchor_shift(p),
            "SHORT_ALWAYS": (-sess),
            "LONG_ALWAYS": sess}
    out = {}
    for arm, tgt in tgts.items():
        trades, _ = E.run_strategy(p, tgt, 1.0, warmup_end_idx=0)
        out[arm] = trades
    return out


def fold_nets(trades: list) -> dict:
    per = {f: 0.0 for f in FOLD_IDS}
    tot = 0.0
    for t in trades:
        v = float(t["pips"])
        tot += v
        fid = S.fold_of_ts(t["entry_ts"])
        if fid:
            per[fid] += v
    return {"total": round(tot, 2),
            "folds": {f: round(v, 2) for f, v in per.items()}}


@pytest.fixture(scope="module")
def committed():
    def load(name):
        return json.loads((FAILRES / name).read_text())
    return {n: load(n) for n in (
        "failres_attrib_trades_EURUSD.json",
        "failres_attrib_trades_GBPUSD.json",
        "failres_daily_EURUSD.json",
        "failres_daily_GBPUSD.json",
        "failres_attrib_agg_EURUSD.json",
        "failres_attrib_agg_GBPUSD.json")}


# --------------------------------------------------------------- 1. recon ----

def test_fold_reconciliation_eurusd_rdaemon():
    books = rebuild_k1("EURUSD")
    fn = fold_nets(books["R-DAEMON"])
    for f, v in EURUSD_RDAEMON_FOLDS.items():
        assert abs(fn["folds"][f] - v) <= TOL, \
            f"EURUSD R-DAEMON {f}: got {fn['folds'][f]}, diag {v}"


def test_full_panel_totals_eurusd_all_books():
    books = rebuild_k1("EURUSD")
    for arm, net in EURUSD_TOTALS.items():
        got = fold_nets(books[arm])["total"]
        assert abs(got - net) <= TOL, f"EURUSD {arm}: got {got}, diag {net}"
    assert len(books["R-DAEMON"]) == 1062


def test_gbpusd_rdaemon_total_and_f3():
    books = rebuild_k1("GBPUSD")
    fn = fold_nets(books["R-DAEMON"])
    assert abs(fn["total"] - GBPUSD_RDAEMON_TOTAL) <= TOL
    assert abs(fn["folds"]["F3"] - GBPUSD_RDAEMON_F3) <= TOL


# ------------------------------------- 2. gross + cost == net (100 sampled) --

@pytest.mark.parametrize("pair", ["EURUSD", "GBPUSD"])
def test_gross_plus_cost_equals_net_100_sampled(committed, pair):
    rows = [r for r in committed[f"failres_attrib_trades_{pair}.json"]["rows"]
            if r["book"] == "R-DAEMON"]
    rng = random.Random(20260926)
    sample = rng.sample(rows, 100)
    for r in sample:
        assert abs((r["gross_pips"] + r["cost_pips"]) - r["net_pips"]) \
            <= 0.011, f"identity violated on {r['entry_ts_utc']} {r['book']}"


# ------------------------------- 3. daily table sums == trade-table sums ----

@pytest.mark.parametrize("pair", ["EURUSD", "GBPUSD"])
def test_daily_sums_match_trade_sums(committed, pair):
    daily = committed[f"failres_daily_{pair}.json"]["rows"]
    recon = committed[f"failres_attrib_agg_{pair}.json"]["reconciliation"]["arms"]
    col = {"R-DAEMON": "net_daemon", "R-ORIG": "net_orig",
           "R-ANCHOR": "net_anchor", "SHORT_ALWAYS": "net_short",
           "LONG_ALWAYS": "net_long"}
    for arm, c in col.items():
        s = round(sum(r[c] for r in daily), 2)
        assert abs(s - recon[arm]["net_full_panel"]) <= TOL, \
            f"{pair} {arm}: daily sum {s} != trade sum " \
            f"{recon[arm]['net_full_panel']}"
    # per-fold identity for the daemon book
    per_fold_daily = {f: 0.0 for f in FOLD_IDS}
    for r in daily:
        if r["fold"]:
            per_fold_daily[r["fold"]] += r["net_daemon"]
    for f in FOLD_IDS:
        assert abs(round(per_fold_daily[f], 2)
                   - recon["R-DAEMON"]["per_fold_net"][f]) <= TOL


def test_committed_recon_block_matches_diag(committed):
    """The committed agg reconciliation block (produced by the run) must
    match the diag targets too (guards artifact drift)."""
    arms = committed["failres_attrib_agg_EURUSD.json"]["reconciliation"]["arms"]
    for f, v in EURUSD_RDAEMON_FOLDS.items():
        assert abs(arms["R-DAEMON"]["per_fold_net"][f] - v) <= TOL
    for arm, net in EURUSD_TOTALS.items():
        assert abs(arms[arm]["net_full_panel"] - net) <= TOL
    garms = committed["failres_attrib_agg_GBPUSD.json"]["reconciliation"]["arms"]
    assert abs(garms["R-DAEMON"]["net_full_panel"] - GBPUSD_RDAEMON_TOTAL) <= TOL
    assert abs(garms["R-DAEMON"]["per_fold_net"]["F3"] - GBPUSD_RDAEMON_F3) <= TOL
