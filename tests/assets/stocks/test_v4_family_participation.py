"""V4-I A8 -- family SFV4-A5-H1-PARTICIPATION-SHIFT: 12 evidence items.

Plan section 9 evidence for the participation-shift family lane.  The family
module implements the frozen proposal
``research/control/stocks_free_v4_run/proposals/a5_h1.json`` exactly:
63-session decision clock anchored byte-exact to the S0 start 2018-04-04
(selection-freeze A9-F pin), long top-3 / short bottom-3 of the 11 sector ETFs
by the 21d-vs-252d dollar-volume shock ratio, +/-1/6 legs, gross 1.0 net 0.0,
63-session holding, next-allowed-session fills, force-flat at fold boundaries.

The twelve items (plan section 9):

1.  Hand-computed feature/target golden.
2.  PIT / completed-session + no-lookahead mutation tests.
3.  Next-allowed-session fill (never same session).
4.  Deterministic double generation (byte-identical).
5.  Split/dividend/raw/TR correctness of the DV feature path.
6.  EW sector factor, frozen 0.5 risk-match scale, price-scale invariance.
7.  Control cannot accidentally equal the anchor.
8.  Gross/net/cash invariants (CASH excluded from turnover).
9.  Cost-once and the frozen turnover convention.
10. Schedule-only feasibility on the REAL snapshot (dates/counts/universe
    ONLY -- no returns, no PnL, no real feature values).
11. Meaningful held-max-|contribution| drop-one.
12. Dummy publication/refusal/replay on a TEMP ledger; canonical ledger
    untouched.

HARD RULE honored throughout: real-data runs are SCHEDULE-ONLY.  No scored
PnL, no backtest of returns on real data, no real-data feature values; the
only helpers that touch returns (ew_sector_factor, risk_matched_context,
value_book) run exclusively on synthetic fixtures.

Run:  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \\
      tests/assets/stocks/test_v4_family_participation.py -q
"""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.assets.stocks.factory import (
    CASH_SYMBOL,
    GatedTrialLedger,
    assert_reconciles,
    etf_leg_turnover,
    publication_metrics,
    select_drop_one_symbol,
    value_book,
)
from research.stocks_free_v4.family_participation import (
    ANCHOR_SESSION,
    ARM_KEY_ANCHOR,
    ARM_KEY_CONTROL,
    ARM_KEY_NEIGHBOUR,
    FOLDS,
    SHOCK_WINDOWS,
    ArmConfigError,
    build_arm_configs,
    build_arm_schedule_blockwise,
    build_arm_schedule_walk,
    build_targets,
    cross_sectional_shocks,
    decide_at,
    dollar_volume,
    eligibility,
    ew_sector_factor,
    rank_by_shock_desc,
    rebuild_targets_excluding,
    risk_matched_context,
    schedule_feasibility,
    schedules_equal,
    shock_ratio,
)
from research.stocks_free_v4.family_participation.config import (
    BENCHMARK_SOURCE,
    DV_SOURCE,
    RETURN_SOURCE,
    ArmConfig,
    Fold,
    ShockWindows,
)
from research.stocks_free_v4.family_participation.features import (
    FeatureError,
    align_to_master,
    mean_window,
)

STAGING = Path(
    "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
)
SCHEDULE_CHECK_PATH = (
    Path(__file__).resolve().parents[3]
    / "research" / "control" / "stocks_free_v4_run" / "i_family_1_schedule_check.json"
)
CANONICAL_EVENT_LOG = (
    Path(__file__).resolve().parents[3]
    / "research" / "control" / "stocks_free_v4_run" / "event_log.jsonl"
)

CFG = build_arm_configs()
SYNTH_SYMBOLS = ("SA", "SB", "SC", "SD", "SE", "SF", "SG", "SH")
LEG = 1.0 / 6.0
T = 399   # decision index used by the golden fixtures (n=400 sessions)
N = 400


# --------------------------------------------------------------------------- #
# synthetic fixture helpers
# --------------------------------------------------------------------------- #
def business_dates(n: int, start: date = date(2017, 1, 2)) -> list[str]:
    """n consecutive NYSE-like weekday sessions as ISO strings."""
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def raw_rows(dates: list[str], close: dict[str, float],
             volume: dict[str, float],
             symbols: tuple[str, ...] = SYNTH_SYMBOLS) -> dict[str, list[dict]]:
    """``_none``-style raw rows per symbol (close/volume constant per session)."""
    return {
        s: [{"datetime": d, "close": str(close[s]), "volume": str(volume[s])}
            for d in dates]
        for s in symbols
    }


def make_aligned(dates: list[str],
                 base_dv: float = 100_000.0,
                 overrides: dict[str, list[tuple[float, int, int]]] | None = None,
                 symbols: tuple[str, ...] = SYNTH_SYMBOLS) -> dict[str, list]:
    """Aligned DV series: constant ``base_dv``; overrides scale closed index
    ranges ``[lo, hi]`` by a multiplier (inclusive indices)."""
    n = len(dates)
    aligned: dict[str, list] = {}
    for s in symbols:
        series = [base_dv] * n
        for mult, lo, hi in (overrides or {}).get(s, []):
            for i in range(lo, hi + 1):
                series[i] = base_dv * mult
        aligned[s] = series
    return aligned


def full_presence(dates: list[str],
                  symbols: tuple[str, ...] = SYNTH_SYMBOLS) -> dict[str, set[str]]:
    return {s: set(dates) for s in symbols}


# =========================================================================== #
# supporting: frozen config head (feeds evidence item 4 / pinning)
# =========================================================================== #
def test_e00_frozen_config_head():
    """Arm ids/roles/windows are exactly the frozen proposal heads; the
    6-legs-x-1/6 book form and the fold table match the frozen contract."""
    assert set(c.arm_id for c in CFG.values()) == \
        {"SFV4-A5-H1-A", "SFV4-A5-H1-N", "SFV4-A5-H1-C"}
    assert CFG[ARM_KEY_ANCHOR].role == "anchor"
    assert CFG[ARM_KEY_NEIGHBOUR].role == "neighbour"
    assert CFG[ARM_KEY_CONTROL].role == "causal_negative_control"
    assert [(f.fold_id, f.start, f.end) for f in FOLDS] == [
        ("S0_FOLD_1", "2018-04-04", "2020-09-01"),
        ("S0_FOLD_2", "2020-09-10", "2023-02-09"),
        ("S0_FOLD_3", "2023-02-17", "2025-07-24"),
    ]
    assert ANCHOR_SESSION == "2018-04-04"
    # a reshaped window is a different family and must be rejected
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="A", arm_id="SFV4-A5-H1-A", role="anchor",
                  windows=ShockWindows(10, 0, 251, 11))
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="A", arm_id="SFV4-A5-H1-X", role="anchor",
                  windows=SHOCK_WINDOWS["A"])
    with pytest.raises(ArmConfigError):
        ArmConfig(arm_key="A", arm_id="SFV4-A5-H1-A", role="anchor",
                  windows=SHOCK_WINDOWS["A"],
                  symbols=("XLB", "SPY"))  # benchmark must never be a leg


# =========================================================================== #
# EVIDENCE 1 -- hand-computed feature and target golden
# =========================================================================== #
def test_e01_golden_feature_and_targets_hand_computed():
    """Hand fixture (n=400 sessions, 8 symbols, base DV 100,000 everywhere).

    Shock(A) = mean(DV, t-20..t) / mean(DV, t-251..t-21).

    Case 1 -- constant DV: every numerator mean = 100000 (fsum of 21 equal
    representable values / 21 is exact) and every denominator mean = 100000
    (231 values) => every shock == 1.0 EXACTLY.  All eight sectors tie at
    1.0; the frozen tie-break is ticker alphabetical ascending, so

        ranked = [SA, SB, SC, SD, SE, SF, SG, SH]
        longs  = SA, SB, SC   at +1/6
        shorts = SF, SG, SH   at -1/6
        net    = fsum(3x(+1/6) + 3x(-1/6)) = 0.0 exactly (fsum is exact)
        CASH   = 1 - net = 1.0

    Case 2 -- SG x2 and SA x0.5 on the last 21 sessions (indices 379..399):
        SG: num = fsum(21 x 200000)/21 = 200000, den = 100000 => 2.0
        SA: num = fsum(21 x 50000)/21  =  50000, den = 100000 => 0.5
        all others 1.0.  Ranked descending with alphabetical ties (0.5 < 1.0,
        so SA is LAST, below the six 1.0 ties):
            [SG, SB, SC, SD, SE, SF, SH, SA]
        longs = SG, SB, SC ; shorts = SF, SH, SA.

    Neighbour cross-check (63-session numerator, same fixture): SG num spans
    t-62..t = 337..399 => 42 sessions at 100000 + 21 at 200000 =>
    mean = 8400000/63, den = 100000 => shock = 4/3 (NOT 2.0) -- window
    membership is the ONLY difference between the arms.
    """
    dates = business_dates(N)
    aligned = make_aligned(dates)  # constant 100_000 everywhere
    shocks = cross_sectional_shocks(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                                    list(SYNTH_SYMBOLS))
    assert shocks == {s: 1.0 for s in SYNTH_SYMBOLS}  # exact hand values
    ranked = rank_by_shock_desc(shocks)
    assert ranked == ["SA", "SB", "SC", "SD", "SE", "SF", "SG", "SH"]
    targets = build_targets(ranked)
    assert targets == {
        "SA": LEG, "SB": LEG, "SC": LEG,
        "SF": -LEG, "SG": -LEG, "SH": -LEG,
        CASH_SYMBOL: 1.0,
    }  # exact, including the CASH residual

    # Case 2: perturb the 21-session numerator windows of SG (x2) and SA (x0.5)
    aligned2 = make_aligned(dates, overrides={
        "SG": [(2.0, T - 20, T)],
        "SA": [(0.5, T - 20, T)],
    })
    d2 = decide_at(aligned2, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR], list(SYNTH_SYMBOLS))
    assert d2["shocks"]["SG"] == 2.0
    assert d2["shocks"]["SA"] == 0.5
    assert d2["shocks"]["SB"] == 1.0
    assert d2["ranked"] == ["SG", "SB", "SC", "SD", "SE", "SF", "SH", "SA"]
    assert d2["targets"] == {
        "SG": LEG, "SB": LEG, "SC": LEG,
        "SF": -LEG, "SH": -LEG, "SA": -LEG,
        CASH_SYMBOL: 1.0,
    }

    # neighbour arm reads a 63-session numerator: hand value 4/3 for SG
    n_shock = shock_ratio(aligned2["SG"], T, SHOCK_WINDOWS[ARM_KEY_NEIGHBOUR])
    assert n_shock == pytest.approx(4.0 / 3.0, rel=1e-15)


# =========================================================================== #
# EVIDENCE 2 -- PIT / completed-session and no-lookahead mutations
# =========================================================================== #
def test_e02_pit_no_lookahead_mutations():
    """Mutating any session AFTER the decision, or any session outside the
    252-session lookback, must leave the decision identical; the truncated-
    series computation must equal the full-series one; windows that would
    read the future or pre-warmup history fail closed."""
    dates = business_dates(N + 10)  # future sessions exist and must not matter
    aligned = make_aligned(dates, overrides={
        "SG": [(2.0, T - 20, T)],
        "SA": [(0.5, T - 20, T)],
    })
    base = decide_at(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR], list(SYNTH_SYMBOLS))

    # (a) mutate FUTURE sessions' volume/close proxies (DV levels) at t+1, t+5
    mutated = {s: list(v) for s, v in aligned.items()}
    mutated["SG"][T + 1] = 1e12
    mutated["SA"][T + 5] = 1e-12
    after = decide_at(mutated, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR], list(SYNTH_SYMBOLS))
    assert after["shocks"] == base["shocks"]
    assert after["ranked"] == base["ranked"]
    assert after["targets"] == base["targets"]

    # (b) mutate a session OUTSIDE the 252-session lookback (t-260)
    mutated2 = {s: list(v) for s, v in aligned.items()}
    mutated2["SC"][T - 260] = 7.0
    after2 = decide_at(mutated2, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR], list(SYNTH_SYMBOLS))
    assert after2["targets"] == base["targets"]

    # (c) PIT truncation equivalence: a series truncated at the decision
    # session (only timestamps <= t) gives the identical decision
    truncated = {s: v[:T + 1] for s, v in aligned.items()}
    after3 = decide_at(truncated, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR], list(SYNTH_SYMBOLS))
    assert after3["shocks"] == base["shocks"]
    assert after3["targets"] == base["targets"]

    # (d) fail-closed: pre-warmup decision (lookback 252 > t+1 sessions)
    with pytest.raises(FeatureError):
        shock_ratio(aligned["SG"], 100, SHOCK_WINDOWS[ARM_KEY_ANCHOR])

    # (e) fail-closed: a window spec whose end reaches past t is rejected
    with pytest.raises(FeatureError):
        mean_window(aligned["SG"], T, 20, -1)

    # (f) missing data inside the warmup window (None) fails closed
    with_missing = {s: list(v) for s, v in aligned.items()}
    with_missing["SG"][T - 100] = None
    with pytest.raises(FeatureError):
        shock_ratio(with_missing["SG"], T, SHOCK_WINDOWS[ARM_KEY_ANCHOR])


# =========================================================================== #
# EVIDENCE 3 -- next-allowed-session fill
# =========================================================================== #
def test_e03_next_allowed_session_fill():
    """Decision at t fills at t+1 ON THE CALENDAR (next listed session),
    never the same session -- including across a multi-day calendar gap."""
    arm = CFG[ARM_KEY_ANCHOR]

    # gapped calendar: all calendar days from 2017-01-01 with a 5-day hole
    # placed immediately after the k=0 decision (2018-04-04), so that
    # decision's fill must JUMP the hole; the frozen fold table is replaced
    # by one synthetic fold spanning the calendar (mechanics test only; the
    # frozen fold table itself is pinned in test_e00/test_e10).
    all_days = [(date(2017, 1, 1) + timedelta(days=i)).isoformat()
                for i in range(600)]
    gap = {f"2018-04-{d:02d}" for d in range(5, 10)}
    dates = [d for d in all_days if d not in gap]
    syn_folds = (Fold("SYN_F1", dates[0], dates[-1]),)
    sched = build_arm_schedule_walk(arm, dates, folds=syn_folds)
    decided = sched.decided
    assert decided, "gapped calendar must still produce decisions"
    assert len(sched.voided) == 0
    for s in decided:
        assert s.fill_session == dates[s.index + 1]      # next ALLOWED session
        assert s.fill_session != s.session               # never the same session
        assert s.fill_session > s.session                # strictly later (ISO)
        assert s.index + 1 == dates.index(s.fill_session)  # lag = 1 position
    # the k=0 decision (2018-04-04) fills across the hole
    assert decided[0].session == "2018-04-04"
    assert decided[0].fill_session == "2018-04-10"
    assert (date.fromisoformat(decided[0].fill_session)
            - date.fromisoformat(decided[0].session)).days > 1
    # and no decision fill ever lands inside the hole
    assert all(s.fill_session not in gap for s in decided)


# =========================================================================== #
# EVIDENCE 4 -- deterministic double generation (byte-identical)
# =========================================================================== #
def test_e04_deterministic_double_generation():
    """Building every arm's schedule twice, through two independent paths,
    gives byte-identical canonical JSON; config digests are stable."""
    dates = business_dates(2200)  # spans beyond the synthetic fold windows
    syn_folds = (Fold("SYN_F1", dates[0], dates[1500]),
                 Fold("SYN_F2", dates[1501], dates[-1]))
    for _key, arm in CFG.items():
        s1 = build_arm_schedule_walk(arm, dates, folds=syn_folds)
        s2 = build_arm_schedule_walk(arm, dates, folds=syn_folds)
        s3 = build_arm_schedule_blockwise(arm, dates, folds=syn_folds)
        assert s1.canonical_json() == s2.canonical_json()   # byte-identical
        assert s1.canonical_json() == s3.canonical_json()   # path-independent
        assert schedules_equal(s1, s3)
        assert s1.schedule_digest == s2.schedule_digest == s3.schedule_digest
        reparsed = json.loads(s1.canonical_json())
        assert reparsed["counts"]["decisions"] == len(s1.decided)
    assert build_arm_configs()[ARM_KEY_ANCHOR].digest == CFG[ARM_KEY_ANCHOR].digest


# =========================================================================== #
# EVIDENCE 5 -- split/dividend/raw/TR correctness of the DV path
# =========================================================================== #
def test_e05_split_dividend_raw_tr_correctness():
    """DV = RAW close x RAW volume from the SAME (_none) series.

    A 2:1 split halves the raw close and doubles the raw volume on the
    effective date, so the raw PAIR (and therefore the 21d-vs-252d shock
    ratio) is unchanged.  The forbidden pairing -- adjusted (_all) close
    times raw volume -- double-counts the back-adjustment and jumps the
    feature by the split factor.  Hand values in-line.
    """
    dates = business_dates(N)
    split_at = T - 19  # effective date inside the 21-session numerator window

    # raw pair WITH the split: close 100->50, volume 1000->2000 => DV 100000
    close = {s: 100.0 for s in SYNTH_SYMBOLS}
    volume = {s: 1000.0 for s in SYNTH_SYMBOLS}
    rows = raw_rows(dates, close, volume)
    for row in rows["SA"]:
        if row["datetime"] >= dates[split_at]:
            row["close"], row["volume"] = "50", "2000"
    dv_split = dollar_volume(rows["SA"])
    assert all(v == 100_000.0 for v in dv_split.values())  # pair is continuous

    aligned_split = {s: align_to_master(dates, dollar_volume(rows[s]))
                     for s in SYNTH_SYMBOLS}
    dec_split = decide_at(aligned_split, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                          list(SYNTH_SYMBOLS))
    assert dec_split["shocks"] == {s: 1.0 for s in SYNTH_SYMBOLS}

    # no-split counterfactual: identical decision (the split does not distort)
    rows_nosplit = raw_rows(dates, close, volume)
    aligned_nosplit = {s: align_to_master(dates, dollar_volume(rows_nosplit[s]))
                       for s in SYNTH_SYMBOLS}
    dec_nosplit = decide_at(aligned_nosplit, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                            list(SYNTH_SYMBOLS))
    assert dec_split["targets"] == dec_nosplit["targets"]
    assert dec_split["ranked"] == dec_nosplit["ranked"]

    # the WRONG pairing (adjusted close x raw volume), computed here only to
    # demonstrate the hazard the module avoids: the adjusted close is flat 50
    # across the split (backward adjustment) while raw volume is 1000 before /
    # 2000 after => DV jumps 50000 -> 100000 at the effective date.
    # num = (50000 + 20x100000)/21 = 2050000/21 ; den = 50000 => 41/21 ~ 1.952
    wrong_dv = [50.0 * (1000.0 if i < split_at else 2000.0) for i in range(N)]
    wrong_shock = shock_ratio(wrong_dv, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR])
    assert wrong_shock == pytest.approx(41.0 / 21.0, rel=1e-12)
    assert dec_split["shocks"]["SA"] == 1.0 != wrong_shock

    # series choice is pinned in the frozen config payload (documentation)
    assert "_none_p1.json" in DV_SOURCE and "close_s(u) * volume_s(u)" in DV_SOURCE
    assert "NOT used" in DV_SOURCE
    assert "_all_p1.json" in RETURN_SOURCE and "adjusted" in RETURN_SOURCE
    assert "SPY_all_p1.json" in BENCHMARK_SOURCE

    # dividend-only events never touch the raw pair: the _none close/volume
    # are as-traded, so the DV path is dividend-invariant by construction
    # (total returns use the _all adjusted close, a separate frozen path)
    assert dv_split[dates[T]] == dv_split[dates[T - 1]]


# =========================================================================== #
# EVIDENCE 6 -- factor calculation and scale invariance
# =========================================================================== #
def test_e06_factor_and_scale_invariance():
    """EW sector factor and the frozen 0.5 SPY risk-match scale on synthetic
    data; scaling every price (or every volume) by 10x leaves shocks, ranks
    and target books invariant."""
    # hand-computed EW factor: returns {SA:+0.02, SB:-0.01, rest 0} -> mean
    rets = {s: {} for s in SYNTH_SYMBOLS}
    rets["SA"]["2024-01-02"] = 0.02
    rets["SB"]["2024-01-02"] = -0.01
    for s in SYNTH_SYMBOLS[2:]:
        rets[s]["2024-01-02"] = 0.0
    assert ew_sector_factor(rets, "2024-01-02", symbols=SYNTH_SYMBOLS) == \
        (0.02 - 0.01 + 0.0 * 6) / 8

    # frozen risk-match scale: 0.5 x SPY return, ex ante
    assert risk_matched_context(0.01) == 0.005
    assert risk_matched_context(-0.02) == pytest.approx(-0.010)

    # scale invariance of the decision
    dates = business_dates(N)
    base_rows = raw_rows(dates, {s: 100.0 for s in SYNTH_SYMBOLS},
                         {s: 1000.0 for s in SYNTH_SYMBOLS})
    for row in base_rows["SG"]:                    # make SG the top shock
        if row["datetime"] >= dates[T - 20]:
            row["volume"] = "2000"

    def decide(rows_map):
        aligned = {s: align_to_master(dates, dollar_volume(rows_map[s]))
                   for s in SYNTH_SYMBOLS}
        return decide_at(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                         list(SYNTH_SYMBOLS))

    base = decide(base_rows)
    x10_prices = {s: [dict(r, close=str(float(r["close"]) * 10)) for r in rows]
                  for s, rows in base_rows.items()}
    x10_volumes = {s: [dict(r, volume=str(float(r["volume"]) * 10)) for r in rows]
                   for s, rows in base_rows.items()}

    for scaled in (x10_prices, x10_volumes):
        dec = decide(scaled)
        assert dec["ranked"] == base["ranked"]          # identical decisions
        assert dec["targets"] == base["targets"]        # identical books
        for s in SYNTH_SYMBOLS:
            assert dec["shocks"][s] == pytest.approx(base["shocks"][s], rel=1e-9)


# =========================================================================== #
# EVIDENCE 7 -- control cannot accidentally equal the anchor
# =========================================================================== #
def test_e07_control_differs_from_anchor():
    """The one-quarter-stale control must produce different shocks/ranks/
    targets than the anchor on synthetic data, and different decision records
    on the real schedule dates (schedule-only: no real feature values)."""
    dates = business_dates(N)
    # SE spikes ONLY in the control's numerator window t-83..t-63 and is flat
    # over the anchor's numerator t-20..t:
    aligned = make_aligned(dates, overrides={"SE": [(10.0, T - 83, T - 63)]})

    anchor = decide_at(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                       list(SYNTH_SYMBOLS))
    control = decide_at(aligned, T, SHOCK_WINDOWS[ARM_KEY_CONTROL],
                        list(SYNTH_SYMBOLS))
    # anchor numerator (t-20..t) is flat 1x, but its denominator
    # (t-251..t-21 = 148..378) CONTAINS the 21 spiked sessions (316..336):
    #   den = (210x100000 + 21x1000000)/231 = 100000 x 420/231
    #   shock = 231/420 = 0.55 (hand value; float-approx)
    assert anchor["shocks"]["SE"] == pytest.approx(0.55, abs=1e-12)
    # control windows t-83..t-63 (spiked) over t-251..t-84 (all 1x, the spike
    # window is OUTSIDE the control denominator) => shock 10.0 exact
    assert control["shocks"]["SE"] == 10.0
    assert control["shocks"]["SD"] == 1.0 and anchor["shocks"]["SD"] == 1.0
    assert anchor["ranked"] != control["ranked"]
    assert anchor["targets"] != control["targets"]
    assert anchor["targets"][CASH_SYMBOL] == control["targets"][CASH_SYMBOL] == 1.0
    # the control structurally cannot see the most recent 63 sessions
    w = SHOCK_WINDOWS[ARM_KEY_CONTROL].to_payload()
    assert w["numerator"]["end_back"] == 63 and w["denominator"]["end_back"] == 84

    # real schedule dates: same anchored clock (identical decision DATE list
    # by construction) but different arm records -- the arms differ in window
    # membership, role, and config digest, never in the clock.
    dates_real = business_dates(2200)
    syn_folds = (Fold("SYN_F1", dates_real[0], dates_real[1500]),
                 Fold("SYN_F2", dates_real[1501], dates_real[-1]))
    a = build_arm_schedule_walk(CFG[ARM_KEY_ANCHOR], dates_real, folds=syn_folds)
    c = build_arm_schedule_walk(CFG[ARM_KEY_CONTROL], dates_real, folds=syn_folds)
    n = build_arm_schedule_walk(CFG[ARM_KEY_NEIGHBOUR], dates_real, folds=syn_folds)
    assert [d.session for d in a.decided] == [d.session for d in c.decided]
    assert [d.session for d in a.decided] == [d.session for d in n.decided]
    assert a.canonical_json() != c.canonical_json()
    assert a.canonical_json() != n.canonical_json()
    assert c.config_digest != a.config_digest
    wa = SHOCK_WINDOWS[ARM_KEY_ANCHOR].to_payload()
    assert wa["numerator"] == {"start_back": 20, "end_back": 0, "sessions": 21}
    assert w["numerator"] == {"start_back": 83, "end_back": 63, "sessions": 21}
    # NOTE (schedule-only interpretation): on the real snapshot the rank/
    # target comparison is proven on synthetic data only; the real-data
    # difference evidence is the differing decision RECORDS above (window
    # membership, role, digest) -- computing real-data feature values is out
    # of scope for this lane by the schedule-only hard rule.


# =========================================================================== #
# EVIDENCE 8 -- cap/gross/net/cash invariants
# =========================================================================== #
def test_e08_gross_net_cash_invariants():
    """After every synthetic decision book: exactly 6 non-CASH legs, 3 long
    and 3 short, gross <= 1.0+eps (= 6 legs x 1/6), net ~ 0, CASH absorbs the
    residual and is EXCLUDED from turnover; force-flat carries no positions."""
    dates = business_dates(N)
    cases = [
        make_aligned(dates),
        make_aligned(dates, overrides={"SG": [(2.0, T - 20, T)],
                                       "SA": [(0.5, T - 20, T)]}),
        make_aligned(dates, overrides={"SE": [(10.0, T - 83, T - 63)],
                                       "SB": [(3.0, T - 20, T)]}),
    ]
    books = []
    for aligned in cases:
        for key in (ARM_KEY_ANCHOR, ARM_KEY_NEIGHBOUR, ARM_KEY_CONTROL):
            dec = decide_at(aligned, T, SHOCK_WINDOWS[key], list(SYNTH_SYMBOLS))
            books.append((key, dec["targets"]))

    assert len(books) == 9
    for _key, targets in books:
        legs = {s: w for s, w in targets.items() if s != CASH_SYMBOL}
        assert len(legs) == 6
        assert sum(1 for w in legs.values() if w > 0) == 3
        assert sum(1 for w in legs.values() if w < 0) == 3
        gross = math.fsum(abs(w) for w in legs.values())
        assert gross <= 1.0 + 1e-9                    # per-proposal gross cap
        assert gross == pytest.approx(1.0, abs=1e-9)  # = 6 x 1/6
        net = math.fsum(w for s, w in targets.items() if s != CASH_SYMBOL)
        assert abs(net) <= 1e-12                      # dollar-neutral legs
        # CASH absorbs the residual so the whole book reconciles to equity 1.0
        assert abs(targets[CASH_SYMBOL] - (1.0 - net)) <= 1e-15
        assert math.fsum(targets.values()) == pytest.approx(1.0, abs=1e-12)
        assert abs(targets[CASH_SYMBOL] - 1.0) <= 1e-12

    # CASH is never a symbol and never in turnover: the frozen turnover of a
    # full sign flip is hand 6 x 2 x (1/6) = 2.0, and changing ONLY the CASH
    # leg leaves it unchanged.
    b1 = books[0][1]
    b2 = {s: -w for s, w in b1.items() if s != CASH_SYMBOL}
    b2[CASH_SYMBOL] = b1[CASH_SYMBOL]
    flip = etf_leg_turnover(b1, b2)
    assert flip == pytest.approx(2.0, abs=1e-12)
    b2_cash_moved = dict(b2, **{CASH_SYMBOL: 0.5})
    assert etf_leg_turnover(b1, b2_cash_moved) == flip  # CASH delta invisible
    assert CASH_SYMBOL not in CFG[ARM_KEY_ANCHOR].symbols


# =========================================================================== #
# EVIDENCE 9 -- cost-once and turnover convention
# =========================================================================== #
def test_e09_cost_once_and_turnover_convention():
    """Canonical accounting on a hand fixture: 10 bps/side charged EXACTLY
    once per fill; turnover == hand sum(|delta_weight|) over non-CASH legs.

    Sessions D1..D3, constant closes (zero drift).  Fill D1 is the initial
    build of the full 6-leg family book (gross 1.0); fill D2 flips every leg.

    Hand arithmetic (nominal decimals):
      D1 turnover = 6 x 1/6 = 1.0  =>  cost = 1.0 x 1.0 x 10 bps = 0.001
      D2 turnover = 6 x 2/6 = 2.0  =>  cost = (1 - 0.001) x 2.0 x 10 bps
                                          = 0.001998
      equity end  = 1 - 0.001 - 0.001998 = 0.997002 ; total_pnl = -0.002998
    """
    d1, d2, d3 = "2024-01-02", "2024-01-03", "2024-01-04"
    sessions = [d1, d2, d3]
    legs6 = ("SA", "SB", "SC", "SD", "SE", "SF")
    raw_close = {s: {d: 100.0 for d in sessions} for s in legs6}
    book1 = {"SA": LEG, "SB": LEG, "SC": LEG,
             "SD": -LEG, "SE": -LEG, "SF": -LEG}
    book2 = {s: -w for s, w in book1.items()}       # full sign flip
    entries = [
        {"entry_type": "FILL", "fill_date": d1, "targets": dict(book1)},
        {"entry_type": "FILL", "fill_date": d2, "targets": dict(book2)},
    ]
    result = value_book(entries, raw_close, {}, {}, sessions, cost_bps=10.0)

    t0 = 6 * LEG                       # hand: initial build turnover 1.0
    c0 = 1.0 * t0 * 10.0 / 1e4         # hand: 0.001
    t1 = 12 * LEG                      # hand: full flip 2.0
    c1 = (1.0 - c0) * t1 * 10.0 / 1e4  # hand: 0.001998
    assert len(result.fill_costs) == 2                      # ONE per fill
    assert [f[0] for f in result.fill_costs] == [d1, d2]
    assert result.fill_costs[0][1] == pytest.approx(t0, rel=1e-12)
    assert result.fill_costs[0][2] == pytest.approx(c0, rel=1e-12)
    assert result.fill_costs[1][1] == pytest.approx(t1, rel=1e-12)
    assert result.fill_costs[1][2] == pytest.approx(c1, rel=1e-12)
    assert result.total_cost == pytest.approx(math.fsum([c0, c1]), rel=1e-12)
    assert_reconciles(result)          # attribution identity + no double-add
    # constant prices => the only PnL is the cost drag
    assert result.total_pnl == pytest.approx(-(c0 + c1), rel=1e-12)

    # the turnover convention itself: hand sum of |delta_w|, CASH excluded
    before = {"SA": 0.5, "SD": 0.25, CASH_SYMBOL: 0.25}
    after = {"SA": 0.25, "SD": 0.5, CASH_SYMBOL: 0.25}
    assert etf_leg_turnover(before, after) == 0.25 + 0.25   # hand: 0.5
    assert etf_leg_turnover(before, after) != 0.75          # CASH not counted


# =========================================================================== #
# EVIDENCE 10 -- schedule-only feasibility on the REAL snapshot
# =========================================================================== #
def _load_real_snapshot():
    """Master SPY calendar + per-symbol presence sets from the staging files."""
    spy = json.load(open(STAGING / "SPY_none_p1.json", encoding="utf-8"))
    dates = sorted(v["datetime"] for v in spy["values"])
    presence = {}
    for s in CFG[ARM_KEY_ANCHOR].symbols:
        sym = json.load(open(STAGING / f"{s}_none_p1.json", encoding="utf-8"))
        presence[s] = {v["datetime"] for v in sym["values"]}
    return dates, presence


@pytest.mark.skipif(not STAGING.is_dir(),
                    reason="UNAVAILABLE: real snapshot staging not present")
def test_e10_real_schedule_only_feasibility():
    """REAL snapshot, SCHEDULE-ONLY: anchored 63-session clock decisions
    within the three frozen folds; counts 10/10/10 = 30; every decision on
    the master calendar; the 252-session warmup exists at every decision for
    the eligible rank set (documented XLC rule); force-flat at every fold
    boundary; next-allowed-session fills.  Output: dates and counts ONLY to
    research/control/stocks_free_v4_run/i_family_1_schedule_check.json."""
    dates, presence = _load_real_snapshot()
    report = {
        "schema": "stocks_free_v4_run/i_family_1_schedule_check@1",
        "producer_role": "A8",
        "family_id": "SFV4-A5-H1-PARTICIPATION-SHIFT",
        "feasibility": "SCHEDULE_ONLY_NO_PNL_NO_REAL_FEATURE_VALUES",
        "clock_note": (
            "byte-exact anchored clock per selection_freeze.json (A9-F): "
            "decisions at master indexes anchor(2018-04-04)+63k. Under this "
            "pin the first decisions of folds 2/3 land at 2020-10-02 and "
            "2023-04-05 (the anchored ticks inside those folds), not at the "
            "fold start sessions 2020-09-10/2023-02-17; fold decision counts "
            "remain 10/10/10 = 30 as the proposal expects, and no anchored "
            "tick falls in a fold gap (zero voided ticks)."
        ),
        "xlc_availability_rule": (
            "fixed availability rule (not performance-based): a sector "
            "enters the rank set at the first anchored decision where its "
            "data covers all 252 master sessions ending at the decision; "
            "XLC (first session 2018-06-19) first qualifies at the "
            "2019-07-05 decision (k=5); before that the rank set is the 10 "
            "available sectors"
        ),
        "arms": {},
    }

    expected_fold_counts = {"S0_FOLD_1": 10, "S0_FOLD_2": 10, "S0_FOLD_3": 10}
    for key, arm in CFG.items():
        sched = build_arm_schedule_walk(arm, dates)
        assert len(sched.voided) == 0
        # counts: exactly 10 decisions per fold, 30 total
        for fold_id, expected in expected_fold_counts.items():
            assert len(sched.decisions_in_fold(fold_id)) == expected
        assert len(sched.decided) == 30
        # feasibility report with every structural check green
        feas = schedule_feasibility(arm, sched, dates, presence)
        assert feas["all_checks_pass"], feas["checks"]
        assert feas["decisions_total"] == 30
        # every decision session exists on the master calendar and fills at
        # the next allowed session (checked inside feasibility; re-assert)
        for _fold_id, fold in feas["folds"].items():
            for d, f in zip(fold["decision_sessions"], fold["fill_sessions"]):
                assert d in set(dates) and f in set(dates)
                assert dates[dates.index(d) + 1] == f
        report["arms"][arm.arm_id] = feas

        if key == ARM_KEY_ANCHOR:
            # anchor-specific pins (deterministic from the snapshot calendar)
            fold1 = sched.decisions_in_fold("S0_FOLD_1")
            assert fold1[0].session == "2018-04-04"        # the anchor itself
            assert fold1[0].fill_session == "2018-04-05"   # next allowed
            assert fold1[-1].session == "2020-07-06"       # k=9
            assert sched.decisions_in_fold("S0_FOLD_2")[0].session == "2020-10-02"
            assert sched.decisions_in_fold("S0_FOLD_3")[0].session == "2023-04-05"
            assert sched.decisions_in_fold("S0_FOLD_3")[-1].session == "2025-07-11"
            # XLC eligibility transition is deterministic: 10 eligible for
            # k=0..4, then 11 from k=5 (2019-07-05) onward
            sizes = feas["folds"]["S0_FOLD_1"]["eligible_rank_set_sizes"]
            assert sizes == [10, 10, 10, 10, 10, 11, 11, 11, 11, 11]
            assert fold1[5].session == "2019-07-05"
            # folds 2 and 3: full 11-sector rank set at every decision
            assert feas["folds"]["S0_FOLD_2"]["eligible_rank_set_sizes"] == [11] * 10
            assert feas["folds"]["S0_FOLD_3"]["eligible_rank_set_sizes"] == [11] * 10
            # force-flat at every fold end (baseline invariants)
            assert [f.session for f in sched.force_flats] == \
                ["2020-09-01", "2023-02-09", "2025-07-24"]

        # double generation on the REAL calendar is byte-identical
        assert schedules_equal(sched, build_arm_schedule_blockwise(arm, dates))

    # ---- write the schedule check artifact: dates and counts ONLY --------
    payload = json.dumps(report, indent=2, sort_keys=True)
    lowered = payload.lower()
    for banned in ("expectancy", "profit_factor", "total_pnl", "equity_curve",
                   "shock_ratio", "leg_weight"):
        assert banned not in lowered, f"schedule check must not carry {banned!r}"
    SCHEDULE_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_CHECK_PATH.write_text(payload + "\n", encoding="utf-8")
    assert SCHEDULE_CHECK_PATH.is_file()
    # no scored metric of any kind exists in this lane
    assert report["feasibility"].startswith("SCHEDULE_ONLY_NO_PNL")


# =========================================================================== #
# EVIDENCE 11 -- meaningful held-max-weight drop-one
# =========================================================================== #
def test_e11_drop_one_max_contribution_leg():
    """Drop-one selects the held leg with max |contribution| (canonical
    selector), rebuilds the book by re-ranking the remaining sectors from
    scratch under the identical rule, and the resulting book is materially
    different (membership changes, dropped leg absent); the code path runs."""
    dates = business_dates(N + 2)  # T+1 must exist for the contribution window
    aligned = make_aligned(dates, overrides={
        "SG": [(2.0, T - 20, T)],     # top shock -> long leg
        "SA": [(0.5, T - 20, T)],     # bottom shock -> short leg
    })
    dec = decide_at(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR], list(SYNTH_SYMBOLS))
    targets = dec["targets"]
    assert targets["SG"] == LEG and targets["SA"] == -LEG

    # synthetic contribution path: SG trends +1%/session over the holding
    # window, everything else flat => SG carries the max |contribution|.
    d0, d1 = dates[T], dates[T + 1]
    raw_close = {s: {d0: 100.0, d1: 100.0} for s in SYNTH_SYMBOLS}
    raw_close["SG"][d1] = 101.0
    entries = [{"entry_type": "FILL", "fill_date": d0, "targets": dict(targets)}]
    result = value_book(entries, raw_close, {}, {}, [d0, d1], cost_bps=10.0)
    dropped = select_drop_one_symbol(result.symbol_contribution, targets)
    assert dropped == "SG"
    assert abs(result.symbol_contribution["SG"]) == max(
        abs(v) for v in result.symbol_contribution.values())

    # rebuild from scratch under the identical rule minus SG: the 4th-ranked
    # sector is promoted to the long side; book materially different.
    rebuilt = rebuild_targets_excluding(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                                        list(SYNTH_SYMBOLS), excluded="SG")
    assert "SG" not in rebuilt
    assert rebuilt["SD"] == LEG            # 4th-ranked promoted to a long
    assert rebuilt["SA"] == -LEG
    assert set(rebuilt) - {CASH_SYMBOL} != set(targets) - {CASH_SYMBOL}
    assert sum(1 for s, w in rebuilt.items()
               if s != CASH_SYMBOL and w > 0) == 3      # still a 3v3 book
    # the eligibility/presence path agrees with the manual remaining set
    elig = eligibility(dates, T, full_presence(dates), warmup=252,
                       symbols=SYNTH_SYMBOLS)
    assert elig == list(SYNTH_SYMBOLS)
    # fail-closed: dropping a symbol outside the eligible set (or CASH)
    with pytest.raises(FeatureError):
        rebuild_targets_excluding(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                                  list(SYNTH_SYMBOLS), excluded="SX")
    with pytest.raises(FeatureError):
        rebuild_targets_excluding(aligned, T, SHOCK_WINDOWS[ARM_KEY_ANCHOR],
                                  list(SYNTH_SYMBOLS), excluded=CASH_SYMBOL)


# =========================================================================== #
# EVIDENCE 12 -- dummy publication / refusal / replay (temp ledger ONLY)
# =========================================================================== #
def test_e12_dummy_publication_refusal_replay(tmp_path):
    """Record a DUMMY artifact (scored=false, real_pnl=false) against a TEMP
    ledger only: observed increments exactly once, replays are zero-delta,
    zero-position results are refused, and the canonical ledger file is left
    byte-identical."""
    canonical_stat = (CANONICAL_EVENT_LOG.stat().st_size,
                      CANONICAL_EVENT_LOG.stat().st_mtime_ns) \
        if CANONICAL_EVENT_LOG.is_file() else None

    tmp_ledger_path = tmp_path / "dummy_ledger.json"
    assert tmp_ledger_path != CANONICAL_EVENT_LOG
    ledger = GatedTrialLedger(str(tmp_ledger_path))

    key = "SFV4-A5-H1-A/DUMMY/synthetic"
    ledger.compute_recorded(key)                    # observed increments once
    assert ledger.observed == 1
    artifact = {
        "schema": "stocks_free_v4_run/i_family_1_dummy@1",
        "producer_role": "A8",
        "family_id": "SFV4-A5-H1-PARTICIPATION-SHIFT",
        "arm_id": "SFV4-A5-H1-A",
        "scored": False,
        "real_pnl": False,
        "note": "DUMMY synthetic artifact; zero scored metrics produced",
        "synthetic_expectancy": 0.0,     # finite dummy metric, NOT scored
    }
    # a synthetic 3v3 book entry set drives the gate counts
    book_entries = [
        {"entry_type": "FILL", "fill_date": "2024-01-02",
         "targets": {"SA": LEG, "SB": LEG, "SC": LEG,
                     "SD": -LEG, "SE": -LEG, "SF": -LEG}},
        {"entry_type": "FORCE_FLAT", "fill_date": "2024-01-03"},
    ]
    metrics = publication_metrics(book_entries)
    assert metrics == {"n_fill_events": 1, "n_held_positions": 6}
    assert ledger.publish_result(key, artifact, **metrics) is True
    assert len(ledger.published_keys) == 1

    # replays are zero-delta
    assert ledger.publish_result(key, artifact, **metrics) is False
    assert ledger.publish_result(key, artifact, **metrics) is False
    assert ledger.observed == 1
    assert len(ledger.published_keys) == 1

    # zero-position results are refused (key stays unpublished, observed keeps
    # its single increment per compute)
    key2 = "SFV4-A5-H1-C/DUMMY/zero-positions"
    ledger.compute_recorded(key2)
    assert ledger.publish_result(key2, artifact, n_fill_events=0,
                                 n_held_positions=0) is False
    assert key2 not in ledger.published_keys
    assert ledger.observed == 2 and len(ledger.published_keys) == 1
    assert ledger.refusals == [{"key": key2,
                                "reasons": ["ZERO_FILL_EVENTS",
                                            "ZERO_HELD_POSITIONS"]}]

    # save / reload round-trip on the TEMP path preserves counters
    ledger.save()
    reloaded = GatedTrialLedger(str(tmp_ledger_path))
    assert reloaded.observed == 2
    assert reloaded.published_keys == {key}

    # the canonical ledger is untouched (this test only ever stat()s it)
    if canonical_stat is not None:
        after = (CANONICAL_EVENT_LOG.stat().st_size,
                 CANONICAL_EVENT_LOG.stat().st_mtime_ns)
        assert after == canonical_stat
