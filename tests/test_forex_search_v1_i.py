"""FOREX-SEARCH-V1 I-lane tests (lane fsearch-i).

SANITIZED SYNTHETIC FIXTURES ONLY — no archive data, no staging bytes,
no network, and NO scored output of any kind (the numbers below are
hand-computed fixture arithmetic, not strategy evidence).

Covers:
  * engine determinism + positions-digest convention (S-lane compatible)
  * one-rollover financing charge arithmetic (9.4 bps stress worst case)
  * dual-books sign invariance (checker sensitivity included)
  * fold force-flat gating
  * harness kill-rule behavior on hand-computed fixtures
    (R1/R2/R3/R4/R5/R6/K6, dual-books, P-20 re-check, Stage-A)
  * R0_NOT_RUN / PBO NOT_RUN labels on every produced verdict skeleton
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
I_DIR = WT / "research/control/forex_search_v1_run/i"
sys.path.insert(0, str(I_DIR))

import i_engine as eng  # noqa: E402
import adjudicate as adj  # noqa: E402

FROZEN_IDS = [
    "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG",
    "FSS-OPEN-GAP-CONFIRM-Q50",
    "FSS-VOL-DRIFT-MOM-L63",
]
SYNTH_LEGS = ["EURUSD", "GBPUSD"]  # relative order kept from the manifest


# ---------------------------------------------------------------- fixtures

def synth_dates(n: int) -> list:
    out = []
    d = date(2010, 1, 4)
    while len(out) < n:
        if d.isoweekday() <= 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def synth_legs(n: int = 420, intra: str = "flat") -> dict:
    """Deterministic OHLC legs (no RNG): opens drift on a slow sinusoid;
    close[i] = open[i] * (1 + r_i) with r_i a small deterministic pattern
    ('flat' = +10 bps intra-session everywhere; 'clock' = +30 bps on
    day-of-month >= 16, +12 bps otherwise)."""
    dates = synth_dates(n)
    legs = {}
    for k, ln in enumerate(SYNTH_LEGS):
        o = np.array([1.0 + 0.002 * np.sin((i + 5 * k) / 9.0) + 1e-5 * i
                      for i in range(n)])
        r = np.empty(n)
        for i in range(n):
            day = int(dates[i][8:10])
            if intra == "clock":
                r[i] = 0.0030 if day >= 16 else 0.0012
            else:
                r[i] = 0.0010
        c = o * (1.0 + r)
        h = np.maximum(o, c) * 1.0002
        low = np.minimum(o, c) * 0.9998
        legs[ln] = {"symbol": ln, "dates": dates, "open": o, "high": h,
                    "low": low, "close": c}
    return legs


@pytest.fixture(scope="module")
def ctx420():
    legs = synth_legs(420)
    master = legs["EURUSD"]["dates"]
    folds = eng.p0().make_folds(master)
    return {"legs": legs, "master": master, "folds": folds}


def arm_cfg(config_id: str, freeze=None) -> dict:
    freeze = freeze or eng.load_freeze()
    sel = next(s for s in freeze["selections"]
               if s["config_id"] == config_id)
    return sel["config_manifest_excerpt_verbatim"]


def t(gross: float, fold: int = 1, leg: str = "EURUSD",
      state: str = "side+1", mi: int = 0) -> dict:
    """Minimal hand trade for rule fixtures (financed = gross − 9.4 at
    stress 2.0)."""
    return {"leg": leg, "fold": fold, "gross_bps": gross, "mi_decision": mi,
            "state_key": state, "side": 1 if "+1" in state else -1,
            "decision_date": "2010-01-04", "entry": 1.0, "exit": 1.0}


def base_ctx(config_id: str, family: str, trades: list, **kw) -> dict:
    ctx = {
        "config_id": config_id, "family": family, "trades": trades,
        "stress": 2.0, "folds": {"boundaries_index": [0, 1, 2, 3]},
        "master": synth_dates(6),
        "complement_trades": kw.pop("complement_trades", []),
        "trend_only_trades": kw.pop("trend_only_trades", None),
        "trend_only_definition": kw.pop("trend_only_definition", "fixture"),
        "clock_only_trades": kw.pop("clock_only_trades", None),
        "weekday_census": kw.pop("weekday_census",
                                 {"max_weekday_share": 0.2,
                                  "total_fired": len(trades)}),
        "usd": kw.pop("usd", {"per_leg_corr": {k: 0.05 for k in SYNTH_LEGS},
                              "pooled_corr": 0.01}),
        "shadows": kw.pop("shadows", {}),
        "k6_fold_nets": kw.pop("k6_fold_nets", None),
        "mutated_positions": kw.pop("mutated_positions", None),
        "serial_clustering": kw.pop("serial_clustering", {}),
    }
    ctx.update(kw)
    return ctx


# ------------------------------------------------------------ freeze inputs

def test_load_freeze_and_sha_pin():
    freeze = eng.load_freeze()
    assert [s["config_id"] for s in freeze["selections"]] == FROZEN_IDS
    assert freeze["schema"] == "selection_freeze@1"
    with pytest.raises(eng.Stop) as ei:
        orig = eng.FREEZE_SHA256
        eng.FREEZE_SHA256 = "0" * 64
        try:
            eng.load_freeze()
        finally:
            eng.FREEZE_SHA256 = orig
    assert ei.value.code == "FROZEN_SHA_MISMATCH"


def test_engine_determinism_and_frozen_warmups(ctx420):
    freeze = eng.load_freeze()
    legs, master, folds = ctx420["legs"], ctx420["master"], ctx420["folds"]
    for cid in FROZEN_IDS:
        cfg = arm_cfg(cid, freeze)
        p1 = eng.build_positions(cfg, legs, master, folds, SYNTH_LEGS)
        p2 = eng.build_positions(cfg, legs, master, folds, SYNTH_LEGS)
        for ln in SYNTH_LEGS:
            assert np.array_equal(p1[ln], p2[ln])
            assert set(np.unique(p1[ln])).issubset({-1, 0, 1})
        # warmup law: no firing before the frozen first decision bar
        fam = cfg["family"]
        first_idx = eng.FIRST_DECISION_BAR[fam] - 1
        for ln in SYNTH_LEGS:
            assert np.count_nonzero(p1[ln][:first_idx]) == 0
        # digest convention identical to the S-lane (sha256_obj of ints)
        d1 = eng.positions_digest(p1, SYNTH_LEGS)
        d2 = eng.sha256_obj({k: [int(x) for x in p1[k]] for k in SYNTH_LEGS})
        assert d1 == d2


def test_verify_positions_against_freeze_like():
    pos = {"EURUSD": np.array([1, 0, -1], dtype=np.int8),
           "GBPUSD": np.array([0, 1, 0], dtype=np.int8)}
    dig = eng.positions_digest(pos, SYNTH_LEGS)
    good = {"selections": [{"config_id": "X", "positions_digest": dig}]}
    eng.verify_positions_vs_freeze(good, "X", pos, SYNTH_LEGS)  # no raise
    bad = {"selections": [{"config_id": "X", "positions_digest": "f" * 64}]}
    with pytest.raises(eng.Stop) as ei:
        eng.verify_positions_vs_freeze(bad, "X", pos, SYNTH_LEGS)
    assert ei.value.code == "INPUT_MISMATCH"
    with pytest.raises(eng.Stop) as ei2:
        eng.verify_positions_vs_freeze(good, "MISSING", pos, SYNTH_LEGS)
    assert ei2.value.code == "INPUT_MISMATCH"


# ------------------------------------------------------- force-flat gating

def test_force_flat_at_fold_boundary():
    n = 6
    legs = synth_legs(n)
    master = legs["EURUSD"]["dates"]
    folds = {"boundaries_index": [0, 3, 6]}  # fold 1: 0..2, fold 2: 3..5
    fold_id = eng.fold_ids(folds, n)
    # FIRST-half state via the frozen P0 engine, warmup 0, so every bar fires
    st = eng.p0().state_clock_cond(legs["EURUSD"], master, dow=None,
                                   monthpos="FIRST", direction="LONG",
                                   warmup_master=0)
    assert set(st.keys()) == {0, 1, 2, 3, 4, 5}
    assert eng.gate_firing(1, "LONG", "EURUSD", legs, master, fold_id) is True
    # decision bar 2 is the last bar of fold 1; its execution bar is the
    # first bar of fold 2 -> force-flat refuses
    assert eng.gate_firing(2, "LONG", "EURUSD", legs, master, fold_id) is False
    # beyond-sample execution also refuses
    assert eng.gate_firing(5, "LONG", "EURUSD", legs, master, fold_id) is False


def test_trades_never_cross_folds_and_census_matches_positions(ctx420):
    freeze = eng.load_freeze()
    legs, master, folds = ctx420["legs"], ctx420["master"], ctx420["folds"]
    fold_id = eng.fold_ids(folds, len(master))
    for cid in FROZEN_IDS:
        cfg = arm_cfg(cid, freeze)
        pos = eng.build_positions(cfg, legs, master, folds, SYNTH_LEGS)
        trades = eng.build_trades(pos, legs, master, folds, SYNTH_LEGS)
        # build_trades raises CONTRACT_VIOLATION on any fold crossing;
        # assert the attribution law independently
        for tr in trades:
            assert tr["fold"] == fold_id[tr["mi_decision"]]
        # rebuilt per-fold fired counts equal the counts from positions
            rebuilt = {str(f): 0 for f in (1, 2, 3)}
            for ln in SYNTH_LEGS:
                for mi in np.nonzero(pos[ln])[0]:
                    rebuilt[str(fold_id[int(mi)])] += 1
            from_counts = eng.substate_counts(trades)
            per_fold = {str(f): sum(from_counts.get(str(f), {}).values())
                        for f in (1, 2, 3)}
            assert per_fold == rebuilt


# ------------------------------------------- cost + financing ladder (F4)

def test_one_rollover_financing_arithmetic_and_stress_worst_case():
    # one session, one round trip = 2 fills; gross 0 bps
    trades = [t(0.0, fold=1)]
    p1, f1 = eng.ladder_bps(trades, 1.0)
    assert p1[0] == pytest.approx(-3.0)     # 2 fills x 1.5 bps
    assert f1[0] == pytest.approx(-4.7)     # price - 1 night x 1.7 bps
    p2, f2 = eng.ladder_bps(trades, 2.0)
    assert p2[0] == pytest.approx(-6.0)     # stress on costs
    assert f2[0] == pytest.approx(-9.4)     # 2x1.5x2.0 + 1.7x2.0 WORST CASE
    assert eng.WORST_CASE_ROUND_TRIP_BPS == pytest.approx(9.4)
    # positive trade keeps the same absolute ladder
    p, f = eng.ladder_bps([t(100.0)], 2.0)
    assert p[0] == pytest.approx(94.0)
    assert f[0] == pytest.approx(90.6)


def test_sign_invariance_financed_never_adds_and_inversion_kill():
    grosses = [5.0, -20.0, 60.0, -7.5, 12.0]
    trades = [t(g) for g in grosses]
    price, financed = eng.ladder_bps(trades, 2.0)
    assert np.all(financed <= price + 1e-12)          # never ADDS pnl
    assert financed.sum() <= price.sum() + 1e-12
    chk = eng.dual_books_check(trades, 2.0)
    assert chk["pass"] is True
    assert chk["financed_never_adds_pnl"] is True
    assert chk["sign_inversion"] is False
    # inversion fixture: price book positive, financed book negative
    inv = [t(4.0)]  # price = 4 - 3 = +1.0 ; financed = 4 - 4.7 = -0.7
    chk_inv = eng.dual_books_check(inv, 1.0)
    assert chk_inv["sign_inversion"] is True
    assert chk_inv["pass"] is False
    # checker sensitivity: a NEGATIVE financing charge would ADD pnl and
    # must be flagged (fixture override only; never a production path)
    chk_add = eng.dual_books_check(trades, 1.0, fin_bps=-1.0)
    assert chk_add["financed_never_adds_pnl"] is False
    assert chk_add["pass"] is False


# ------------------------------------------------------------ rule R1 / R2

def test_r1_expectancy_kill_and_pass():
    good = [t(500.0), t(500.0), t(500.0), t(-20.0)]
    row = adj.r1_expectancy(base_ctx("X", "OPEN-GAP", good))
    assert row["verdict"] == "PASS"
    # financed expectancy = mean(gross - 9.4) = (1500 - 20 - 37.6)/4 > 0
    bad = [t(-10.0), t(-10.0)]
    row = adj.r1_expectancy(base_ctx("X", "OPEN-GAP", bad))
    assert row["verdict"] == "KILL"
    row = adj.r1_expectancy(base_ctx("X", "OPEN-GAP", []))
    assert row["verdict"] == "NOT_RUN"


def test_r2_pf_floor_fold_positivity_and_population_floor():
    # PF < 1.10 with positive expectancy -> R2 kills
    # financed: 10 wins x +105 (gross 114.4), 10 losses x -100 (gross
    # -90.6): net +50 > 0, PF = 1050/1000 = 1.05 < 1.10
    trades = [t(114.4)] * 10 + [t(-90.6)] * 10
    row = adj.r2_robustness(base_ctx("X", "OPEN-GAP", trades))
    assert row["verdict"] == "KILL"
    assert row["detail"]["pf_pass"] is False
    assert row["detail"]["floor_pass"] is False  # folds 2,3 unpopulated
    # fold positivity failure: big fold-1 win, fold-2 loss, PF fine
    trades = [t(500.0, fold=1)] * 11 + [t(-30.0, fold=2)] * 11 + \
        [t(500.0, fold=3)] * 11
    row = adj.r2_robustness(base_ctx("X", "OPEN-GAP", trades))
    assert row["verdict"] == "KILL"
    assert row["detail"]["fold_positivity"] is False
    assert row["detail"]["pf_pass"] is True
    # pure population-floor failure: all folds positive, PF fine,
    # fold 3 has only 5 fired decisions of its state
    trades = ([t(500.0, fold=1)] * 11 + [t(500.0, fold=2)] * 11 +
              [t(500.0, fold=3)] * 5)
    row = adj.r2_robustness(base_ctx("X", "OPEN-GAP", trades))
    assert row["verdict"] == "KILL"
    assert row["detail"]["fold_positivity"] is True
    assert row["detail"]["pf_pass"] is True
    assert row["detail"]["floor_pass"] is False
    assert "3" in row["detail"]["floor_failures"]
    # full pass: >= 10 per state per fold, all folds positive, PF >= 1.10
    trades = ([t(500.0, fold=f) for f in (1, 2, 3) for _ in range(11)] +
              [t(-100.0, fold=f, state="side-1") for f in (1, 2, 3)
               for _ in range(10)])
    row = adj.r2_robustness(base_ctx("X", "OPEN-GAP", trades))
    assert row["verdict"] == "PASS"
    assert row["detail"]["pf_pass"] is True
    assert row["detail"]["fold_positivity"] is True
    assert row["detail"]["floor_pass"] is True


# ------------------------------------------------------------ rule R3 / R4

def _populated(gross: float, leg: str = "GBPUSD") -> list:
    """Complement/control book with the population floor cleared:
    >= 10 fired decisions in EVERY fold."""
    return [t(gross, fold=f, leg=leg) for f in (1, 2, 3) for _ in range(11)]


def test_r3_complement_out_earn_tie_self_fail_and_degenerate():
    cand = [t(500.0, fold=f) for f in (1, 2, 3) for _ in range(11)]
    # financed net = 33 x 490.6
    # complement OUT-EARNS -> KILL
    row = adj.r3_mechanism(base_ctx("X", "OPEN-GAP", cand,
                                    complement_trades=_populated(600.0)))
    assert row["verdict"] == "KILL"
    # TIE (equal nets) -> KILL (>= comparison)
    row = adj.r3_mechanism(base_ctx("X", "OPEN-GAP", cand,
                                    complement_trades=_populated(500.0)))
    assert row["verdict"] == "KILL"
    # self-failing complement still kills (V15 precedent)
    row = adj.r3_mechanism(base_ctx("X", "OPEN-GAP", cand,
                                    complement_trades=_populated(-500.0)))
    assert row["verdict"] == "KILL"
    # complement strictly between 0 and candidate -> PASS
    row = adj.r3_mechanism(base_ctx("X", "OPEN-GAP", cand,
                                    complement_trades=_populated(100.0)))
    assert row["verdict"] == "PASS"
    # degenerate (empty) complement -> NOT_RUN both ways, never a PASS
    row = adj.r3_mechanism(base_ctx("X", "OPEN-GAP", cand,
                                    complement_trades=[]))
    assert row["verdict"] == "NOT_RUN"
    # sub-floor complement population -> NOT_RUN both ways
    row = adj.r3_mechanism(base_ctx("X", "OPEN-GAP", cand,
                                    complement_trades=[t(600.0, fold=1)]))
    assert row["verdict"] == "NOT_RUN"


def test_r4_trend_only_reproduction_and_clock_cond_not_adjudicable():
    cand = ([t(500.0, fold=1)] * 11 + [t(500.0, fold=2)] * 11 +
            [t(500.0, fold=3)] * 11)
    # fold nets (financed): 11 x 490.6 each.
    # trend-only reproduces folds 1 and 2 at >= 0.5x same-sign, not fold 3
    to = ([t(500.0, fold=1, leg="GBPUSD")] * 11 +
          [t(300.0, fold=2, leg="GBPUSD")] * 11 +
          [t(100.0, fold=3, leg="GBPUSD")] * 11)
    row = adj.r4_trend_reduction(base_ctx(
        "FSS-OPEN-GAP-CONFIRM-Q50", "OPEN-GAP", cand, trend_only_trades=to))
    assert row["verdict"] == "KILL"
    assert row["detail"]["reproduced_folds"] == [1, 2]
    # <= 1 reproduced fold -> PASS
    to = [t(100.0, fold=f, leg="GBPUSD") for f in (1, 2, 3) for _ in range(11)]
    row = adj.r4_trend_reduction(base_ctx(
        "FSS-OPEN-GAP-CONFIRM-Q50", "OPEN-GAP", cand, trend_only_trades=to))
    assert row["verdict"] == "PASS"
    # opposite-sign shadow never reproduces
    to = [t(-500.0, fold=f, leg="GBPUSD") for f in (1, 2, 3) for _ in range(11)]
    row = adj.r4_trend_reduction(base_ctx(
        "FSS-OPEN-GAP-CONFIRM-Q50", "OPEN-GAP", cand, trend_only_trades=to))
    assert row["verdict"] == "PASS"
    # CLOCK-COND: NOT_ADJUDICABLE per the frozen D1 manifest, never PASS
    row = adj.r4_trend_reduction(base_ctx(
        "FSS-CLOCK-COND-MONTHPOS-SECOND-LONG", "CLOCK-COND", cand))
    assert row["verdict"] == "NOT_ADJUDICABLE"


# ------------------------------------------------------------ rule R5

def test_r5_clock_only_out_earn_and_weekday_share_breach():
    cand = [t(500.0)] * 33
    co_loses = [t(300.0, leg="GBPUSD")] * 33  # 290.6 < 490.6 per trade
    row = adj.r5_clock_geometry(base_ctx(
        "X", "OPEN-GAP", cand, clock_only_trades=co_loses,
        weekday_census={"max_weekday_share": 0.2, "total_fired": 33}))
    assert row["verdict"] == "PASS"
    co_earns_more = [t(600.0, leg="GBPUSD")] * 33
    row = adj.r5_clock_geometry(base_ctx(
        "X", "OPEN-GAP", cand, clock_only_trades=co_earns_more,
        weekday_census={"max_weekday_share": 0.2, "total_fired": 33}))
    assert row["verdict"] == "KILL"  # CLOCK-ONLY out-earns
    row = adj.r5_clock_geometry(base_ctx(
        "X", "OPEN-GAP", cand, clock_only_trades=co_loses,
        weekday_census={"max_weekday_share": 0.5, "total_fired": 33}))
    assert row["verdict"] == "KILL"  # weekday-share floor breach (0.35)


def test_weekday_share_of_firings_engine():
    master = synth_dates(20)  # starts Tuesday 2010-01-05? (2010-01-04 Mon)
    pos = {ln: np.zeros(20, dtype=np.int8) for ln in SYNTH_LEGS}
    for i in (0, 5, 10, 15):  # all Mondays
        pos["EURUSD"][i] = 1
    census = eng.weekday_share_of_firings(pos, master, SYNTH_LEGS)
    assert census["total_fired"] == 4
    assert census["shares"]["1"] == pytest.approx(1.0)
    assert census["max_weekday_share"] == pytest.approx(1.0)
    assert census["max_weekday_share"] > eng.R5_MAX_WEEKDAY_SHARE_FLOOR
    pos2 = {ln: np.zeros(20, dtype=np.int8) for ln in SYNTH_LEGS}
    for i in range(20):  # every session: 4 per weekday
        for ln in SYNTH_LEGS:
            pos2[ln][i] = 1
    census2 = eng.weekday_share_of_firings(pos2, master, SYNTH_LEGS)
    assert census2["max_weekday_share"] == pytest.approx(0.2)
    assert census2["max_weekday_share"] <= eng.R5_MAX_WEEKDAY_SHARE_FLOOR


# ------------------------------------------------------------ rule R6 / K6

def test_r6_usd_drift_per_leg_and_pooled_and_shadows():
    cand = [t(500.0)]
    ok = {"per_leg_corr": {"EURUSD": 0.05, "GBPUSD": -0.1},
          "pooled_corr": 0.08}
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand, usd=ok))
    assert row["verdict"] == "PASS"
    breach = {"per_leg_corr": {"EURUSD": 0.05, "GBPUSD": 0.25},
              "pooled_corr": 0.08}
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand, usd=breach))
    assert row["verdict"] == "KILL"
    pooled_only_breach = {"per_leg_corr": {"EURUSD": 0.05, "GBPUSD": 0.05},
                          "pooled_corr": 0.30}
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand,
                                    usd=pooled_only_breach))
    assert row["verdict"] == "KILL"
    unmeasurable = {"per_leg_corr": {"EURUSD": None, "GBPUSD": 0.05},
                    "pooled_corr": 0.01}
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand, usd=unmeasurable))
    assert row["verdict"] == "NOT_ADJUDICABLE"
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand, usd=None))
    assert row["verdict"] == "NOT_RUN"  # pooled-only law cannot PASS
    # shadow reproduction (>= 0.5x same-sign) kills; absent -> NOT_RUN rows
    shadows = {"DGS10-LEVEL": {"net_bps": 300.0,
                               "fold_net_bps": {"1": 300.0}}}
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand, shadows=shadows))
    assert row["verdict"] == "KILL"
    d = row["detail"]["macro_shadows"]
    assert d[0]["disposition"] == "REJECT"
    assert all(s["disposition"] == "NOT_RUN" for s in d[1:])
    # opposite-sign / sub-half shadow does NOT reproduce
    shadows = {"DGS10-LEVEL": {"net_bps": -300.0,
                               "fold_net_bps": {"1": -300.0}}}
    row = adj.r6_usd_macro(base_ctx("X", "OPEN-GAP", cand, shadows=shadows))
    assert row["verdict"] == "PASS"


def test_k6_dispositions():
    row = adj.k6_slow_drift(base_ctx("X", "OPEN-GAP", [t(500.0)]))
    assert row["verdict"] == "NOT_ADJUDICABLE"  # exact test NOT frozen at S
    assert "NOT_FROZEN_AT_S" in str(row["detail"]["exact_test"])
    ctx = base_ctx("X", "OPEN-GAP", [t(500.0)], k6_fold_nets={
        "fresh_state": {"1": 1.0, "2": 1.0, "3": 1.0},
        "delayed_state": {"1": 1.0, "2": 1.0, "3": 1.0},
        "fresh_complement": {"1": 1.0, "2": 1.0, "3": 1.0},
        "delayed_complement": {"1": 1.0, "2": 1.0, "3": 1.0}})
    row = adj.k6_slow_drift(ctx, exact_test=lambda *a: True)
    assert row["verdict"] == "KILL"
    row = adj.k6_slow_drift(ctx, exact_test=lambda *a: False)
    assert row["verdict"] == "PASS"


# ---------------------------------------------- dual-books / P-20 re-check

def test_dual_books_rule_wrapper():
    # inversion fixture at stress 1.0: price = 4 - 3 = +1.0,
    # financed = 4 - 4.7 = -0.7 (sign inversion -> KILL)
    row = adj.dual_books_rule(base_ctx("X", "OPEN-GAP", [t(4.0)],
                                       stress=1.0))
    assert row["verdict"] == "KILL"
    row = adj.dual_books_rule(base_ctx("X", "OPEN-GAP", [t(500.0)]))
    assert row["verdict"] == "PASS"


def test_p20_recheck_pass_kill_and_frozen_matrix():
    master = synth_dates(64)
    rng_a = np.array([1 if i % 3 == 0 else 0 for i in range(64)], dtype=np.int8)
    rng_b = np.array([1 if i % 5 == 0 else 0 for i in range(64)], dtype=np.int8)
    arms = {"A": {ln: rng_a for ln in SYNTH_LEGS},
            "B": {ln: rng_b for ln in SYNTH_LEGS}}
    out = adj.p20_recheck(arms, SYNTH_LEGS)
    assert out["verdict"] == "PASS"
    assert out["detail"][0]["books_distinct"] is True
    # identical books -> rho 1 -> not books-distinct -> KILL
    arms_same = {"A": {ln: rng_a for ln in SYNTH_LEGS},
                 "B": {ln: rng_a for ln in SYNTH_LEGS}}
    out_kill = adj.p20_recheck(arms_same, SYNTH_LEGS)
    assert out_kill["verdict"] == "KILL"
    # frozen-matrix mismatch -> fail-closed
    rho = out["detail"][0]["pooled_rho"]
    frozen = [{"arm_a": "A", "arm_b": "B",
               "pooled_rho": float(rho) + 0.5}]
    out = adj.p20_recheck(arms, SYNTH_LEGS, frozen_matrix=frozen)
    assert out["verdict"] == "KILL"
    frozen_ok = [{"arm_a": "A", "arm_b": "B", "pooled_rho": float(rho)}]
    out = adj.p20_recheck(arms, SYNTH_LEGS, frozen_matrix=frozen_ok)
    assert out["verdict"] == "PASS"


# ---------------------------------------------------------------- Stage-A

def _two_leg(trades: list, n_master: int = 6) -> dict:
    return base_ctx("X", "OPEN-GAP", trades, master=synth_dates(n_master),
                    mutated_positions={ln: np.zeros(n_master, dtype=np.int8)
                                       for ln in SYNTH_LEGS})


def test_stage_a_fold_positive_share_and_concentration():
    # all-positive, balanced book: the five structural subgates + P-11 pass,
    # but the per-session Sharpe of this small fixture is below the frozen
    # DSR deflation bar (N=33, alpha 0.10) -> Stage-A KILL (F-2 battery).
    trades = [t(500.0, fold=f, leg=ln, mi=f)
              for f in (1, 2, 3) for ln in SYNTH_LEGS for _ in range(10)]
    out = adj.stage_a(_two_leg(trades))
    assert out["subgates"]["fold_positive_share"]["pass"] is True
    assert out["subgates"]["concentration"]["pass"] is True
    assert out["subgates"]["mdd"]["pass"] is True
    assert out["subgates"]["stress_margin"]["pass"] is True
    assert out["subgates"]["drop_one"]["pass"] is True
    assert out["subgates"]["pit_mutation"]["pass"] is True
    assert out["subgates"]["p11_per_period_series"]["pass"] is True
    assert out["subgates"]["dsr"]["computed"] is True
    assert out["subgates"]["dsr"]["pass"] is False
    assert out["verdict"] == "KILL"
    # folds +,-,- : share 1/3 <= 50% -> fps kills
    trades = ([t(500.0, fold=1, leg=ln, mi=1) for ln in SYNTH_LEGS
               for _ in range(10)] +
              [t(-500.0, fold=f, leg=ln, mi=f) for f in (2, 3)
               for ln in SYNTH_LEGS for _ in range(10)])
    out = adj.stage_a(_two_leg(trades))
    assert out["subgates"]["fold_positive_share"]["share"] == \
        pytest.approx(1 / 3)
    assert out["subgates"]["fold_positive_share"]["pass"] is False
    assert out["verdict"] == "KILL"
    # concentration: fold 1 carries 22/30 of a positive total -> KILL
    trades = ([t(500.0, fold=1, leg=ln, mi=1) for ln in SYNTH_LEGS
               for _ in range(11)] +
              [t(500.0, fold=f, leg=ln, mi=f) for f in (2, 3)
               for ln in SYNTH_LEGS])
    out = adj.stage_a(_two_leg(trades))
    assert out["subgates"]["fold_positive_share"]["pass"] is True
    assert out["subgates"]["concentration"]["largest_fold_share"] == \
        pytest.approx(22.0 / 26.0)
    assert out["subgates"]["concentration"]["pass"] is False
    assert out["verdict"] == "KILL"


def test_stage_a_mdd_drop_one_and_pit_mutation():
    # MDD: consecutive heavy loss days on distinct decision dates
    master = synth_dates(6)
    trades = [t(-5000.0, fold=1, mi=i) for i in range(5)]
    mutated = {"EURUSD": np.zeros(6, dtype=np.int8)}
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", trades, master=master,
                               mutated_positions=mutated))
    assert out["subgates"]["mdd"]["max_drawdown_frac"] > 0.15
    assert out["subgates"]["mdd"]["pass"] is False
    assert out["verdict"] == "KILL"
    # drop-one: dropping EURUSD leaves a negative GBPUSD book -> KILL
    trades = ([t(500.0, fold=1, leg="EURUSD")] * 5 +
              [t(-500.0, fold=1, leg="GBPUSD")] * 20)
    mutated2 = {"EURUSD": np.zeros(6, dtype=np.int8),
                "GBPUSD": np.zeros(6, dtype=np.int8)}
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", trades,
                               mutated_positions=mutated2))
    assert out["subgates"]["drop_one"]["pass"] is False
    assert out["verdict"] == "KILL"
    # drop leaving an EMPTY book is NOT_ADJUDICABLE fail-closed
    trades = [t(500.0, fold=1, leg="EURUSD")] * 5
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", trades,
                               mutated_positions={"EURUSD": np.zeros(6)}))
    assert out["subgates"]["drop_one"]["adjudicable"] is False
    assert out["subgates"]["drop_one"]["pass"] is False
    # PIT mutation: mutated book EQUALS the original at a fired bar -> KILL
    orig = np.zeros(6, dtype=np.int8)
    orig[2] = 1
    trades = [t(500.0, fold=1, mi=2)]
    mut_eq = {"EURUSD": orig.copy()}
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", trades, master=master,
                               mutated_positions=mut_eq))
    assert out["subgates"]["pit_mutation"]["pass"] is False
    assert out["verdict"] == "KILL"
    # mutated book REFUSES (0) at every fired decision -> pass
    mut_zero = {"EURUSD": np.zeros(6, dtype=np.int8)}
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", trades, master=master,
                               mutated_positions=mut_zero))
    assert out["subgates"]["pit_mutation"]["pass"] is True
    # missing mutated book -> fail-closed KILL (never an inferred PASS)
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", trades, master=master))
    assert out["subgates"]["pit_mutation"]["pass"] is False
    assert out["verdict"] == "KILL"


def test_pit_mutation_engine_consecutive_calendar_breach(ctx420):
    """The honest consequence of the §6 law on a pure calendar state: the
    one-bar-earlier recomputation of a consecutive-firing calendar book is
    UNCHANGED on interior fired bars, so the control correctly flags it
    (CLOCK-COND is declared EXPECTED-TO-DIE; R5/Stage-A carry that)."""
    freeze = eng.load_freeze()
    legs, master, folds = ctx420["legs"], ctx420["master"], ctx420["folds"]
    cfg = arm_cfg("FSS-CLOCK-COND-MONTHPOS-SECOND-LONG", freeze)
    pos = eng.build_positions(cfg, legs, master, folds, SYNTH_LEGS)
    mut = eng.pit_mutated_positions(cfg, legs, master, folds, SYNTH_LEGS)
    breaches = 0
    total = 0
    for ln in SYNTH_LEGS:
        for mi in np.nonzero(pos[ln])[0]:
            total += 1
            if int(mut[ln][int(mi)]) == int(pos[ln][int(mi)]):
                breaches += 1
    assert total > 0
    assert breaches > 0  # consecutive second-half sessions reproduce
    ctx = base_ctx("FSS-CLOCK-COND-MONTHPOS-SECOND-LONG", "CLOCK-COND",
                   eng.build_trades(pos, legs, master, folds, SYNTH_LEGS),
                   master=master, mutated_positions=mut)
    out = adj.stage_a(ctx)
    assert out["subgates"]["pit_mutation"]["breach_count"] == breaches
    assert out["verdict"] == "KILL"


# -------------------------------------- Stage-A DSR + P-11 (F-2 remediation)

def test_norm_cdf_ppf_and_expected_max_sharpe():
    assert adj._norm_cdf(0.0) == pytest.approx(0.5)
    assert adj._norm_ppf(0.5) == pytest.approx(0.0, abs=1e-9)
    # standard normal table anchors
    assert adj._norm_ppf(0.975) == pytest.approx(1.959964, abs=1e-5)
    assert adj._norm_cdf(1.959964) == pytest.approx(0.975, abs=1e-6)
    # E[max SR] is monotone increasing in the trial count N (§5 N=33 grid,
    # §6 P-9 program-cumulative ~260)
    e5 = adj.expected_max_sharpe(5)
    e33 = adj.expected_max_sharpe(adj.DSR_FROZEN_GRID_N)
    e260 = adj.expected_max_sharpe(adj.DSR_PROGRAM_CUMULATIVE_N)
    assert 0 < e5 < e33 < e260
    assert e33 == pytest.approx(2.112401, abs=2e-6)   # N = frozen grid size
    assert e260 == pytest.approx(2.850201, abs=2e-6)  # program-cumulative


def test_deflated_sharpe_ratio_hand_recomputation():
    """Independent in-test reimplementation of the documented Bailey/LdP
    formula (Phi((SR - SR0) sqrt(T-1) / sqrt(1 - g3 SR + ((g4-1)/4) SR^2)))
    must reproduce the harness value for arbitrary deterministic series."""
    import math

    def reference(returns, n):
        r = np.asarray(returns, dtype=float)
        sd = float(np.std(r, ddof=1))
        sr = float(np.mean(r)) / sd
        z = (r - float(np.mean(r))) / sd
        g3 = float(np.mean(z ** 3))
        g4 = float(np.mean(z ** 4))
        sr0 = adj.expected_max_sharpe(n)
        stat = ((sr - sr0) * math.sqrt(r.size - 1)) / \
            math.sqrt(1.0 - g3 * sr + ((g4 - 1.0) / 4.0) * sr * sr)
        return 0.5 * (1.0 + math.erf(stat / math.sqrt(2.0))), sr

    rng = np.random.default_rng(20260917)
    for series in (np.array([1.0, 1.0, 0.5]),
                   np.array([0.02, 0.0025, -0.001, 0.03, 0.0] * 25),
                   rng.normal(0.001, 0.01, size=400)):
        for n in (5, adj.DSR_FROZEN_GRID_N, adj.DSR_PROGRAM_CUMULATIVE_N):
            got = adj.deflated_sharpe_ratio(series, n)
            want, sr = reference(series, n)
            assert got["computed"] is True
            assert got["dsr_probability"] == pytest.approx(want, abs=1e-12)
            assert got["sr_per_period"] == pytest.approx(sr, abs=1e-12)
    # zero-variance or degenerate series never PASS (fail-closed)
    for bad in (np.array([1.0, 1.0, 1.0]), np.array([1.0])):
        got = adj.deflated_sharpe_ratio(bad, 33)
        assert got["computed"] is False


def test_dsr_gate_alpha_bar_and_monotone_deflation():
    # the same SR-2.0 series: more trials + lower alpha => strictly more
    # deflation (probability ordering), and the gate bar is 1 - alpha
    wave = np.sin(np.linspace(0.0, 50.0, 250))
    wave = (wave - wave.mean()) / float(np.std(wave, ddof=1))
    series = (0.002 + 0.001 * wave).tolist()
    d5 = adj.deflated_sharpe_ratio(series, 5)["dsr_probability"]
    d33 = adj.deflated_sharpe_ratio(series, 33)["dsr_probability"]
    d260 = adj.deflated_sharpe_ratio(series, 260)["dsr_probability"]
    assert d5 > d33 > d260
    gate = adj.dsr_gate({"computed": True, "per_period_returns": series},
                        n_trials=adj.DSR_FROZEN_GRID_N, alpha=adj.DSR_ALPHA)
    assert gate["bar"] == pytest.approx(0.90)
    assert gate["pass"] == (gate["dsr_probability"] >= 0.90)
    assert gate["n_trials"] == 33 and gate["alpha"] == pytest.approx(0.10)
    # program-cumulative gate rows are REPORTED ONLY by construction in
    # stage_a: their bar is 1 - 0.05, never gating
    assert adj.DSR_PROGRAM_ALPHA == 0.05
    # uncomputable P-11 series -> gate fails closed
    gate_bad = adj.dsr_gate({"computed": False, "reason": "empty book"},
                            n_trials=33, alpha=0.10)
    assert gate_bad["computed"] is False and gate_bad["pass"] is False


def test_stage_a_p11_persistence_and_dsr_wiring():
    master = synth_dates(30)
    trades = [t(500.0, fold=1, leg=ln, mi=i) for i in range(5)
              for ln in SYNTH_LEGS for _ in range(2)]
    mut = {ln: np.zeros(30, dtype=np.int8) for ln in SYNTH_LEGS}
    ctx = base_ctx("X", "OPEN-GAP", trades, master=master,
                   mutated_positions=mut)
    out = adj.stage_a(ctx)
    p11 = out["subgates"]["p11_per_period_series"]
    assert p11["computed"] is True and p11["pass"] is True
    assert p11["n_periods"] == 30
    # per-period series persisted IN the verdict: active days carry the
    # financed net, flat days 0.0; digest deterministic
    active = [s for s in p11["series_persisted"] if s["financed_net_bps"]]
    assert len(active) == 5
    assert all(s["financed_net_bps"] == pytest.approx(4 * 490.6)
               for s in active)
    out2 = adj.stage_a(base_ctx("X", "OPEN-GAP", trades, master=master,
                                mutated_positions=mut))
    assert out2["subgates"]["p11_per_period_series"]["series_digest"] == \
        p11["series_digest"]
    # DSR subgate rides on the persisted series; program-cumulative row is
    # reported alongside and never gates
    dsr = out["subgates"]["dsr"]
    assert dsr["computed"] is True
    assert dsr["n_trials"] == 33 and dsr["alpha"] == pytest.approx(0.10)
    prog = dsr["reported_program_cumulative"]
    assert prog["n_trials"] == 260 and prog["alpha"] == pytest.approx(0.05)
    assert "REPORTED ONLY" in prog["role"]
    # persistence round-trip via persist_p11_series (E-runner surface)
    verdicts = [{"config_id": "X", "stage_a": out}]
    p11_path = Path("/tmp") / "fsearch_test_p11_series.json"
    sha = adj.persist_p11_series(verdicts, p11_path)
    blob = json.loads(p11_path.read_text())
    assert blob["schema"] == "fsearch_p11_per_period_series@1"
    assert blob["arms"]["X"] == p11["series_persisted"]
    import hashlib
    assert sha == hashlib.sha256(p11_path.read_bytes()).hexdigest()
    p11_path.unlink()


def test_stage_a_empty_book_p11_and_dsr_fail_closed():
    out = adj.stage_a(base_ctx("X", "OPEN-GAP", []))
    assert out["verdict"] == "NOT_RUN"
    assert out["subgates"]["empty_book"] == "NOT_RUN fail-closed"


# -------------------------------------------------- engine series helpers

def test_usd_basket_sign_convention_and_max_drawdown():
    n = 3
    legs = {
        "EURUSD": {"dates": synth_dates(n),
                   "open": np.array([1.0, 1.0, 1.0]),
                   "close": np.array([1.0, 1.0, 1.001])},
        "USDCAD": {"dates": synth_dates(n),
                   "open": np.array([1.0, 1.0, 1.0]),
                   "close": np.array([1.0, 1.0, 1.001])},
    }
    out = eng.usd_basket_series(legs, synth_dates(n), ["EURUSD", "USDCAD"])
    # session 1: EURUSD +10 bps pair -> USD side -10; USDCAD +10 -> +10
    assert out["per_leg_usd_side_bps"]["EURUSD"][1] == pytest.approx(-10.0)
    assert out["per_leg_usd_side_bps"]["USDCAD"][1] == pytest.approx(10.0)
    assert out["basket_bps"][1] == pytest.approx(0.0)
    assert eng.max_drawdown_frac(np.array([100.0, -2000.0])) == \
        pytest.approx(1.0 - (1.01 * 0.80) / 1.01)
    assert eng.max_drawdown_frac(np.array([0.0, 0.0])) == 0.0


def test_serial_clustering_census():
    pos = {"EURUSD": np.array([1, 1, 0, 1, 0, 0], dtype=np.int8),
           "GBPUSD": np.array([0, -1, -1, -1, 0, 1], dtype=np.int8)}
    out = eng.serial_clustering_census(pos, SYNTH_LEGS)
    assert out["per_leg"]["EURUSD"] == {"fired": 3, "consecutive_fired": 1}
    assert out["per_leg"]["GBPUSD"] == {"fired": 4, "consecutive_fired": 2}
    assert out["pooled_fired"] == 7
    assert out["pooled_consecutive_fired"] == 3
    assert out["trade_independence"] == "DECLARED NOT ASSUMED"


# ------------------------------------------- end-to-end ordered adjudication

def _survivor_context(ctx420):
    """A hand-built PIT-sensitive, weekday-spread, profitable fixture for
    the REAL CLOCK-COND config id (books synthesized — no engine run on
    real data). The book clears the FULL relaxed battery INCLUDING the F-2
    DSR gate (N=33, alpha 0.10): every session fires on both legs with a
    deterministic small/small-variance payoff, so the per-session Sharpe
    clears the frozen E[max SR] deflation bar; losses-free variance comes
    from the every-4th-session small-payoff pattern."""
    master = ctx420["master"]
    legs_order = SYNTH_LEGS
    n = len(master)
    positions = {ln: np.zeros(n, dtype=np.int8) for ln in legs_order}
    trades = []
    k = 0
    for mi in range(n):
        for ln in legs_order:
            positions[ln][mi] = 1
            fold = 1 if mi < 140 else (2 if mi < 280 else 3)
            gross = 60.0 if k % 8 == 7 else 120.0
            trades.append({"leg": ln, "mi_decision": mi,
                           "decision_date": master[mi],
                           "mi_exec": min(mi + 1, n - 1),
                           "exec_date": master[min(mi + 1, n - 1)],
                           "fold": fold, "side": 1, "entry": 1.0,
                           "exit": 1.0, "gross_bps": gross,
                           "state_key": "side+1"})
            k += 1
    complement = [t(20.0, fold=(1 if mi < 140 else (2 if mi < 280 else 3)),
                    leg="GBPUSD", mi=mi) for mi in range(n)]
    clock_only = [t(20.0, fold=(1 if mi < 140 else (2 if mi < 280 else 3)),
                    leg="GBPUSD", mi=mi) for mi in range(n)]
    mutated = {ln: np.zeros(n, dtype=np.int8) for ln in legs_order}
    census = eng.weekday_share_of_firings(positions, master, legs_order)
    return base_ctx("FSS-CLOCK-COND-MONTHPOS-SECOND-LONG", "CLOCK-COND",
                    trades, master=master, complement_trades=complement,
                    clock_only_trades=clock_only, mutated_positions=mutated,
                    weekday_census=census, serial_clustering={})


def _dsr_failing_context(ctx420):
    """The pre-F-2 'survivor' fixture: passes every ordered rule and the
    structural Stage-A subgates, but its sparse per-session series sits far
    below the frozen DSR deflation bar — the arm must NOT be a survivor."""
    master = ctx420["master"]
    legs_order = SYNTH_LEGS
    n = len(master)
    positions = {ln: np.zeros(n, dtype=np.int8) for ln in legs_order}
    mis = list(range(70, 394, 6))
    for ln in legs_order:
        for mi in mis:
            positions[ln][mi] = 1
    trades = []
    for mi in mis:
        fold = 1 if mi < 140 else (2 if mi < 280 else 3)
        for ln in legs_order:
            trades.append({"leg": ln, "mi_decision": mi,
                           "decision_date": master[mi], "mi_exec": mi + 1,
                           "exec_date": master[min(mi + 1, n - 1)],
                           "fold": fold, "side": 1, "entry": 1.0,
                           "exit": 1.003, "gross_bps": 30.0,
                           "state_key": "side+1"})
    complement = [t(20.0, fold=(1 if mi < 140 else (2 if mi < 280 else 3)),
                    leg="GBPUSD", mi=mi) for mi in mis]
    clock_only = [t(20.0, fold=(1 if mi < 140 else (2 if mi < 280 else 3)),
                    leg="GBPUSD", mi=mi) for mi in mis]
    mutated = {ln: np.zeros(n, dtype=np.int8) for ln in legs_order}
    census = eng.weekday_share_of_firings(positions, master, legs_order)
    return base_ctx("FSS-CLOCK-COND-MONTHPOS-SECOND-LONG", "CLOCK-COND",
                    trades, master=master, complement_trades=complement,
                    clock_only_trades=clock_only, mutated_positions=mutated,
                    weekday_census=census, serial_clustering={})


def test_adjudicate_arm_survivor_and_ordered_kill(ctx420):
    ctx = _survivor_context(ctx420)
    verdict = adj.adjudicate_arm(ctx)
    assert verdict["arm_verdict"] == "SURVIVOR_CANDIDATE"
    assert verdict["ordered_rules"][0]["rule"] == "R1"
    r4 = next(r for r in verdict["ordered_rules"] if r["rule"] == "R4")
    assert r4["verdict"] == "NOT_ADJUDICABLE"  # CLOCK-COND, frozen manifest
    k6 = next(r for r in verdict["ordered_rules"] if r["rule"] == "K6")
    assert k6["verdict"] == "NOT_ADJUDICABLE"  # exact test not frozen at S
    # non-killing, non-passing rules ride as DISCLOSURES on a survivor
    # (the same law that carries R0 NOT_RUN into the terminal name)
    assert set(verdict["incomplete_rules"]) == {"R4", "K6"}
    assert verdict["labels"]["r0_ancestry"] == "NOT_RUN"
    assert verdict["stage_a"]["verdict"] == "PASS"
    # F-2: the DSR gate COMPUTED at N=33 / alpha 0.10 and PASSED; the
    # program-cumulative row rides as REPORTED ONLY
    dsr = verdict["stage_a"]["subgates"]["dsr"]
    assert dsr["computed"] is True and dsr["pass"] is True
    assert dsr["n_trials"] == 33 and dsr["alpha"] == pytest.approx(0.10)
    assert dsr["reported_program_cumulative"]["n_trials"] == 260
    assert verdict["labels"]["r0_ancestry"] == "NOT_RUN"
    assert verdict["labels"]["pbo"] == "NOT_RUN"
    # a DSR-failing book: ordered battery + structural subgates pass but
    # the arm is NOT a survivor (fail-closed at the relaxed battery)
    weak = adj.adjudicate_arm(_dsr_failing_context(ctx420))
    assert weak["stage_a"]["subgates"]["dsr"]["computed"] is True
    assert weak["stage_a"]["subgates"]["dsr"]["pass"] is False
    assert weak["stage_a"]["verdict"] == "KILL"
    assert weak["arm_verdict"] == "REJECTED"
    # ordered first-binding kill: R1 kill leaves later rules NOT_EVALUATED
    bad = base_ctx("FSS-VOL-DRIFT-MOM-L63", "VOL-DRIFT", [t(-500.0)],
                   usd={"per_leg_corr": {"EURUSD": 0.9, "GBPUSD": 0.9},
                        "pooled_corr": 0.9})
    v2 = adj.adjudicate_arm(bad)
    assert v2["ordered_rules"][0]["verdict"] == "KILL"
    assert [r["verdict"] for r in v2["ordered_rules"][1:]] == \
        ["NOT_EVALUATED"] * 6
    assert v2["arm_verdict"] == "REJECTED"


def test_adjudicate_cycle_outcomes_and_labels(ctx420):
    ctx = _survivor_context(ctx420)
    n = len(ctx420["master"])
    pos = {ctx["config_id"]: {ln: np.zeros(n, dtype=np.int8)
                              for ln in SYNTH_LEGS}}
    for ln in SYNTH_LEGS:
        for mi in range(n):
            pos[ctx["config_id"]][ln][mi] = 1
    out = adj.adjudicate_cycle([ctx], pos, SYNTH_LEGS)
    assert out["survivors"] == ["FSS-CLOCK-COND-MONTHPOS-SECOND-LONG"]
    assert out["proposed_outcome_name"] == (
        "FOREX_SEARCH_V1_SURVIVORS_UNDER_RELAXED_BATTERY_R0_NOT_RUN_PBO_NOT_RUN")
    assert out["p20_recheck"]["verdict"] == "PASS"
    assert out["labels"]["r0_ancestry"] == "NOT_RUN"
    assert out["labels"]["pbo"] == "NOT_RUN"
    assert "owner-relaxed" in out["labels"]["relaxation_disclosure_verbatim"]
    # F-2: the survivor outcome name is emitted ONLY after the DSR gate
    # computed AND passed on every survivor
    assert out["dsr_gate_on_survivors"] == {
        "survivor_count": 1, "computed_and_passed_on_every_survivor": True}
    # F-8: explicit scored-cell budget counter on the cycle output
    assert out["scored_cell_budget"] == {
        "used": 1, "max": 3, "within_budget": True,
        "source": out["scored_cell_budget"]["source"]}
    # a DSR-failing arm that clears every ordered rule must NOT yield the
    # relaxed-battery survivor name (INCOMPLETE fail-closed instead)
    weak = _dsr_failing_context(ctx420)
    weak_pos = {weak["config_id"]: {ln: pos[ctx["config_id"]][ln].copy()
                                    for ln in SYNTH_LEGS}}
    for ln in SYNTH_LEGS:
        weak_pos[weak["config_id"]][ln][:] = 0
        for mi in range(70, 394, 6):
            weak_pos[weak["config_id"]][ln][mi] = 1
    out_weak = adj.adjudicate_cycle([weak], weak_pos, SYNTH_LEGS)
    assert out_weak["survivors"] == []
    assert out_weak["dsr_gate_on_survivors"] == {
        "survivor_count": 0, "computed_and_passed_on_every_survivor": False}
    assert out_weak["proposed_outcome_name"] == \
        "FOREX_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE"
    # budget breach is fail-closed (defensive; the freeze walk caps at 3)
    out_budget = adj.adjudicate_cycle([ctx, weak], {**pos, **weak_pos},
                                      SYNTH_LEGS)
    assert out_budget["scored_cell_budget"]["within_budget"] is True
    assert out_budget["proposed_outcome_name"] == \
        "FOREX_SEARCH_V1_INCOMPLETE_NOT_PROMOTABLE"  # weak arm kills it
    # all-rejected cycle -> REJECT_ALL outcome name
    bad = base_ctx("FSS-VOL-DRIFT-MOM-L63", "VOL-DRIFT", [t(-500.0)])
    bad_pos = {"FSS-VOL-DRIFT-MOM-L63": {ln: np.zeros(n, dtype=np.int8)
                                         for ln in SYNTH_LEGS}}
    out2 = adj.adjudicate_cycle([bad], bad_pos, SYNTH_LEGS)
    assert out2["proposed_outcome_name"] == "FOREX_SEARCH_V1_REJECT_ALL"


def test_verdict_skeleton_labels():
    skel = adj.build_verdict_skeleton(FROZEN_IDS)
    assert skel["labels"]["r0_ancestry"] == "NOT_RUN"
    assert skel["labels"]["pbo"] == "NOT_RUN"
    assert "R0 NOT_RUN" in skel["labels"]["r0_not_run_verbatim"]
    assert "PBO NOT_RUN" in skel["labels"]["pbo_not_run_verbatim"]
    assert "0.20" in skel["labels"]["r0_not_run_verbatim"]       # standing
    assert "0.30" in skel["labels"]["r0_not_run_verbatim"]       # relaxed
    assert "owner-relaxed" in \
        skel["labels"]["relaxation_disclosure_verbatim"]
    assert "1.7 bps" in skel["labels"]["financing_disclosure_verbatim"]
    assert skel["labels"]["no_scored_output_this_lane"] is True
    assert [a["config_id"] for a in skel["arms"]] == FROZEN_IDS
    assert all(a["arm_verdict"] is None for a in skel["arms"])
    # F-8: explicit scored-cell budget counter (pre-GO: nothing consumed)
    assert skel["scored_cell_budget"] == {
        "used": 0, "max": 3, "within_budget": True,
        "source": skel["scored_cell_budget"]["source"]}
    assert skel["scored_cell_budget"]["max"] == adj.SCORED_CELL_BUDGET_MAX


# ------------------------------------------------------------ real-data gate

def test_staging_loader_is_go_gated(monkeypatch):
    monkeypatch.delenv("FOREX_SEARCH_V1_GO_PHRASE", raising=False)
    with pytest.raises(eng.Stop) as ei:
        eng.load_staging_legs()
    assert ei.value.code == "SCORED_EXECUTION_NOT_AUTHORIZED"
    monkeypatch.setenv("FOREX_SEARCH_V1_GO_PHRASE", "not the phrase")
    with pytest.raises(eng.Stop) as ei2:
        eng.load_staging_legs()
    assert ei2.value.code == "SCORED_EXECUTION_NOT_AUTHORIZED"


def test_main_prints_skeleton_only(capsys):
    rc = adj.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "fsearch_i_verdict_skeleton@1" in out
    assert "NOT_RUN" in out

