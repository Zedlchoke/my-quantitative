"""V5 family-1 (SFV5-A6-H2-CROSS-SECTOR-COUPLING) evidence suite — lane A8.

Implements the preregistered family
``research/control/stocks_free_v5_run/proposals/a6_h2.json`` exactly
(anchor COUPLE63-BN-L3S3-42, neighbour COUPLE21-BN-L3S3-42, causal negative
control NOMPRICE42-BN-L3S3) through
``research/assets/stocks/coupling_family.py``, and produces the V4-shape
evidence list.  Discipline, restated so it cannot be missed:

* the module computes ZERO PnL anywhere: no return aggregation, no
  expectancy, no profit factor, no drawdown exists in it or in this suite;
* real-snapshot tests are SCHEDULE-ONLY plus the one preregistered
  PnL-free identifiability measurement (anchor coupling ranks vs NOMPRICE
  raw-price ranks — the A9-F measurement the selection freeze pins);
  every real read is clamped to the S0 window (no session after
  2025-07-31 is ever read — the module's calendar validator fails closed
  on S1 sessions);
* scored-looking numbers anywhere live on SYNTHETIC data only (keyed by
  the frozen 11-sector universe, as the arm contract requires), and the
  only published artifacts are structural digests (scored=false,
  real_pnl=false);
* writes go to pytest tmp directories plus the one lane artifact
  research/control/stocks_free_v5_run/i_family_1_schedule_check.json
  (dates and counts ONLY); canonical ledgers and frozen control
  artifacts are never written.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \\
      tests/assets/stocks/test_v5_family_coupling.py -q   (from worktree root)
"""

from __future__ import annotations

import datetime as dt
import functools
import hashlib
import json
import math
from pathlib import Path

import pytest

from research.assets.stocks.factory import (
    CASH_SYMBOL,
    GatedTrialLedger,
    assert_reconciles,
    etf_leg_turnover,
    fill_cost,
    publication_metrics,
    select_drop_one_symbol,
    value_book,
)
from research.assets.stocks.coupling_family import (
    ANCHOR_SESSION,
    ARM_IDS,
    ARM_KEY_ANCHOR,
    ARM_KEY_CONTROL,
    ARM_KEY_NEIGHBOUR,
    ARM_RULE_NAMES,
    ArmConfig,
    ArmConfigError,
    BASE_COST_BPS,
    BENCHMARK_SYMBOL,
    beta_map,
    book_digest,
    book_entries_blockwise,
    book_entries_walk,
    build_arm_configs,
    build_arm_schedule_blockwise,
    build_arm_schedule_walk,
    build_targets,
    CLOCK_PERIOD_SESSIONS,
    coupling_ranks,
    decide_at,
    dry_run_artifact,
    eligibility,
    estimate_turnover,
    FAMILY_ID,
    FamilyError,
    FOLDS,
    GROSS_CAP,
    HEDGE_ABS_CAP,
    hedge_weight,
    HOLDING_SESSIONS,
    LEG_WEIGHT,
    membership_churn,
    MIN_ELIGIBLE,
    nomprice_ranks,
    ols_slope,
    Panel,
    pearson,
    rebuild_targets_excluding,
    return_series,
    S0_END,
    schedule_feasibility,
    schedules_equal,
    SECTOR_SYMBOLS,
    STRESS_COST_BPS,
    TURNOVER_CEILING_TWO_WAY_PER_YEAR,
    WARMUP_SESSIONS,
    validate_book,
)

WORKTREE_ROOT = Path(__file__).resolve().parents[3]
STAGING = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging")
PROPOSAL_PATH = (WORKTREE_ROOT / "research" / "control" / "stocks_free_v5_run"
                 / "proposals" / "a6_h2.json")
BASELINE_PATH = (WORKTREE_ROOT / "research" / "control" / "stocks_free_v5_run"
                 / "baseline_invariants.json")
SELECTION_PATH = (WORKTREE_ROOT / "research" / "control" / "stocks_free_v5_run"
                  / "selection_freeze.json")
SCHEDULE_CHECK_PATH = (WORKTREE_ROOT / "research" / "control"
                       / "stocks_free_v5_run" / "i_family_1_schedule_check.json")

CFGS = build_arm_configs()

# --------------------------------------------------------------------------- #
# synthetic calendars and deterministic panels (frozen universe, no RNG)
# --------------------------------------------------------------------------- #
#: The hand-fixture universe: six frozen sectors + the benchmark.
GOLD_SYMS = ("XLB", "XLF", "XLK", "XLE", "XLI", "XLP")

#: Small exact fixture: 5 dyadic closes -> 4 hand-computable returns.
SMALL_DATES = ["2030-01-01", "2030-01-02", "2030-01-03", "2030-01-04",
               "2030-01-05"]

#: Period-4 return patterns (x0.01) tiled over the full calendar.
PAT_A = (0.01, -0.01, 0.01, -0.01)     # SPY / XLB / XLK (and -A for XLE)
PAT_B = (0.01, 0.01, -0.01, -0.01)     # the remaining eight sectors
DECISION_T = 400                        # decision index for full fixtures


def weekday_sessions(start: str, end: str) -> list[str]:
    d = dt.date.fromisoformat(start)
    last = dt.date.fromisoformat(end)
    out = []
    while d <= last:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


#: Full synthetic calendar: warmup 252 exists before the first used decision
#: index; spans all three frozen folds; ends inside S0.
FULL_DATES = weekday_sessions("2016-01-04", "2025-07-30")

#: Hand-fixture closes (small): see test_e01a for the exact derivation.
SMALL_CLOSES = {
    "XLB": [100.0, 100.0, 150.0, 150.0, 75.0],   # A = (0, +.5, 0, -.5)
    "XLF": [100.0, 150.0, 150.0, 75.0, 75.0],    # B = (+.5, 0, -.5, 0)
    "XLK": [100.0, 100.0, 150.0, 150.0, 75.0],   # A (identical to XLB)
    "XLE": [100.0, 100.0, 50.0, 50.0, 75.0],     # -A
    "XLI": [100.0, 150.0, 150.0, 75.0, 75.0],    # B (identical to XLF)
    "XLP": [100.0, 200.0, 250.0, 500.0, 625.0],  # C = (+1, +.25, +1, +.25)
    "SPY": [100.0, 100.0, 150.0, 150.0, 75.0],   # benchmark = A
}


def small_panel(raw_levels: dict[str, float] | None = None) -> Panel:
    adj = {s: dict(zip(SMALL_DATES, closes))
           for s, closes in SMALL_CLOSES.items()}
    raw = None
    if raw_levels is not None:
        raw = {s: {SMALL_DATES[-1]: lvl} for s, lvl in raw_levels.items()}
    return Panel(adj, raw)


#: Full-panel pattern assignment (frozen universe): SPY/XLB/XLK carry A,
#: XLE its exact mirror, the remaining eight carry B.
FULL_PATTERNS = {
    "SPY": PAT_A, "XLB": PAT_A, "XLK": PAT_A,
    "XLE": tuple(-x for x in PAT_A),
    "XLC": PAT_B, "XLF": PAT_B, "XLI": PAT_B, "XLP": PAT_B, "XLRE": PAT_B,
    "XLU": PAT_B, "XLV": PAT_B, "XLY": PAT_B,
}

#: Full-panel RAW price-level multipliers (control-key fixture): the
#: ascending NOMPRICE order is hand-known at EVERY session (levels grow
#: linearly in the session index; equal multipliers tie, breaking A-Z).
#: XLE is deliberately the most EXPENSIVE share so the control shorts the
#: sector the anchor longs most (the mirror series) — the baskets differ.
RAW_MULT = {"XLB": 1.0, "XLK": 1.0, "XLC": 3.0, "XLF": 5.0, "XLI": 7.0,
            "XLP": 9.0, "XLRE": 11.0, "XLU": 13.0, "XLV": 15.0, "XLY": 17.0,
            "XLE": 100.0}
CONTROL_RANK_ORDER = ["XLB", "XLK", "XLC", "XLF", "XLI", "XLP", "XLRE",
                      "XLU", "XLV", "XLY", "XLE"]


def full_closes() -> dict[str, list[float]]:
    """Deterministic pseudo-returns tiled from the period-4 patterns; closes
    are the cumulative product (no RNG, byte-stable across runs)."""
    out = {}
    for s, pat in FULL_PATTERNS.items():
        closes = [100.0]
        for i in range(1, len(FULL_DATES)):
            closes.append(closes[-1] * (1.0 + pat[i % 4]))
        out[s] = closes
    return out


def full_panel() -> Panel:
    adj = {s: dict(zip(FULL_DATES, closes))
           for s, closes in full_closes().items()}
    raw = {s: {d: float(i + 1) * RAW_MULT[s]
               for i, d in enumerate(FULL_DATES)}
           for s in SECTOR_SYMBOLS}
    return Panel(adj, raw)


def full_presence() -> dict[str, set[str]]:
    return {s: set(FULL_DATES) for s in SECTOR_SYMBOLS}


def mutate_close(panel: Panel, sym: str, index: int, factor: float) -> Panel:
    """A copy of ``panel`` with one adjusted close rescaled (deterministic)."""
    adj = {s: dict(m) for s, m in panel.adjusted_closes.items()}
    adj[sym][FULL_DATES[index]] = adj[sym][FULL_DATES[index]] * factor
    return Panel(adj, panel.raw_closes)


def anchor_decision_json(panel: Panel, t: int) -> str:
    from research.assets.common.contracts import canonical_json
    dec = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, t,
                    full_presence())
    return canonical_json(dec)


# =========================================================================== #
# EVIDENCE 0 -- frozen heads pinned against the frozen control artifacts
# =========================================================================== #
def test_e00_frozen_family_head_matches_control_artifacts():
    """Family id / arm ids / rule names / folds are EXACTLY the frozen
    proposal + selection-freeze + baseline-invariants heads (read-only)."""
    proposal = json.loads(PROPOSAL_PATH.read_text())
    selection = json.loads(SELECTION_PATH.read_text())
    baseline = json.loads(BASELINE_PATH.read_text())
    assert proposal["hypothesis_id"] == "SFV5-A6-H2"
    assert selection["selected_families"][0]["family_id"] == FAMILY_ID
    assert ARM_IDS[ARM_KEY_ANCHOR] == "SFV5-A6-H2-A"
    assert ARM_IDS[ARM_KEY_NEIGHBOUR] == "SFV5-A6-H2-N"
    assert ARM_IDS[ARM_KEY_CONTROL] == "SFV5-A6-H2-C"
    assert ARM_RULE_NAMES[ARM_KEY_ANCHOR] == "COUPLE63-BN-L3S3-42"
    assert ARM_RULE_NAMES[ARM_KEY_NEIGHBOUR] == "COUPLE21-BN-L3S3-42"
    assert ARM_RULE_NAMES[ARM_KEY_CONTROL] == "NOMPRICE42-BN-L3S3"
    assert CFGS[ARM_KEY_ANCHOR].corr_window_sessions == 63
    assert CFGS[ARM_KEY_NEIGHBOUR].corr_window_sessions == 21
    assert CFGS[ARM_KEY_CONTROL].corr_window_sessions is None
    assert [(f.fold_id, f.start, f.end) for f in FOLDS] == [
        (f["fold_id"], f["start"], f["end"]) for f in baseline["folds"]]
    assert (ANCHOR_SESSION, CLOCK_PERIOD_SESSIONS, HOLDING_SESSIONS,
            WARMUP_SESSIONS) == ("2018-04-04", 42, 42, 252)
    assert (BASE_COST_BPS, STRESS_COST_BPS) == (10.0, 20.0)
    assert TURNOVER_CEILING_TWO_WAY_PER_YEAR == 6.0
    assert (GROSS_CAP, HEDGE_ABS_CAP, LEG_WEIGHT, MIN_ELIGIBLE) == \
        (1.25, 0.25, 1.0 / 6.0, 6)
    assert BENCHMARK_SYMBOL not in SECTOR_SYMBOLS
    assert len(SECTOR_SYMBOLS) == 11


def test_e00_arm_config_is_digest_pinned_and_fail_closed():
    """Equal configs share a digest; any frozen-field mutation is refused
    (a reshaped window or a re-rolled control would be a NEW arm)."""
    base = CFGS[ARM_KEY_ANCHOR]
    twin = ArmConfig(arm_key="A", arm_id="SFV5-A6-H2-A", role="anchor",
                     rule_name="COUPLE63-BN-L3S3-42", key_kind="COUPLE",
                     corr_window_sessions=63)
    assert twin.digest == base.digest
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="A", arm_id="SFV5-A6-H2-A", role="anchor",
                  rule_name="COUPLE63-BN-L3S3-42", key_kind="COUPLE",
                  corr_window_sessions=42)          # window is frozen at 63
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="C", arm_id="SFV5-A6-H2-C",
                  role="causal_negative_control", rule_name="NOMPRICE42-BN-L3S3",
                  key_kind="NOMPRICE", corr_window_sessions=21)
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="A", arm_id="SFV5-A6-H2-A", role="neighbour",
                  rule_name="COUPLE63-BN-L3S3-42", key_kind="COUPLE",
                  corr_window_sessions=63)          # role is frozen
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="N", arm_id="SFV5-A6-H2-N", role="neighbour",
                  rule_name="COUPLE21-BN-L3S3-42", key_kind="NOMPRICE",
                  corr_window_sessions=None)        # only C may rank prices
    assert set(build_arm_configs()) == {"A", "N", "C"}
    assert all(len(arm.digest) == 64 for arm in CFGS.values())


def test_e00_master_calendar_fails_closed_on_s1_and_disorder():
    """The S1 guard: a calendar extending past 2025-07-31 is refused
    outright (no session after the S0 screening end can be addressed);
    disordered or empty calendars are refused too."""
    for bad in (FULL_DATES + ["2025-08-03"],
                [FULL_DATES[50], FULL_DATES[10]],
                []):
        with pytest.raises(FamilyError):
            build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], bad)


# =========================================================================== #
# EVIDENCE 1 -- hand-computed feature / target goldens (exact equality)
# =========================================================================== #
def test_e01a_golden_coupling_ranks_hand_computed():
    """Hand fixture (5 dyadic closes -> 4 returns; window = 4):

    r(XLB)=r(XLK)=A=(0,+.5,0,-.5); r(XLF)=r(XLI)=B=(+.5,0,-.5,0);
    r(XLE)=-A; r(XLP)=C=(+1,+.25,+1,+.25); r(SPY)=A.
    Disjoint supports make A.B = 0 exactly; A.C = .5*.25 - .5*.25 = 0;
    B.C = .5*1 - .5*1 = 0; all means are 0 or dyadic so sxy vanishes
    exactly; sxx(A) = 0.5 and corr(A,-A) = -0.5/sqrt(0.25) = -1.0 exactly.
    Coupling scores (mean over the 5 peers, hand):
      XLE: (-1 +0 -1 +0 +0)/5 = -0.4     (strictly lowest)
      XLB=XLK: (0 +1 -1 +0 +0)/5 = 0.0   (identical series: bitwise tie)
      XLP: all five peers orthogonal: 0.0 (bitwise tie with XLB/XLK)
      XLF=XLI: (0 +0 +0 +1 +0)/5 = +0.2  (bitwise tie)
    Ascending with A-Z ties: [XLE, XLB, XLK, XLP, XLF, XLI].
    """
    panel = small_panel()
    scores, counts, ranked = coupling_ranks(
        panel, SMALL_DATES, t=4, corr_window=4, eligible=list(GOLD_SYMS))
    A = [0.0, 0.5, 0.0, -0.5]
    assert pearson(A, A) == 1.0
    assert pearson(A, [-v for v in A]) == -1.0
    assert pearson(A, [0.5, 0.0, -0.5, 0.0]) == 0.0
    assert pearson(A, [1.0, 0.25, 1.0, 0.25]) == 0.0
    assert pearson([0.5, 0.0, -0.5, 0.0], [1.0, 0.25, 1.0, 0.25]) == 0.0
    # every eligible pair was defined: exactly 5 defined pairs per sector
    assert counts == {s: 5 for s in GOLD_SYMS}
    # hand scores, exact
    assert scores["XLE"] == -0.4
    assert scores["XLB"] == scores["XLK"] == scores["XLP"] == 0.0
    assert scores["XLF"] == scores["XLI"] == 0.2
    assert ranked == ["XLE", "XLB", "XLK", "XLP", "XLF", "XLI"]
    # the floor rule: with 5 eligible sectors each has only 4 defined pairs
    # (< 5) so NOTHING is rankable at that decision — recorded, not guessed
    scores2, counts2, ranked2 = coupling_ranks(
        panel, SMALL_DATES, t=4, corr_window=4,
        eligible=["XLB", "XLF", "XLK", "XLE", "XLI"])
    assert counts2 == {s: 4 for s in ("XLB", "XLF", "XLK", "XLE", "XLI")}
    assert scores2 == {} and ranked2 == []


def test_e01b_golden_ols_slope_and_beta_map():
    """Hand OLS slopes: y == x gives exactly 1.0, y == 0.5*x exactly 0.5
    (dyadic scaling is exact in floats), orthogonal patterns exactly 0.0;
    beta_map over the real 252-session window returns the exact slope for a
    sector whose return series IS the benchmark series."""
    xs = [0.0, 1.0, 0.0, -0.5]
    assert ols_slope(xs, xs) == 1.0
    assert ols_slope(xs, [0.5 * v for v in xs]) == 0.5
    assert ols_slope(xs, [0.5, 0.0, -0.5, 0.0]) == 0.0
    assert ols_slope(xs, [0.0, -1.0, 0.0, 0.5]) == -1.0
    closes = full_closes()
    n = len(FULL_DATES)
    spy_rets = return_series([closes["SPY"][i] for i in range(n)])
    rets = {s: return_series([closes[s][i] for i in range(n)])
            for s in ("XLB", "XLE", "XLF")}
    betas = beta_map(spy_rets, rets, DECISION_T, ["XLB", "XLE", "XLF"])
    assert betas["XLB"] == 1.0                    # identical series: exact
    assert betas["XLE"] == pytest.approx(-1.0, abs=1e-9)
    # PAT_B is orthogonal to PAT_A over whole periods; the 251-return beta
    # window carries a 3-session remainder, so the cross slope is O(1/250)
    assert betas["XLF"] == pytest.approx(0.0, abs=0.01)
    with pytest.raises(FamilyError):
        beta_map(spy_rets, rets, DECISION_T, ["XLB", BENCHMARK_SYMBOL])


def test_e01c_golden_targets_hedge_and_truncation():
    """Hand books: sector legs exactly +-1/6; hedge = -sum(w*beta) truncated
    to [-0.25, +0.25]; CASH = 1 - net; gross = 1 + |hedge| <= 1.25."""
    ranked = ["XLE", "XLB", "XLK", "XLP", "XLF", "XLI"]
    # case 1 (in band): longs XLE/XLB/XLK betas -1/+1/+1, shorts betas 0 ->
    # hedge = -[(1/6)(-1+1+1)] = -1/6 exactly; CASH = 1 + 1/6
    betas = {"XLE": -1.0, "XLB": 1.0, "XLK": 1.0, "XLP": 0.0, "XLF": 0.0,
             "XLI": 0.0}
    t = build_targets(ranked, betas)
    assert t["XLE"] == t["XLB"] == t["XLK"] == LEG_WEIGHT
    assert t["XLP"] == t["XLF"] == t["XLI"] == -LEG_WEIGHT
    assert t["SPY"] == pytest.approx(-LEG_WEIGHT, rel=1e-15)
    assert t["CASH"] == pytest.approx(1.0 + LEG_WEIGHT, rel=1e-15)
    # case 2 (truncated below): long betas +1, shorts 0 -> raw hedge -1/2
    # clamps at -0.25 (all-equal betas would cancel: the 3v3 book is
    # dollar-neutral, so beta spread is what the hedge responds to)
    t2 = build_targets(ranked, {s: 1.0 for s in ("XLE", "XLB", "XLK")} |
                       {s: 0.0 for s in ("XLP", "XLF", "XLI")})
    assert t2["SPY"] == -HEDGE_ABS_CAP
    assert sum(abs(v) for k, v in t2.items() if k != CASH_SYMBOL) == \
        pytest.approx(GROSS_CAP, rel=1e-12)
    # case 3 (truncated above): all SHORT betas +1 -> raw hedge +1/3 clamps
    t3 = build_targets(ranked, {s: 0.0 for s in ("XLE", "XLB", "XLK")} |
                       {s: 1.0 for s in ("XLP", "XLF", "XLI")})
    assert t3["SPY"] == HEDGE_ABS_CAP
    # hedge primitive hand cases
    assert hedge_weight({"XLB": LEG_WEIGHT}, {"XLB": 1.5}) == \
        pytest.approx(-HEDGE_ABS_CAP, rel=1e-15)
    assert hedge_weight({"XLB": LEG_WEIGHT}, {"XLB": -1.0}) == LEG_WEIGHT
    assert hedge_weight({}, {}) == 0.0
    # degenerate books are refused: overlap and below the frozen minimum
    with pytest.raises(FamilyError):
        build_targets(["XLB", "XLF", "XLK", "XLK", "XLE", "XLI"], betas)
    with pytest.raises(FamilyError):
        build_targets(["XLB", "XLF", "XLK"], betas)


def test_e01d_golden_full_anchor_decision_payload():
    """Full anchor decision on the tiled panel: XLE (the exact mirror
    series) is the unique lowest-coupling sector; XLB and XLK (identical
    series) tie bitwise; the book carries exactly 6 sector legs at +-1/6,
    the SPY hedge leg, and CASH = 1 - net; gross = 1 + |hedge| <= 1.25."""
    dec = decide_at(CFGS[ARM_KEY_ANCHOR], full_panel(), FULL_DATES,
                    DECISION_T, full_presence())
    assert dec["session"] == FULL_DATES[DECISION_T]
    assert dec["scored"] is True
    assert dec["eligible"] == list(SECTOR_SYMBOLS)
    assert dec["ranked"][0] == "XLE"
    assert dec["coupling_scores"]["XLB"] == dec["coupling_scores"]["XLK"]
    assert dec["defined_pair_counts"] == {s: 10 for s in SECTOR_SYMBOLS}
    targets = dec["targets"]
    legs = [s for s in targets
            if s not in (BENCHMARK_SYMBOL, CASH_SYMBOL)]
    assert len(legs) == 6
    assert all(targets[s] == LEG_WEIGHT for s in legs[:3])
    assert all(targets[s] == -LEG_WEIGHT for s in legs[3:])
    assert abs(sum(targets[s] for s in legs)) < 1e-12      # 3v3 dollar-neutral
    assert abs(targets[CASH_SYMBOL] - (1.0 - targets[BENCHMARK_SYMBOL])) < 1e-9
    assert dec["gross"] == pytest.approx(
        1.0 + abs(targets[BENCHMARK_SYMBOL]), rel=1e-12)
    assert dec["gross"] <= GROSS_CAP + 1e-12


def test_e01e_golden_nomprice_control_decision():
    """Control golden on the tiled panel: the key is the RAW price LEVEL at
    the decision session.  RAW levels grow as (session_index+1) * MULT with
    MULT = {XLB:1, XLK:1, XLC:3, XLF:5, XLI:7, XLP:9, XLRE:11, XLU:13,
    XLV:15, XLY:17, XLE:100}, so the ascending order is hand-known at
    EVERY session (ties break A-Z): [XLB, XLK, XLC, XLF, XLI, XLP, XLRE,
    XLU, XLV, XLY, XLE] -> long XLB/XLK/XLC, short XLV/XLY/XLE — a
    materially different book from the anchor (which LONGS XLE, the exact
    mirror series, as its lowest-coupling leg)."""
    panel = full_panel()
    t = DECISION_T
    dec = decide_at(CFGS[ARM_KEY_CONTROL], panel, FULL_DATES, t,
                    full_presence())
    assert dec["scored"] is True
    levels = dec["nominal_price_levels"]
    assert levels == {s: float(t + 1) * RAW_MULT[s] for s in SECTOR_SYMBOLS}
    assert dec["ranked"] == CONTROL_RANK_ORDER
    tg = dec["targets"]
    assert tg["XLB"] == tg["XLK"] == tg["XLC"] == LEG_WEIGHT
    assert tg["XLV"] == tg["XLY"] == tg["XLE"] == -LEG_WEIGHT
    # the control hedge still comes from ADJUSTED-return betas: XLB/XLK are
    # the benchmark series themselves, so the raw-price key never enters it
    assert dec["betas"]["XLB"] == 1.0 and dec["betas"]["XLK"] == 1.0
    assert -HEDGE_ABS_CAP <= tg["SPY"] <= HEDGE_ABS_CAP
    anchor = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, t,
                       full_presence())
    assert anchor["eligible"] == dec["eligible"]      # same eligibility rule
    assert anchor["ranked"] != dec["ranked"]
    assert anchor["targets"] != dec["targets"]
    # the two keys genuinely disagree about XLE: anchor longs the mirror
    # series (lowest coupling), the control shorts it (highest raw price)
    assert anchor["targets"]["XLE"] == LEG_WEIGHT
    assert dec["targets"]["XLE"] == -LEG_WEIGHT


# =========================================================================== #
# EVIDENCE 2 -- PIT / no-lookahead mutation tests
# =========================================================================== #
def test_e02a_future_rows_cannot_enter_a_decision():
    """A decision at slot t reads only data with timestamp <= the decision
    close: rescaling XLB's adjusted close AFTER t — including at the FILL
    session t+1 and beyond — leaves the decision payload byte-identical."""
    base = anchor_decision_json(full_panel(), DECISION_T)
    for idx in (DECISION_T + 1, DECISION_T + 2, DECISION_T + 40):
        assert anchor_decision_json(
            mutate_close(full_panel(), "XLB", idx, 1.1), DECISION_T) == base


def test_e02b_row_at_the_decision_close_changes_the_decision():
    """The decision close itself IS read: mutating XLB's close at index t
    (inside its 63-session coupling window and 252-session beta window)
    changes the payload; the row one session before the deepest read
    (index t-252, outside every window) cannot."""
    base = anchor_decision_json(full_panel(), DECISION_T)
    assert anchor_decision_json(
        mutate_close(full_panel(), "XLB", DECISION_T, 1.1), DECISION_T) != base
    assert anchor_decision_json(
        mutate_close(full_panel(), "XLB", DECISION_T - WARMUP_SESSIONS, 1.1),
        DECISION_T) == base


def test_e02c_shifted_return_row_moves_the_rank():
    """Shifting XLB's return row one session later (close[i] := close[i-1])
    rewrites its completed-return history: the anchor ranking changes
    accordingly (XLB leaves its bitwise tie with XLK)."""
    panel = full_panel()
    base = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, DECISION_T,
                     full_presence())
    adj = {s: dict(m) for s, m in panel.adjusted_closes.items()}
    xlk = adj["XLB"]
    shifted = [xlk[FULL_DATES[0]]] + [xlk[FULL_DATES[i - 1]]
                                      for i in range(1, len(FULL_DATES))]
    adj["XLB"] = dict(zip(FULL_DATES, shifted))
    after = decide_at(CFGS[ARM_KEY_ANCHOR], Panel(adj, panel.raw_closes),
                      FULL_DATES, DECISION_T, full_presence())
    assert after["scored"] is True and base["scored"] is True
    assert after["ranked"] != base["ranked"]
    assert after["coupling_scores"]["XLB"] != base["coupling_scores"]["XLB"]
    # XLB's shift leaves every pairwise count intact (the mutation moves
    # values, not availability)
    assert after["defined_pair_counts"] == base["defined_pair_counts"]
    # the schedule is calendar-only: close mutations never move a slot
    assert build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], FULL_DATES) \
        .schedule_digest == build_arm_schedule_walk(
            CFGS[ARM_KEY_ANCHOR], FULL_DATES).schedule_digest


def test_e02d_shifted_calendar_session_moves_the_schedule():
    """Removing one master session before the anchor+42 tick moves that tick
    one session earlier — the schedule follows the calendar, never the
    returns, and every slot keeps the next-allowed-session fill."""
    anchor_i = FULL_DATES.index(ANCHOR_SESSION)
    drop = anchor_i + 20                      # a session inside fold 1
    reduced = [d for i, d in enumerate(FULL_DATES) if i != drop]
    s_full = build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], FULL_DATES)
    s_red = build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], reduced)
    assert (s_full.decided[0].session, s_full.decided[1].session) == \
        (ANCHOR_SESSION, FULL_DATES[anchor_i + 42])
    # dropping one session AFTER the anchor but BEFORE tick k=1 pushes that
    # tick one session LATER on the reduced calendar
    assert s_red.decided[1].session == FULL_DATES[anchor_i + 43]
    assert s_full.schedule_digest != s_red.schedule_digest
    for sched, cal in ((s_full, FULL_DATES), (s_red, reduced)):
        for slot in sched.decided:
            assert cal[cal.index(slot.session) + 1] == slot.fill_session


# =========================================================================== #
# EVIDENCE 3 -- next-allowed-session fills; force-flat at fold boundaries
# =========================================================================== #
def test_e03_fills_are_next_allowed_session_never_same_session():
    sched = build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], FULL_DATES)
    assert len(sched.decided) > 0
    for slot in sched.decided:
        i = FULL_DATES.index(slot.session)
        assert slot.fill_session == FULL_DATES[i + 1]
        assert slot.fill_session != slot.session
    flats = {f.session for f in sched.force_flats}
    spans = {f.fold_id: (f.start, f.end) for f in FOLDS}
    for slot in sched.decided:
        start, end = spans[slot.fold_id]
        assert start <= slot.fill_session <= end
        assert slot.fill_session not in flats


def test_e03_force_flat_at_every_fold_end_no_cross_fold_carry():
    sched = build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], FULL_DATES)
    assert [(f.fold_id, f.session) for f in sched.force_flats] == [
        ("S0_FOLD_1", "2020-09-01"), ("S0_FOLD_2", "2023-02-09"),
        ("S0_FOLD_3", "2025-07-24")]
    entries = book_entries_walk(CFGS[ARM_KEY_ANCHOR], full_panel(),
                                FULL_DATES, sched, full_presence())
    for fold in FOLDS:
        flats = [e for e in entries if e["entry_type"] == "FORCE_FLAT"
                 and e["fill_date"] == fold.end]
        assert len(flats) == 1
        # the flat is the LAST book event of its fold: no fill after it
        assert not [e for e in entries if e["entry_type"] == "FILL"
                    and fold.start <= e["fill_date"] <= fold.end
                    and e["fill_date"] > fold.end]


def test_e03_voided_tick_recorded_never_retimed():
    """A 42-grid tick landing in a fold gap is VOIDED and recorded — never
    re-timed to a neighbour session (frozen sample-size discipline)."""
    anchor_i = FULL_DATES.index(ANCHOR_SESSION)
    gap_session = "2020-09-03"                # inside fold gap 1
    gap_i = FULL_DATES.index(gap_session)
    n_drop = gap_i - (anchor_i + CLOCK_PERIOD_SESSIONS)
    assert n_drop > 0
    dropped = set(FULL_DATES[anchor_i + 1: anchor_i + 1 + n_drop])
    reduced = [d for d in FULL_DATES if d not in dropped]
    assert all(f.end in reduced for f in FOLDS)
    sched = build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], reduced)
    voided_sessions = [s.session for s in sched.decisions if s.fold_id is None]
    assert gap_session in voided_sessions
    assert [s.k for s in sched.decisions if s.session == gap_session] == [1]
    assert gap_session not in [s.session for s in sched.decided]
    # exactly one tick carries k=1: the voided slot was consumed, not moved
    assert [s.k for s in sched.decisions].count(1) == 1


# =========================================================================== #
# EVIDENCE 4 -- deterministic double generation (byte-identical)
# =========================================================================== #
def test_e04_schedule_double_generation_byte_identical():
    for key in (ARM_KEY_ANCHOR, ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
        arm = CFGS[key]
        a = build_arm_schedule_walk(arm, FULL_DATES)
        b = build_arm_schedule_blockwise(arm, FULL_DATES)
        assert schedules_equal(a, b)
        assert a.canonical_json() == b.canonical_json()
        assert a.schedule_digest == b.schedule_digest
        assert build_arm_schedule_walk(arm, FULL_DATES).schedule_digest == \
            a.schedule_digest


def test_e04_books_double_generation_byte_identical():
    panel = full_panel()
    for key in (ARM_KEY_ANCHOR, ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
        arm = CFGS[key]
        sched = build_arm_schedule_walk(arm, FULL_DATES)
        a = book_entries_walk(arm, panel, FULL_DATES, sched, full_presence())
        b = book_entries_blockwise(arm, panel, FULL_DATES, sched,
                                   full_presence())
        assert book_digest(a) == book_digest(b)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
        assert book_digest(book_entries_walk(
            arm, panel, FULL_DATES, sched, full_presence())) == book_digest(a)


def test_e04_dry_run_artifact_digest_stability():
    arm = CFGS[ARM_KEY_ANCHOR]
    sched = build_arm_schedule_walk(arm, FULL_DATES)
    entries = book_entries_walk(arm, full_panel(), FULL_DATES, sched,
                                full_presence())
    art1 = dry_run_artifact(arm, sched, entries)
    art2 = dry_run_artifact(arm, sched, entries)
    assert json.dumps(art1, sort_keys=True) == json.dumps(art2, sort_keys=True)
    assert art1["book_digest"] == art2["book_digest"]
    assert art1["schedule_digest"] == sched.schedule_digest
    assert art1["scored"] is False and art1["real_pnl"] is False


# =========================================================================== #
# EVIDENCE 5 -- split/dividend correctness (adjusted _all path ONLY)
# =========================================================================== #
def test_e05_returns_come_from_the_adjusted_series_only():
    """The return builder takes ONE adjusted close series; the raw panel is
    structurally unreachable from the anchor code path: rescaling, adding,
    or deleting the raw panel leaves every anchor decision byte-identical."""
    panel = full_panel()
    base = anchor_decision_json(panel, DECISION_T)
    wild_raw = {s: {d: (v + 1.0) * 1000.0 for d, v in m.items()}
                for s, m in panel.raw_closes.items()}
    assert anchor_decision_json(Panel(panel.adjusted_closes, wild_raw),
                                DECISION_T) == base
    assert anchor_decision_json(Panel(panel.adjusted_closes, None),
                                DECISION_T) == base


def test_e05_adjusted_path_is_continuous_across_a_split_raw_is_not():
    """A 2:1 split: the RAW as-traded close halves; the ADJUSTED close is
    back-adjusted and smooth.  The adjusted close-to-close ratio (the only
    return input) shows no gap; the raw series shows the -50% artifact."""
    dates = ["2030-01-01", "2030-01-02", "2030-01-03", "2030-01-04"]
    adjusted = {d: 100.0 + 2.0 * i for i, d in enumerate(dates)}
    raw = dict(adjusted)
    raw[dates[2]] = raw[dates[2]] / 2.0       # ex-date: raw halves
    raw[dates[3]] = raw[dates[3]] / 2.0
    r_adj = return_series([adjusted[d] for d in dates])
    r_raw = return_series([raw[d] for d in dates])
    assert r_adj[0] is None
    assert all(abs(r - 0.02) < 0.001 for r in r_adj[1:])   # smooth ~2%/day
    assert r_raw[2] == pytest.approx(-0.49019607843137253)  # the split artifact
    # contrast: the adjusted path is smooth where the raw path gaps ~-50%
    assert r_adj[2] - r_raw[2] > 0.4
    # the coupling feature computed on the adjusted path is smooth: sectors
    # sharing the smooth adjusted panel are perfectly co-moving (corr 1.0,
    # 5 defined peers each) — never gapped by the raw split
    panel_adj = Panel({s: dict(adjusted)
                       for s in ("XLB", "XLF", "XLK", "XLE", "XLI", "XLP")},
                      None)
    scores, counts, ranked = coupling_ranks(
        panel_adj, dates, 3, 3, ["XLB", "XLF", "XLK", "XLE", "XLI", "XLP"])
    assert counts == {s: 5 for s in
                      ("XLB", "XLF", "XLK", "XLE", "XLI", "XLP")}
    assert all(v == pytest.approx(1.0) for v in scores.values())
    # all six scores are bitwise 1.0: the tie breaks alphabetically A-Z
    assert ranked == ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP"]


def test_e05_control_key_reads_the_raw_level_and_nothing_else_does():
    """Rescaling each symbol's RAW prices by a distinct per-symbol factor
    reorders the NOMPRICE control while the anchor ranking is untouched."""
    panel = full_panel()
    anchor_rank = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES,
                            DECISION_T, full_presence())["ranked"]
    control_rank = decide_at(CFGS[ARM_KEY_CONTROL], panel, FULL_DATES,
                             DECISION_T, full_presence())["ranked"]
    scaled_raw = {s: {d: v * float(len(panel.raw_closes) - i)
                     for d, v in m.items()}
                  for i, (s, m) in enumerate(panel.raw_closes.items())}
    p2 = Panel(panel.adjusted_closes, scaled_raw)
    assert decide_at(CFGS[ARM_KEY_CONTROL], p2, FULL_DATES, DECISION_T,
                     full_presence())["ranked"] != control_rank
    assert decide_at(CFGS[ARM_KEY_ANCHOR], p2, FULL_DATES, DECISION_T,
                     full_presence())["ranked"] == anchor_rank


# =========================================================================== #
# EVIDENCE 6 -- scale (and location) invariance of the coupling feature
# =========================================================================== #
def test_e06_scale_invariance_exact_ranks_unchanged():
    """Multiplying one symbol's closes (hence its returns) by a positive
    constant leaves its coupling rank untouched — the audit's
    scale-invariance argument that no transformation of price levels can
    move the anchor key.  8.0 and 0.125 are exact dyadic scalings of the
    dyadic hand fixture, so the return patterns are bit-identical and the
    assert is exact equality of the full ordering."""
    base_ranked = ["XLE", "XLB", "XLK", "XLP", "XLF", "XLI"]
    for sym, factor in (("XLE", 8.0), ("XLB", 0.125), ("XLP", 8.0)):
        adj = {s: list(v) for s, v in SMALL_CLOSES.items()}
        adj[sym] = [v * factor for v in adj[sym]]
        panel = Panel({s: dict(zip(SMALL_DATES, v)) for s, v in adj.items()},
                      None)
        _, _, ranked = coupling_ranks(panel, SMALL_DATES, 4, 4,
                                      list(GOLD_SYMS))
        assert ranked == base_ranked


def test_e06_full_panel_scale_invariance_of_decisions():
    """On the tiled panel, scaling XLE's whole price path leaves the anchor
    ranking identical and the six sector legs identical (the hedge is equal
    to within float noise of the rescaled closes)."""
    panel = full_panel()
    base = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, DECISION_T,
                     full_presence())
    adj = {s: dict(m) for s, m in panel.adjusted_closes.items()}
    adj["XLE"] = {d: v * 3.0 for d, v in adj["XLE"].items()}
    scaled = decide_at(CFGS[ARM_KEY_ANCHOR], Panel(adj, None), FULL_DATES,
                       DECISION_T, full_presence())
    assert scaled["ranked"] == base["ranked"]
    legs = [s for s in base["targets"]
            if s not in (BENCHMARK_SYMBOL, CASH_SYMBOL)]
    assert all(scaled["targets"][s] == base["targets"][s] for s in legs)
    assert scaled["targets"]["SPY"] == \
        pytest.approx(base["targets"]["SPY"], abs=1e-9)


def test_e06_location_shift_of_returns_cannot_move_the_correlation():
    """The location-invariance wall (drift is not momentum here): adding a
    constant to one symbol's RETURN series leaves Pearson unchanged, so a
    pure drift cannot reorder the coupling key."""
    r = [0.0, 1.0, 0.0, -0.5]
    drifted = [v + 0.37 for v in r]
    peer = [0.5, 0.0, -0.5, 0.0]
    assert pearson(r, peer) == pytest.approx(pearson(drifted, peer),
                                             rel=1e-12)
    assert pearson(r, r) == pytest.approx(pearson(drifted, drifted), rel=1e-12)


# =========================================================================== #
# EVIDENCE 7 -- the control cannot equal the anchor (identifiability)
# =========================================================================== #
def _spearman(order_a: list[str], order_c: list[str]) -> float:
    common = [s for s in order_a if s in set(order_c)]
    pos_c = {s: i for i, s in enumerate(order_c)}
    xs = [float(i) for i in range(len(common))]
    ys = [float(pos_c[s]) for s in common]
    r = pearson(xs, ys)
    return 0.0 if r is None else r


def test_e07_synthetic_anchor_neighbour_and_control_ranks_differ():
    panel = full_panel()
    presence = full_presence()
    anchor = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, DECISION_T,
                       presence)
    control = decide_at(CFGS[ARM_KEY_CONTROL], panel, FULL_DATES, DECISION_T,
                        presence)
    neighbour = decide_at(CFGS[ARM_KEY_NEIGHBOUR], panel, FULL_DATES,
                          DECISION_T, presence)
    assert anchor["ranked"] != control["ranked"]
    assert anchor["targets"] != control["targets"]
    # the neighbour is the SAME mechanism at a faster window: it agrees on
    # the leader (mechanism support) while its scores are numerically the
    # 21-window estimator, not the 63-window one
    assert neighbour["ranked"][0] == anchor["ranked"][0] == "XLE"
    assert neighbour["coupling_scores"] != anchor["coupling_scores"]
    assert neighbour["scored"] is True


@functools.lru_cache(maxsize=1)
def _real_snapshot():
    """REAL snapshot, clamped to S0: master calendar (SPY sessions <= S0_END),
    per-sector presence (dates), adjusted (_all) and raw (_none) closes.
    NO session after 2025-07-31 is retained — enforced here and again by
    the module's calendar validator."""
    if not STAGING.is_dir():
        pytest.skip("UNAVAILABLE: real snapshot staging not present")
    spy = json.loads((STAGING / "SPY_none_p1.json").read_text())
    dates = sorted(v["datetime"] for v in spy["values"]
                   if v["datetime"] <= S0_END)
    presence: dict[str, list[str]] = {}
    adjusted: dict[str, dict[str, float]] = {}
    raw: dict[str, dict[str, float]] = {}
    for s in SECTOR_SYMBOLS:
        vals = json.loads((STAGING / f"{s}_none_p1.json").read_text())["values"]
        presence[s] = sorted(v["datetime"] for v in vals
                             if v["datetime"] <= S0_END)
        raw[s] = {v["datetime"]: float(v["close"]) for v in vals
                  if v["datetime"] <= S0_END}
        allv = json.loads((STAGING / f"{s}_all_p1.json").read_text())["values"]
        adjusted[s] = {v["datetime"]: float(v["close"]) for v in allv
                       if v["datetime"] <= S0_END}
    spy_all = json.loads((STAGING / "SPY_all_p1.json").read_text())["values"]
    adjusted[BENCHMARK_SYMBOL] = {v["datetime"]: float(v["close"])
                                  for v in spy_all if v["datetime"] <= S0_END}
    assert dates[0] == "2010-01-04" and dates[-1] == S0_END
    return dates, presence, Panel(adjusted, raw)


@functools.lru_cache(maxsize=1)
def _real_identifiability():
    """The preregistered PnL-free A9-F measurement over the 44 real slots:
    anchor coupling-63 ranks vs NOMPRICE raw-level ranks (no betas, no
    targets, no returns aggregated — ranks only)."""
    dates, presence, panel = _real_snapshot()
    a = dates.index(ANCHOR_SESSION)
    rhos: list[float] = []
    long_share: list[bool] = []
    short_share: list[bool] = []
    ranked_pairs: list[tuple[str, tuple, tuple]] = []
    k = 0
    while True:
        i = a + CLOCK_PERIOD_SESSIONS * k
        if i >= len(dates) or dates[i] > FOLDS[-1].end:
            break
        eligible = eligibility(dates, i, presence)
        _, _, ranked_a = coupling_ranks(panel, dates, i, 63, eligible)
        _, ranked_c = nomprice_ranks(panel, dates, i, eligible)
        if len(ranked_a) >= MIN_ELIGIBLE:
            rhos.append(abs(_spearman(ranked_a, ranked_c)))
            long_share.append(len(set(ranked_a[:3]) & set(ranked_c[:3])) >= 2)
            short_share.append(len(set(ranked_a[-3:]) & set(ranked_c[-3:])) >= 2)
        ranked_pairs.append((dates[i], tuple(ranked_a), tuple(ranked_c)))
        k += 1
    return tuple(ranked_pairs), tuple(rhos), tuple(long_share), \
        tuple(short_share)


@pytest.mark.skipif(not STAGING.is_dir(),
                    reason="UNAVAILABLE: real snapshot staging not present")
def test_e07_real_control_cannot_collapse_into_the_anchor():
    """Regression pin on the REAL snapshot (bounds, not exact floats, for
    CI stability): mean |Spearman| ~ 0.28 (A9-F measured 0.2818) — far
    below the 0.60 pre-selection kill threshold and the V4 0.78-0.83
    near-collinearity band; >= 2-leg same-side sharing ~18%/20% — far below
    the 70% kill.  The two rank series differ at EVERY one of the 44 slots."""
    ranked_pairs, rhos, long_share, short_share = _real_identifiability()
    assert len(ranked_pairs) == 44                     # the full 42-grid
    mean_abs = math.fsum(rhos) / len(rhos)
    assert 0.10 <= mean_abs <= 0.45                    # measured ~0.2818
    assert mean_abs < 0.60                             # preregistered kill
    assert mean_abs < 0.78                             # V4 collision band
    ls = math.fsum(long_share) / len(long_share)
    ss = math.fsum(short_share) / len(short_share)
    assert ls < 0.25 and ss < 0.25                     # measured 0.18/0.20
    assert ls < 0.70 and ss < 0.70                     # preregistered kill
    assert all(ra != rc for _, ra, rc in ranked_pairs)
    assert max(rhos) < 1.0


# =========================================================================== #
# EVIDENCE 8 -- cap / gross / net / cash invariants
# =========================================================================== #
def test_e08_book_invariants_on_every_synthetic_decision():
    for t in range(300, 320):
        for key in (ARM_KEY_ANCHOR, ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
            dec = decide_at(CFGS[key], full_panel(), FULL_DATES, t,
                            full_presence())
            targets = dec["targets"]
            legs = {s: w for s, w in targets.items() if s != CASH_SYMBOL}
            sector = {s: w for s, w in legs.items()
                      if s != BENCHMARK_SYMBOL}
            assert len(sector) == 6
            assert all(w in (LEG_WEIGHT, -LEG_WEIGHT)
                       for w in sector.values())
            assert sum(1 for w in sector.values() if w == LEG_WEIGHT) == 3
            assert abs(math.fsum(sector.values())) < 1e-12   # 3v3 neutral
            net = math.fsum(legs.values())
            assert abs(net - targets[BENCHMARK_SYMBOL]) < 1e-12
            assert abs(targets[CASH_SYMBOL] - (1.0 - net)) < 1e-9
            gross = math.fsum(abs(w) for w in legs.values())
            assert gross == pytest.approx(1.0 + abs(net), rel=1e-12)
            assert gross <= GROSS_CAP + 1e-12


def test_e08_book_validator_refuses_corrupted_entries():
    with pytest.raises(FamilyError):                   # does not sum to 1
        validate_book([{"entry_type": "FILL", "fill_date": FULL_DATES[300],
                        "targets": {"XLB": 2.0, "XLE": -0.5, "SPY": 0.1,
                                    CASH_SYMBOL: -0.6}}])
    with pytest.raises(FamilyError):                   # sector legs not neutral
        validate_book([{"entry_type": "FILL", "fill_date": FULL_DATES[300],
                        "targets": {"XLB": 0.7, "XLE": -0.7, "SPY": 0.0,
                                    CASH_SYMBOL: 0.3}}])
    with pytest.raises(FamilyError):                   # gross above the cap
        validate_book([{"entry_type": "FILL", "fill_date": FULL_DATES[300],
                        "targets": {"XLB": 0.9, "XLE": -0.9, "SPY": 0.25,
                                    CASH_SYMBOL: 0.75}}])


def test_e08_every_constructed_book_passes_the_validator():
    for key in (ARM_KEY_ANCHOR, ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
        sched = build_arm_schedule_walk(CFGS[key], FULL_DATES)
        entries = book_entries_walk(CFGS[key], full_panel(), FULL_DATES,
                                    sched, full_presence())
        assert all(e["entry_type"] in ("FILL", "FORCE_FLAT") for e in entries)
        assert len([e for e in entries
                    if e["entry_type"] == "FORCE_FLAT"]) == len(FOLDS)


# =========================================================================== #
# EVIDENCE 9 -- cost-once + ADJ-5 turnover accounting (factory path)
# =========================================================================== #
def test_e09_turnover_convention_non_cash_only_spy_counted():
    before = {"XLB": 0.5, "XLE": 0.25, CASH_SYMBOL: 0.25}
    after = {"XLB": 0.25, "XLE": 0.5, CASH_SYMBOL: 0.25}
    assert etf_leg_turnover(before, after) == pytest.approx(0.5)
    assert etf_leg_turnover(before, after) != pytest.approx(0.75)
    # the SPY hedge leg is a NON-CASH leg: its delta counts (ADJ-5)
    assert etf_leg_turnover({"SPY": 0.25}, {"SPY": -0.25}) == pytest.approx(0.5)
    assert etf_leg_turnover({CASH_SYMBOL: 1.0},
                            {"XLB": LEG_WEIGHT, "XLE": -LEG_WEIGHT,
                             "SPY": 0.25}) == \
        pytest.approx(2 * LEG_WEIGHT + 0.25)


def test_e09_costs_charged_exactly_once_hand_computed():
    """Hand-costed book through the canonical factory path: build (0.25 +
    2/6 one-way), full flip (0.5 + 4/6), and the fold force-flat (0.25 +
    2/6 back to cash) are each charged EXACTLY ONCE; constant prices make
    the dummy synthetic PnL equal minus the cost sum."""
    dates = ["2018-01-02", "2018-01-03", "2018-01-04", "2018-01-05",
             "2018-01-08", "2018-01-09"]
    flat = {s: {d: 100.0 for d in dates} for s in ("XLB", "XLE", "SPY")}
    t1 = {"XLB": LEG_WEIGHT, "XLE": -LEG_WEIGHT, "SPY": 0.25,
          CASH_SYMBOL: 0.75}
    t2 = {"XLB": -LEG_WEIGHT, "XLE": LEG_WEIGHT, "SPY": -0.25,
          CASH_SYMBOL: 0.75}
    entries = [{"entry_type": "FILL", "fill_date": dates[1], "targets": t1},
               {"entry_type": "FILL", "fill_date": dates[3], "targets": t2},
               {"entry_type": "FORCE_FLAT", "fill_date": dates[5]}]
    result = value_book(entries, flat, {}, {}, dates, cost_bps=BASE_COST_BPS)
    turn_build = 2 * LEG_WEIGHT + 0.25                 # build from all-cash
    turn_flip = 4 * LEG_WEIGHT + 0.5                   # full flip
    turn_flat = 2 * LEG_WEIGHT + 0.25                  # flat closes the book
    c1 = fill_cost(1.0, turn_build, BASE_COST_BPS)
    c2 = fill_cost(1.0 - c1, turn_flip, BASE_COST_BPS)
    c3 = fill_cost(1.0 - c1 - c2, turn_flat, BASE_COST_BPS)
    assert len(result.fill_costs) == 3
    assert [fc[1] for fc in result.fill_costs] == \
        pytest.approx([turn_build, turn_flip, turn_flat])
    assert result.total_cost == pytest.approx(c1 + c2 + c3, rel=1e-12)
    assert_reconciles(result)          # attribution identity + no double-add
    # constant prices: the only PnL is the cost drag (dummy synthetic metric)
    assert result.total_pnl == pytest.approx(-(c1 + c2 + c3), rel=1e-9)


def test_e09_stress_cost_doubles_the_first_fill():
    dates = ["2018-01-02", "2018-01-03", "2018-01-04"]
    flat = {s: {d: 100.0 for d in dates} for s in ("XLB", "SPY")}
    entries = [{"entry_type": "FILL", "fill_date": dates[1],
                "targets": {"XLB": LEG_WEIGHT, "SPY": 0.25,
                            CASH_SYMBOL: 0.75}}]
    base = value_book(entries, flat, {}, {}, dates, cost_bps=BASE_COST_BPS)
    stress = value_book(entries, flat, {}, {}, dates,
                        cost_bps=STRESS_COST_BPS)
    assert stress.fill_costs[0][2] == pytest.approx(
        2.0 * base.fill_costs[0][2], rel=1e-12)
    assert stress.total_cost > base.total_cost


def test_e09_family_entries_valuate_clean_through_the_factory():
    """The family's own book entries (explicit CASH leg + FORCE_FLAT rows)
    run through the canonical accounting path on synthetic closes and
    reconcile (dummy synthetic metric only — never run on real data)."""
    anchor_i = FULL_DATES.index(ANCHOR_SESSION)
    dates = FULL_DATES[anchor_i + 1: anchor_i + 1 + 3 * CLOCK_PERIOD_SESSIONS]
    sched = build_arm_schedule_walk(CFGS[ARM_KEY_ANCHOR], FULL_DATES)
    entries = [e for e in book_entries_walk(
        CFGS[ARM_KEY_ANCHOR], full_panel(), FULL_DATES, sched,
        full_presence()) if dates[0] <= e["fill_date"] <= dates[-1]]
    assert len(entries) >= 3, "expected fills inside the valuation window"
    closes = {s: {d: 100.0 + (7.0 if s == "XLB" else 0.0) for d in dates}
              for s in list(SECTOR_SYMBOLS) + ["SPY"]}
    result = value_book(entries, closes, {}, {}, dates, cost_bps=BASE_COST_BPS)
    assert_reconciles(result)


# =========================================================================== #
# EVIDENCE 10 -- schedule-only feasibility on the REAL snapshot
# =========================================================================== #
def test_e10_real_42grid_schedule_feasibility():
    """REAL snapshot, SCHEDULE-ONLY (dates/counts/universe): the 42-session
    global grid yields 44 slots, 15/15/14 per fold, zero voided; every
    structural check green; the WRITTEN eligibility rule gives 10 sectors
    from S0 start and 11 from XLC's 252nd session (the proposal's "9 from
    S0 start" prose is contradicted by its own rule — A9-F reading)."""
    dates, presence, _panel = _real_snapshot()
    arm = CFGS[ARM_KEY_ANCHOR]
    sched = build_arm_schedule_walk(arm, dates)
    assert len(sched.voided) == 0
    assert [len(sched.decisions_in_fold(f.fold_id)) for f in FOLDS] == \
        [15, 15, 14]
    assert len(sched.decided) == 44
    feas = schedule_feasibility(arm, sched, dates, presence)
    assert feas["all_checks_pass"], feas["checks"]
    assert feas["folds"]["S0_FOLD_1"]["eligible_set_sizes"] == \
        [10] * 8 + [11] * 7
    assert feas["folds"]["S0_FOLD_2"]["eligible_set_sizes"] == [11] * 15
    assert feas["folds"]["S0_FOLD_3"]["eligible_set_sizes"] == [11] * 14
    first = sched.decided[0]
    assert (first.k, first.session, first.fill_session) == \
        (0, "2018-04-04", "2018-04-05")
    last = sched.decided[-1]
    assert (last.k, last.session, last.fill_session) == \
        (43, "2025-06-10", "2025-06-11")
    assert sched.decisions_in_fold("S0_FOLD_1")[-1].session == "2020-08-04"
    assert sched.decisions_in_fold("S0_FOLD_2")[0].session == "2020-10-02"
    assert schedules_equal(sched, build_arm_schedule_blockwise(arm, dates))
    # all three arms share the identical decision/fill calendar
    for key in (ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
        other = build_arm_schedule_walk(CFGS[key], dates)
        assert [s.session for s in other.decided] == \
            [s.session for s in sched.decided]
        assert [s.fill_session for s in other.decided] == \
            [s.fill_session for s in sched.decided]


def _real_turnover_estimate() -> dict[str, float]:
    ranked_pairs, _rhos, _ls, _ss = _real_identifiability()
    dates, _presence, _panel = _real_snapshot()
    s0_sessions = len(dates) - dates.index(ANCHOR_SESSION)
    assert s0_sessions == 1842
    churn = membership_churn([list(ra) for _, ra, _rc in ranked_pairs])
    assert len(churn) == 43
    return estimate_turnover(churn, s0_sessions, n_force_flats=len(FOLDS))


@pytest.mark.skipif(not STAGING.is_dir(),
                    reason="UNAVAILABLE: real snapshot staging not present")
def test_e10_real_turnover_estimate_inside_ceiling():
    """Measured-churn turnover arithmetic on the real ranking series
    (weights only, ZERO returns): the mid estimate sits inside the 6.0
    two-way ceiling; the full-reconstitution bound stays reported as the
    declared falsification surface (it exceeds the ceiling BY DESIGN)."""
    est = _real_turnover_estimate()
    assert 0.5 <= est["mean_membership_churn_legs"] <= 3.0   # measured 1.535
    assert est["max_membership_churn_legs"] <= 6
    assert est["mid_two_way_per_year"] < TURNOVER_CEILING_TWO_WAY_PER_YEAR
    assert 1.0 < est["mid_two_way_per_year"] < 5.0           # measured ~3.07
    assert est["upper_two_way_per_year"] > est["mid_two_way_per_year"]
    assert est["full_reconstitution_bound_two_way_per_year"] > \
        TURNOVER_CEILING_TWO_WAY_PER_YEAR


@pytest.mark.skipif(not STAGING.is_dir(),
                    reason="UNAVAILABLE: real snapshot staging not present")
def test_e10_writes_schedule_check_artifact_dates_and_counts_only():
    """Writes research/control/stocks_free_v5_run/i_family_1_schedule_check
    .json — dates, counts, structural checks and weight-only churn
    arithmetic; the payload is scanned to prove it carries no scored
    metric of any kind."""
    dates, presence, _panel = _real_snapshot()
    report = {
        "schema": "stocks_free_v5_run/i_family_1_schedule_check@1",
        "producer_role": "A8",
        "family_id": FAMILY_ID,
        "hypothesis_id": "SFV5-A6-H2",
        "feasibility": "SCHEDULE_ONLY_NO_PNL_NO_REAL_FEATURE_VALUES",
        "arms": {},
        "turnover_estimate_weights_only": _real_turnover_estimate(),
        "identifiability_note": (
            "anchor-vs-NOMPRICE rank divergence measured PnL-free in "
            "test_e07_real_control_cannot_collapse_into_the_anchor; bounds "
            "asserted there, values not republished here"),
    }
    for key in (ARM_KEY_ANCHOR, ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
        arm = CFGS[key]
        sched = build_arm_schedule_walk(arm, dates)
        feas = schedule_feasibility(arm, sched, dates, presence)
        assert feas["all_checks_pass"], feas["checks"]
        report["arms"][arm.arm_id] = {
            "rule_name": arm.rule_name,
            "role": arm.role,
            "config_digest": arm.digest,
            "schedule_digest": sched.schedule_digest,
            "decisions_total": feas["decisions_total"],
            "voided_ticks": feas["voided_ticks"],
            "folds": feas["folds"],
            "force_flats": feas["force_flats"],
            "checks": feas["checks"],
            "all_checks_pass": feas["all_checks_pass"],
        }
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    lowered = payload.lower()
    for banned in ("expectancy", "profit_factor", "total_pnl", "equity",
                   "drawdown", "sharpe", "sortino", "incremental_alpha"):
        assert banned not in lowered, \
            f"schedule check must not carry {banned!r}"
    SCHEDULE_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_CHECK_PATH.write_text(payload, encoding="utf-8")
    assert SCHEDULE_CHECK_PATH.is_file()


# =========================================================================== #
# EVIDENCE 11 -- non-vacuous drop-one design (ETF and fold)
# =========================================================================== #
def test_e11_drop_one_etf_changes_the_book():
    """Drop-one selects the held sector with max |contribution| (canonical
    selector over the sector legs), rebuilds by re-ranking the remaining
    eligible sectors from scratch under the identical rule; membership
    changes and the dropped leg is absent."""
    panel = full_panel()
    presence = full_presence()
    t = DECISION_T
    targets = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, t,
                        presence)["targets"]
    sector_weights = {s: w for s, w in targets.items()
                      if s not in (CASH_SYMBOL, BENCHMARK_SYMBOL)}
    contribution = {s: float(abs(i)) for i, s in
                    enumerate(sorted(sector_weights))}
    contribution["XLB"] = 10.0
    excluded = select_drop_one_symbol(contribution, sector_weights)
    assert excluded == "XLB"
    rebuilt = rebuild_targets_excluding(CFGS[ARM_KEY_ANCHOR], panel,
                                        FULL_DATES, t, presence, excluded)
    assert excluded not in rebuilt
    assert rebuilt != targets
    longs_old = {s for s, w in targets.items() if w > 0
                 and s not in (CASH_SYMBOL, BENCHMARK_SYMBOL)}
    longs_new = {s for s, w in rebuilt.items() if w > 0
                 and s not in (CASH_SYMBOL, BENCHMARK_SYMBOL)}
    assert longs_old != longs_new                      # membership changed
    assert len(longs_new) == 3
    assert len(rebuilt) == len(targets)
    with pytest.raises(FamilyError):                   # unknown sector
        rebuild_targets_excluding(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, t,
                                  presence, "ZZZ")


def test_e11_drop_one_fold_changes_the_book():
    """Rerunning the lane with one fold removed executes and produces a
    materially different schedule and book (no cross-fold carry)."""
    arm = CFGS[ARM_KEY_ANCHOR]
    panel = full_panel()
    sched3 = build_arm_schedule_walk(arm, FULL_DATES)
    sched2 = build_arm_schedule_walk(arm, FULL_DATES, folds=FOLDS[:2])
    assert len(sched3.decided) > len(sched2.decided)
    assert [f.session for f in sched2.force_flats] == \
        ["2020-09-01", "2023-02-09"]
    book3 = book_entries_walk(arm, panel, FULL_DATES, sched3, full_presence())
    book2 = book_entries_walk(arm, panel, FULL_DATES, sched2, full_presence())
    assert book_digest(book3) != book_digest(book2)
    assert len(book3) > len(book2)
    for e in book2:
        assert any(f.start <= e["fill_date"] <= f.end for f in FOLDS[:2])


def test_e11_skipped_decisions_fill_nothing():
    """A decision whose rankable set falls below the frozen 6 is skipped:
    the payload is unscored (no targets) and the book records no fill for
    that slot.  On the real snapshot the skip rule is measure-zero."""
    panel = full_panel()
    tiny_presence = {s: set(FULL_DATES) for s in ("XLB", "XLE", "XLF", "XLK")}
    dec = decide_at(CFGS[ARM_KEY_ANCHOR], panel, FULL_DATES, DECISION_T,
                    tiny_presence)
    assert dec["scored"] is False
    assert "targets" not in dec and "skip_reason" in dec
    # real snapshot first slot: fully scored with 8 non-CASH legs
    dates, real_presence, real_panel = _real_snapshot()
    real_dec = decide_at(CFGS[ARM_KEY_ANCHOR], real_panel, dates,
                         dates.index(ANCHOR_SESSION), real_presence)
    assert real_dec["scored"] is True
    assert len(real_dec["targets"]) == 8               # 6 legs + SPY + CASH


# =========================================================================== #
# EVIDENCE 12 -- dummy publication / refusal / replay (structural digests)
# =========================================================================== #
def test_e12_dummy_publish_replay_refuse_zero_scored_metrics(tmp_path):
    canonical = WORKTREE_ROOT / "research" / "control" / "stocks_free_v4_run" \
        / "event_log.jsonl"
    before = canonical.read_bytes() if canonical.is_file() else None
    arm = CFGS[ARM_KEY_ANCHOR]
    sched = build_arm_schedule_walk(arm, FULL_DATES)
    entries = book_entries_walk(arm, full_panel(), FULL_DATES, sched,
                                full_presence())
    metrics = publication_metrics(entries)
    assert metrics["n_fill_events"] > 0
    assert metrics["n_held_positions"] == 7            # 6 sectors + SPY
    artifact = dry_run_artifact(arm, sched, entries)
    # the artifact carries structure ONLY — allowlisted keys, no metrics
    assert set(artifact) == {
        "schema", "kind", "family_id", "hypothesis_id", "arm_id",
        "rule_name", "role", "config_digest", "schedule_digest",
        "book_digest", "counts", "scored", "real_pnl"}
    ledger = GatedTrialLedger(str(tmp_path / "ledger.json"))
    ledger.compute_recorded("trial.coupling.dry")
    assert ledger.publish_result("trial.coupling.dry", artifact,
                                 n_fill_events=metrics["n_fill_events"],
                                 n_held_positions=metrics["n_held_positions"])
    assert ledger.observed == 1                        # publish adds no increment
    replay = ledger.publish_result("trial.coupling.dry", artifact,
                                   n_fill_events=metrics["n_fill_events"],
                                   n_held_positions=metrics["n_held_positions"])
    assert replay is False and ledger.observed == 1    # replay: zero delta
    # refusal on empty positions: the compute is recorded, never published
    ledger.compute_recorded("trial.coupling.empty")
    refused = ledger.publish_result("trial.coupling.empty", artifact,
                                    n_fill_events=0, n_held_positions=0)
    assert refused is False
    assert ledger.refusals == [{"key": "trial.coupling.empty",
                                "reasons": ["ZERO_FILL_EVENTS",
                                            "ZERO_HELD_POSITIONS"]}]
    assert ledger.observed == 2
    ledger.save()
    saved = json.loads((tmp_path / "ledger.json").read_text())
    assert sorted(saved["published_keys"]) == ["trial.coupling.dry"]
    # the disk carries the artifact as a DIGEST: the stored digest equals the
    # canonical digest of the dry-run artifact (and of any rebuild of it)
    from research.assets.common.contracts import canonical_json
    digest = hashlib.sha256(
        canonical_json(artifact).encode("utf-8")).hexdigest()
    stored = [e for e in saved["entries"] if "artifact_digest" in e]
    assert len(stored) == 1 and stored[0]["key"] == "trial.coupling.dry"
    assert stored[0]["artifact_digest"] == digest
    after = canonical.read_bytes() if canonical.is_file() else None
    assert after == before          # the canonical ledger was never touched


def test_e12_replay_digests_identical_across_reruns(tmp_path):
    """Rebuilding the dry run from scratch and replaying it yields the
    identical structural digests (byte-stable publication surface): the
    replay is refused as zero-delta and the stored artifact digest still
    matches the rebuilt artifact."""
    arm = CFGS[ARM_KEY_ANCHOR]
    runs = []
    for _ in range(2):
        sched = build_arm_schedule_walk(arm, FULL_DATES)
        entries = book_entries_walk(arm, full_panel(), FULL_DATES, sched,
                                    full_presence())
        runs.append(dry_run_artifact(arm, sched, entries))
    assert json.dumps(runs[0], sort_keys=True) == \
        json.dumps(runs[1], sort_keys=True)
    metrics = publication_metrics(book_entries_walk(
        arm, full_panel(), FULL_DATES,
        build_arm_schedule_walk(arm, FULL_DATES), full_presence()))
    ledger = GatedTrialLedger(str(tmp_path / "ledger.json"))
    assert ledger.publish_result("trial.coupling.dry", runs[0],
                                 n_fill_events=metrics["n_fill_events"],
                                 n_held_positions=metrics["n_held_positions"])
    assert ledger.publish_result(
        "trial.coupling.dry", runs[1],
        n_fill_events=metrics["n_fill_events"],
        n_held_positions=metrics["n_held_positions"]) is False
    ledger.save()
    saved = json.loads((tmp_path / "ledger.json").read_text())
    from research.assets.common.contracts import canonical_json
    digest = hashlib.sha256(
        canonical_json(runs[0]).encode("utf-8")).hexdigest()
    stored = [e for e in saved["entries"] if "artifact_digest" in e]
    assert len(stored) == 1                          # replay added no artifact
    assert stored[0]["artifact_digest"] == digest
