"""COMMODITIES-NG1 I-phase runner-machinery tests (task
commodities-ng1-i-implementation).

SYNTHETIC FIXTURES ONLY for every decision series, kernel book, control
output and outcome number: the frozen rule machinery, execution law,
control battery and R1-R6 scaffolding are pinned with HAND-COMPUTED
series on synthetic weekly grids.  Real-substrate access is limited to
STRUCTURAL plumbing (digests, counts, config assembly): the committed
S freeze is re-verified for the 3 booked-cell digests, and the
``--dry-run-plumbing`` self-check runs on SYNTHETIC loaders with the
I-phase no-PnL law enforced.  NO scored execution and no outcome
number on real data anywhere.

Semantic provenance pinned here: the anchor state machine re-states
the committed D2 measurement machinery (measure_novelty.py::
percentile_tail + state_a4p2) verbatim; the parity was additionally
verified against that committed code on randomized synthetic chains
across all 9 frozen parameter combinations (w in {52,104,156} x cut in
{0.05,0.10,0.20}, tau 0.02, h_max 13).
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

RUN_DIR = os.path.join(REPO_ROOT, "research", "control",
                       "commodities_ng1_run")

from research.assets.commodities_ng1 import clock as K
from research.assets.commodities_ng1 import kernel as KX
from research.assets.commodities_ng1.cot_census import (
    CotLookupRefused, release_instant as p0_release_instant,
)
from research.assets.commodities_ng1.clock import KernelPitRefused
from research.assets.commodities_ng1.runners import (
    battery_position_series, chain as CH, decision_trades, arm_metrics,
    book_ledger, control_verdict_row, control_verdict_rows,
    crowd_carry_positions, empty_booked_population_verdict,
    percentile_tail, price_only_positions,
    release_clock_positions, shifted_release_positions,
    clairvoyant_positions, trades_to_folds, falsification_eval,
    q11_eligibility, evaluate_stage_a, pbo_verdict, fold_of, sign,
)
from research.assets.commodities_ng1.runners.chain import (
    build_pair_chain, counted_rows, verify_pair_census, ChainRefused,
)
from research.assets.commodities_ng1.runners.dry_run import (
    assemble_booked_arms, assert_structural, plumbing_self_check,
)
from research.assets.commodities_ng1.runners.execute import (
    ExecutionRefused,
)
from research.assets.commodities_ng1.runners.stage_a import (
    FOLDS_FROZEN, FoldRefused, r1_expectancy, r2_control_kill,
    r3_folds, r4_profit_factor, r5_stress, r6_non_concentration,
)


# ----------------------------------------------------------------------- #
# Synthetic fixture helpers
# ----------------------------------------------------------------------- #

def weekday_sessions(start: date, weeks: int) -> list[date]:
    """Synthetic measured session calendar: every Mon-Fri (no holidays)."""
    out = []
    d = start
    end = start + timedelta(days=7 * weeks)
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def synthetic_closes(sessions: list[date]) -> dict:
    """Deterministic synthetic RAW closes (no outcome semantics)."""
    return {s: 100.0 + (s.toordinal() % 23) * 0.25 for s in sessions}


def rows_from_g(g_values: list, spec_nets: list | None = None) -> list[dict]:
    """Minimal chain rows for the pure state-machine tests: g given,
    spec_net defaults to g*1000 (integer crowd counts)."""
    rows = []
    for i, g in enumerate(g_values):
        spec = int(round(g * 1000)) if spec_nets is None else spec_nets[i]
        rows.append({
            "report_date": date(2020, 1, 7) + timedelta(days=7 * i),
            "release_instant": p0_release_instant(
                date(2020, 1, 7) + timedelta(days=7 * i)),
            "release_date": date(2020, 1, 10) + timedelta(days=7 * i),
            "decision_session": date(2020, 1, 13) + timedelta(days=7 * i),
            "g": g,
            "spec_net": spec,
            "comm_net": 0,
            "open_interest": 1000,
            "cend_session": None,
            "cend_close": None,
        })
    return rows


PARAMS = {"percentile_window_weeks_w": 4, "tail_q_lo": 0.25,
          "tail_q_hi": 0.75, "trigger_tau_geometry": 0.02,
          "carry_bound_weeks_h_max": 2}


# ----------------------------------------------------------------------- #
# 1. Frozen rule machinery (hand-computed decision series)
# ----------------------------------------------------------------------- #

def test_percentile_tail_hand_computed():
    # window w=4, cut=0.25, values [.50,.60,.40,.70]: x=.70 rank 4/4 -> hi
    v = [0.50, 0.60, 0.40, 0.70]
    assert percentile_tail(v, 3, 4, 0.25) == "hi"
    # x=.30 over [0.60,0.40,0.70,0.30]: rank 1/4 = 0.25 <= 0.25 -> lo
    assert percentile_tail([0.60, 0.40, 0.70, 0.30], 3, 4, 0.25) == "lo"
    # true mid value (rank 0.5): neither cut -> None
    assert percentile_tail([0.10, 0.20, 0.30, 0.40], 1, 4, 0.25) is None
    # incomplete window -> None; None member -> None
    assert percentile_tail(v, 2, 4, 0.25) is None
    assert percentile_tail([0.1, None, 0.3, 0.4], 3, 4, 0.25) is None
    # degenerate: rank in [1-cut, cut] (needs cut >= 0.5) satisfies BOTH
    # cuts -> None, never a bucket (D2 refusal semantics)
    assert percentile_tail([1.0, 2.0, 3.0, 4.0], 3, 4, 0.6) is not None
    assert percentile_tail([1.0, 2.0, 3.0, 4.0], 1, 4, 0.6) is None


def test_anchor_entry_trigger_and_flip_entry_hand_computed():
    # w=4 cut=0.25 tau=0.02 h_max=2 (PARAMS)
    g = [0.50, 0.60, 0.40, 0.70, 0.30, 0.20, 0.10, 0.05, 0.00,
         -0.05, -0.30, -0.60]
    rows = rows_from_g(g)
    pos = crowd_carry_positions(rows, PARAMS)
    # i3 'hi' entry d=sign(spec_net)=+1; i4 same-row trigger + left-tail
    # -> flat, then fresh 'lo' transition re-arms d=+1 (spec_net>0);
    # i5 opposing flow -0.10 >= tau -> trigger to flat; 'lo' stays
    # entered -> no fresh re-entry afterwards.
    assert pos == [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                   0.0, 0.0]


def test_anchor_h_max_bound_and_short_entry_hand_computed():
    g = [0.40, 0.60, 0.80, 0.20, 0.19, 0.18, 0.17, 0.16, 0.15]
    spec = [400, 600, 800, -200, -190, -180, -170, -160, -150]
    rows = rows_from_g(g, spec)
    pos = crowd_carry_positions(rows, PARAMS)
    # i3 fresh 'lo' entry with negative crowd (d=-1); flows -0.01 are
    # below tau and same-sign -> hold i4; i5 is the h_max bound
    # (5-3 >= 2) -> flat; 'lo' remains entered -> no re-entry.
    assert pos == [0.0, 0.0, 0.0, -1.0, -1.0, 0.0, 0.0, 0.0, 0.0]


def test_anchor_opposite_tail_flip_hand_computed():
    g = [0.80, 0.90, 0.70, 0.10, 0.90, 0.80, 0.95, 0.70, 0.60, 0.50]
    spec = [800, 900, 700, -300, 500, 800, 950, -200, -200, -200]
    params = dict(PARAMS, trigger_tau_geometry=0.99,
                  carry_bound_weeks_h_max=10)   # triggers/bound off
    pos = crowd_carry_positions(rows_from_g(g, spec), params)
    # 'lo' entry d=-1 at i3; direct transition into 'hi' at i4 ->
    # left-tail flat THEN fresh 'hi' re-arm d=+1 (the flip under the
    # same frozen convention); i7 back to 'lo' -> flip to -1.
    assert pos == [0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, -1.0, -1.0, -1.0]


def test_anchor_no_entry_on_zero_crowd():
    g = [0.40, 0.60, 0.80, 0.20, 0.20, 0.20]
    spec = [400, 600, 800, 0, 0, 0]
    pos = crowd_carry_positions(rows_from_g(g, spec), PARAMS)
    # fresh 'lo' bucket at i3 but spec_net == 0 -> no arming (frozen
    # convention d != 0 required).  The later tie cluster raises ranks
    # into the 'hi' bucket (rank >= 0.75) but d stays 0 -> never armed.
    assert pos == [0.0] * 6


def test_anchor_asymmetric_tails_refused():
    rows = rows_from_g([0.5] * 6)
    bad = dict(PARAMS, tail_q_lo=0.1, tail_q_hi=0.8)
    with pytest.raises(ValueError, match="symmetric"):
        crowd_carry_positions(rows, bad)


def test_sign_convention():
    assert sign(0.1) == 1.0 and sign(-0.1) == -1.0 and sign(0.0) == 0.0
    assert sign(None) == 0.0


# ----------------------------------------------------------------------- #
# 2. Price-only shadow (hand-computed, NO CoT input)
# ----------------------------------------------------------------------- #

def test_price_only_shadow_hand_computed():
    # designed weekly displacement series r (row 0 undefined);
    # w=5, cut=0.25, tau_price=0.02, h_max=3
    r = [None, 0.05, 0.06, 0.04, 0.02, -0.03, -0.04, -0.06, 0.05, -0.08]
    rows = rows_from_g([0.0] * len(r))       # g unused by the shadow
    close = 100.0
    for i, row in enumerate(rows):
        if i == 0:
            row["cend_close"] = close
            continue
        close = close * (1.0 + r[i])   # close-to-close ratio == r[i]
        row["cend_close"] = close
    params = {"percentile_window_weeks_w": 5, "tail_q_lo": 0.25,
              "tail_q_hi": 0.75, "carry_bound_weeks_h_max": 3,
              "tau_price_weekly_a4p2": 0.02}
    pos = price_only_positions(rows, params)
    # i5 fresh 'lo' displacement tail -> short (d=sign(r)=-1); holds
    # i6,i7 (flows same-sign, below the h_max bound); i8 displacement
    # +0.05 >= 0.02 opposing AND leaves the tail -> flat then fresh
    # 'hi' re-arm +1; i9 back to 'lo' -> flip to -1.
    assert pos == [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, -1.0, 1.0, -1.0]


# ----------------------------------------------------------------------- #
# 3. Release-clock shadow + shifted-release placebo (hand-computed)
# ----------------------------------------------------------------------- #

def test_release_clock_fixed_sign_pooled():
    assert release_clock_positions(7) == [1.0] * 7
    assert release_clock_positions(3, -1.0) == [-1.0] * 3
    with pytest.raises(ValueError):
        release_clock_positions(3, 0.5)


def test_shifted_release_placebo_k4_hand_computed():
    anchor = [0.0, 1.0, 1.0, 0.0, -1.0, -1.0, -1.0, 0.0, 0.0]
    pos = shifted_release_positions(anchor, 4)
    # decision row i reads the state as of report i-4 (k frozen at 4):
    # pos[i] = anchor[i-4] for i >= 4, else flat
    assert pos == [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, -1.0]
    with pytest.raises(ValueError):
        shifted_release_positions(anchor, 0)


# ----------------------------------------------------------------------- #
# 4. Clairvoyant ceiling (diagnostic; full-sample buckets)
# ----------------------------------------------------------------------- #

def test_clairvoyant_full_sample_buckets():
    g = [0.80, 0.90, 0.70, 0.10, 0.90, 0.80]
    spec = [800, 900, 700, -300, 500, 800]
    params = dict(PARAMS, trigger_tau_geometry=0.99,
                  carry_bound_weeks_h_max=10)
    rows = rows_from_g(g, spec)
    pos = clairvoyant_positions(rows, params)
    # full-sample ranks (n=6): .90 -> 'hi' (rank 1.0), .10 -> 'lo'
    # (rank 1/6), the rest mid -> None.  Oracle entry needs no warmup:
    # i1 fresh 'hi' -> +1; i2 leaves the tail -> flat; i3 fresh 'lo'
    # -> -1; i4 fresh 'hi' -> +1; i5 leaves -> flat.
    assert pos == [0.0, 1.0, 0.0, -1.0, 1.0, 0.0]
    # the live anchor (trailing windows) is warmup-bound: flat at i1
    anchor_live = crowd_carry_positions(rows, params)
    assert anchor_live[:2] == [0.0, 0.0]
    assert anchor_live[3] == -1.0            # first trailing 'lo' entry


# ----------------------------------------------------------------------- #
# 5. Chain assembly (clock, PIT, readability, counted window)
# ----------------------------------------------------------------------- #

def tuesdays(start: date, n: int) -> list[date]:
    return [start + timedelta(days=7 * i) for i in range(n)]


def test_chain_decision_sessions_readability_and_counted():
    start = date(2018, 1, 2)                    # a Tuesday
    reps = tuesdays(start, 60)
    reports = [{"report_date": d, "open_interest": 1000,
                "noncomm_long": 100, "noncomm_short": 0,
                "noncomm_spreading": 0, "comm_long": 0, "comm_short": 0}
               for d in reps]
    sessions = weekday_sessions(date(2017, 12, 1), 70)
    closes = synthetic_closes(sessions)
    chain = build_pair_chain(reports, sessions, closes)
    rows = chain["rows"]
    assert len(rows) == 60
    r0 = rows[0]
    # release = Friday 15:30 ET of the report week, decision session =
    # next measured session strictly after the release day (Monday)
    assert r0["release_date"] == date(2018, 1, 5)
    assert r0["decision_session"] == date(2018, 1, 8)
    assert r0["rule_source"] == "p0_release_instant"
    # cend_close = previous session's close (the D1 stricter close+1
    # reading: the decision session's own close is never a fact source)
    assert r0["cend_session"] == date(2018, 1, 5)
    assert r0["cend_close"] == closes[date(2018, 1, 5)]
    # counted window: 60 window releases - 52 warmup = 8 counted
    assert sum(chain["counted"]) == 8
    assert chain["rows"][counted_rows(chain)[0]]["release_date"] \
        == date(2019, 1, 4)
    # geometry identity on committed counts
    assert r0["g"] == ((100 - 0) - (0 - 0)) / 1000
    assert r0["spec_net"] == 100


def test_chain_holiday_shift_monday_report():
    monday = date(2018, 2, 19)                  # measured holiday shift
    reports = [{"report_date": monday, "open_interest": 1000,
                "noncomm_long": 10, "noncomm_short": 0,
                "noncomm_spreading": 0, "comm_long": 0, "comm_short": 0}]
    sessions = weekday_sessions(date(2018, 2, 1), 4)
    chain = build_pair_chain(reports, sessions, synthetic_closes(sessions))
    row = chain["rows"][0]
    # same week anchor: Friday of that week; identity asserted by the
    # committed feasibility rule (imported, never re-derived)
    assert row["release_date"] == date(2018, 2, 23)
    assert row["rule_source"] == "week_anchor_holiday_shift"


def test_chain_refuses_non_conforming_report_dates():
    sessions = weekday_sessions(date(2018, 1, 1), 4)
    # neither Tuesday nor Monday: the committed release rule refuses
    with pytest.raises(Exception):
        build_pair_chain([{"report_date": date(2018, 1, 3),
                           "open_interest": 10, "noncomm_long": 1,
                           "noncomm_short": 0, "noncomm_spreading": 0,
                           "comm_long": 0, "comm_short": 0}],
                         sessions, synthetic_closes(sessions))
    # duplicate report dates: fail closed
    dup = {"report_date": date(2018, 1, 2), "open_interest": 10,
           "noncomm_long": 1, "noncomm_short": 0, "noncomm_spreading": 0,
           "comm_long": 0, "comm_short": 0}
    with pytest.raises(ChainRefused, match="duplicate"):
        build_pair_chain([dup, dict(dup)], sessions,
                         synthetic_closes(sessions))


def test_kernel_pit_gate_refuses_early_read():
    d = date(2018, 1, 2)
    release = p0_release_instant(d)
    with pytest.raises(KernelPitRefused):
        K.kernel_pit_require_visible(
            d, release - timedelta(seconds=1))
    g = K.kernel_pit_require_visible(d, release)
    assert g["pit_allowed"] is True
    # Monday as-of dates are the committed feasibility rule's extension;
    # the raw P0 kernel gate refuses them (canary semantics) -- which is
    # exactly why the runner imports the committed generalized rule.
    with pytest.raises(CotLookupRefused):
        K.kernel_pit_require_visible(date(2018, 2, 19), release)


def test_chain_census_identity():
    start = date(2018, 1, 2)
    reps = tuesdays(start, 60)
    reports = [{"report_date": d, "open_interest": 1000,
                "noncomm_long": 5, "noncomm_short": 0,
                "noncomm_spreading": 0, "comm_long": 0, "comm_short": 0}
               for d in reps]
    sessions = weekday_sessions(date(2017, 12, 1), 70)
    chain = build_pair_chain(reports, sessions, synthetic_closes(sessions))
    window_rows = [i for i, r in enumerate(chain["rows"])
                   if r["release_date"] >= date(2018, 1, 1)]
    counted_window = window_rows[52:]
    mapped = [i for i in counted_window
              if chain["rows"][i]["decision_session"] is not None]
    floor = {
        "counted_expected_releases": len(counted_window),
        "grid_eligible_instants": len(mapped),
        "counted_first_release":
            chain["rows"][mapped[0]]["release_date"].isoformat(),
        "counted_last_release":
            chain["rows"][counted_window[-1]]["release_date"].isoformat(),
        "unmapped_release_dates_counted": [],
    }
    assert verify_pair_census("TEST/LEG", chain, floor) is True
    broken = dict(floor, grid_eligible_instants=len(mapped) + 1)
    with pytest.raises(ChainRefused, match="grid-eligible"):
        verify_pair_census("TEST/LEG", chain, broken)


# ----------------------------------------------------------------------- #
# 6. Execution -> P1 kernel books (hand-computed)
# ----------------------------------------------------------------------- #

def counted_chain(decision_sessions: list[date],
                  release_dates: list[date]) -> dict:
    rows = [{"report_date": rd - timedelta(days=3),   # Tuesday of week
             "release_instant": p0_release_instant(rd - timedelta(days=3)),
             "release_date": rd,
             "rule_source": "p0_release_instant",
             "decision_session": ds, "g": 0.5, "spec_net": 500,
             "comm_net": 0, "open_interest": 1000,
             "cend_session": None, "cend_close": None}
            for rd, ds in zip(release_dates, decision_sessions)]
    n = len(rows)
    return {"rows": rows, "counted": [True] * n}


MONDAYS = [date(2020, 1, 6) + timedelta(days=7 * i) for i in range(4)]
RELEASES = [d - timedelta(days=3) for d in MONDAYS]   # prior Friday


def leg_constants(half=0.002, expense=0.05, tracking=0.01):
    return {"TESTLEG": {"half_spread_frac": half,
                        "expense_annual": expense,
                        "tracking_divergence_annual": tracking}}


def test_decision_trades_and_kernel_books_hand_computed():
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = dict(synthetic_closes(sessions))
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 13)] = 110.0
    closes[date(2020, 1, 20)] = 90.0
    closes[date(2020, 1, 27)] = 95.0
    chain = counted_chain(MONDAYS, RELEASES)
    positions = [1.0, 1.0, 0.0, 0.0]
    res = decision_trades(chain, positions, "TESTLEG", sessions, closes)
    assert len(res["trades"]) == 1
    t = res["trades"][0]
    assert t["direction"] == 1 and t["closed"] is True
    assert t["entry_session"] == date(2020, 1, 6)
    assert t["exit_session"] == date(2020, 1, 20)
    assert t["entry_price"] == 100.0 and t["exit_price"] == 90.0
    assert t["days_held"] == 14
    assert len(t["fills"]) == 2                      # once-per-fill law
    assert res["fills"] == 2
    booked = book_ledger(res["trades"], leg_constants())
    led = booked["ledger"]
    # hand-computed: gross = 1.0*(90/100-1) = -0.10
    assert led["gross"]["total"] == pytest.approx(-0.10)
    # transaction at tier 2.0 = 2 fills x (1.0 x 0.002 x 2.0) = 0.008
    assert led["costs"]["2.0"]["commissions_total"] == pytest.approx(0.008)
    # drag = 1.0 x (0.05 + 0.01) x 14 / 365.25
    drag = 1.0 * 0.06 * 14 / 365.25
    assert led["costs"]["2.0"]["slippage_total"] == pytest.approx(drag)
    net = -0.10 - 0.008 - drag
    assert led["net"]["2.0"]["total"] == pytest.approx(net)
    # dual-book identity through the ROOT accounting module
    assert booked["reconciliation"]["identity_ok"] is True
    # tiers scale ONLY the transaction component
    assert led["costs"]["1.0"]["commissions_total"] \
        == pytest.approx(0.004)
    assert led["costs"]["1.0"]["slippage_total"] == pytest.approx(drag)
    m = arm_metrics(led, eligible_instants=4)
    assert m["per_trade_edge"] == pytest.approx(net / 1)
    assert m["per_decision_edge"] == pytest.approx(net / 4)


def test_delay_pair_d1_execution_mapping():
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = synthetic_closes(sessions)
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 13)] = 110.0
    closes[date(2020, 1, 20)] = 90.0
    chain = counted_chain(MONDAYS, RELEASES)
    positions = [1.0, 1.0, 0.0, 0.0]
    res = decision_trades(chain, positions, "TESTLEG", sessions, closes,
                          execution_lag_sessions=1)
    t = res["trades"][0]
    # D1 placement: fills at the NEXT measured session after D0
    assert t["entry_session"] == date(2020, 1, 7)
    assert t["exit_session"] == date(2020, 1, 21)
    # the decision series itself is unchanged (placement diagnostic)
    assert positions == [1.0, 1.0, 0.0, 0.0]


def test_split_boundary_law_excludes_spanning_trade():
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = dict(synthetic_closes(sessions))
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 20)] = 90.0
    chain = counted_chain(MONDAYS, RELEASES)
    positions = [1.0, 1.0, 0.0, 0.0]
    res = decision_trades(chain, positions, "TESTLEG", sessions, closes,
                          split_boundary_dates={date(2020, 1, 15)})
    assert res["trades"] == []
    assert len(res["split_boundary_excluded"]) == 1
    ex = res["split_boundary_excluded"][0]
    assert ex["entry_session"] == "2020-01-06"
    assert ex["exit_session"] == "2020-01-20"
    assert "share-base boundary" in ex["reason"]
    # a boundary ON the entry date is a single-base trade: bookable
    res2 = decision_trades(chain, positions, "TESTLEG", sessions, closes,
                           split_boundary_dates={date(2020, 1, 6)})
    assert len(res2["trades"]) == 1
    assert res2["split_boundary_excluded"] == []


def test_terminal_policy_force_closes_open_leg():
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = dict(synthetic_closes(sessions))
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 13)] = 110.0
    closes[date(2020, 1, 27)] = 105.0
    chain = counted_chain(MONDAYS, RELEASES)
    res = decision_trades(chain, [1.0, 1.0, 1.0, 1.0], "TESTLEG",
                          sessions, closes)
    assert len(res["trades"]) == 1
    t = res["trades"][0]
    assert t["closed"] is False                    # terminal population
    assert t["exit_session"] == sessions[-1]
    assert t["exit_price"] == closes[sessions[-1]]
    booked = book_ledger(res["trades"], leg_constants())
    led = booked["ledger"]
    assert led["gross_closed_total"] == pytest.approx(0.0)
    expected_terminal = closes[sessions[-1]] / 100.0 - 1.0
    assert led["gross_terminal_total"] == pytest.approx(expected_terminal)
    assert booked["reconciliation"]["identity_ok"] is True


def test_execution_refusals_fail_closed():
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = synthetic_closes(sessions)
    chain = counted_chain(MONDAYS, RELEASES)
    with pytest.raises(ExecutionRefused):       # length mismatch
        decision_trades(chain, [1.0, 0.0], "TESTLEG", sessions, closes)
    with pytest.raises(ExecutionRefused):       # decision on uncounted row
        bad = {"rows": chain["rows"], "counted": [False] * 4}
        decision_trades(bad, [1.0, 0.0, 0.0, 0.0], "TESTLEG", sessions,
                        closes)
    # missing RAW close for the execution session
    partial = {k: v for k, v in closes.items() if k != MONDAYS[0]}
    with pytest.raises(ExecutionRefused, match="no RAW close"):
        decision_trades(chain, [1.0, 0.0, 0.0, 0.0], "TESTLEG", sessions,
                        partial)


def test_kernel_refuses_unmeasured_leg_fail_closed():
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = synthetic_closes(sessions)
    chain = counted_chain(MONDAYS, RELEASES)
    res = decision_trades(chain, [1.0, 0.0, 0.0, 0.0], "TESTLEG",
                          sessions, closes)
    with pytest.raises(KX.KernelRefused, match="half-spread"):
        book_ledger(res["trades"], {"OTHER": {"half_spread_frac": None}})


# ----------------------------------------------------------------------- #
# 7. Control battery + D1 falsification rule (hand-computed)
# ----------------------------------------------------------------------- #

def metrics_for(net_total: float, trades: int, decisions: int) -> dict:
    return {"per_trade_edge": net_total / trades,
            "per_decision_edge": net_total / decisions,
            "trades": trades, "eligible_instants": decisions}


def test_battery_roles_present_and_delay_pair_reuses_anchor():
    sessions = weekday_sessions(date(2017, 12, 1), 70)
    reps = tuesdays(date(2018, 1, 2), 60)
    reports = [{"report_date": d, "open_interest": 1000,
                "noncomm_long": (i * 37) % 900, "noncomm_short": 100,
                "noncomm_spreading": 0, "comm_long": 50,
                "comm_short": (i * 11) % 400}
               for i, d in enumerate(reps)]
    chain = build_pair_chain(reports, sessions, synthetic_closes(sessions))
    series = battery_position_series(chain, PARAMS)
    assert set(series) == {"ANCHOR", "PRICE_ONLY_SHADOW",
                           "RELEASE_CLOCK_SHADOW",
                           "SHIFTED_RELEASE_PLACEBO", "DELAY_PAIR",
                           "CLAIRVOYANT"}
    assert series["DELAY_PAIR"] == series["ANCHOR"]
    assert series["RELEASE_CLOCK_SHADOW"] == [1.0] * len(chain["rows"])
    # placebo = anchor lagged by the frozen k=4
    assert series["SHIFTED_RELEASE_PLACEBO"][4:] \
        == series["ANCHOR"][:-4]
    assert series["SHIFTED_RELEASE_PLACEBO"][:4] == [0.0] * 4


def test_falsification_rule_both_clauses_hand_computed():
    anchor = metrics_for(100.0, 4, 40)          # 25/trade, 2.5/decision
    # V8 fires (90 >= 0.5x100 same sign), falsification clear (2.25 < 2.5)
    v = r2_control_kill(anchor, metrics_for(90.0, 4, 40))
    assert v["v8_clause"]["fires"] is True
    assert v["falsification_clause"]["fires"] is False
    assert v["kill"] is True
    # below the V8 line and below the anchor edge: no kill
    v = r2_control_kill(anchor, metrics_for(40.0, 4, 40))
    assert v["kill"] is False
    # strictly greater per-decision edge kills even below the V8 line
    v = r2_control_kill(anchor, metrics_for(101.0, 20, 40))
    assert v["v8_clause"]["fires"] is False     # 5.05 < 12.5? no: 101/20
    # recompute: per-trade 5.05 >= 12.5 is FALSE -> V8 clear
    assert v["falsification_clause"]["fires"] is True   # 2.525 > 2.5
    assert v["kill"] is True
    # opposite-sign killer never fires either clause
    v = r2_control_kill(anchor, metrics_for(-200.0, 4, 40))
    assert v["kill"] is False
    # Q-11: undefined edges (no trades) can never kill
    v = r2_control_kill(anchor, {"per_trade_edge": None,
                                 "per_decision_edge": None})
    assert v["kill"] is False


def test_falsification_battery_eval_coverage():
    anchor = metrics_for(100.0, 4, 40)
    killers = {"PRICE_ONLY_SHADOW": metrics_for(101.0, 20, 40),
               "RELEASE_CLOCK_SHADOW": metrics_for(40.0, 4, 40),
               "SHIFTED_RELEASE_PLACEBO": metrics_for(90.0, 4, 40)}
    out = falsification_eval(anchor, killers)
    assert out["coverage_complete"] is True
    assert out["falsification_fired_by"] == ["PRICE_ONLY_SHADOW"]
    assert out["kill"] is True
    out = falsification_eval(anchor, {"PRICE_ONLY_SHADOW":
                                      metrics_for(1.0, 4, 40)})
    assert out["coverage_complete"] is False
    assert out["missing_killers"] == ["RELEASE_CLOCK_SHADOW",
                                      "SHIFTED_RELEASE_PLACEBO"]
    assert out["kill"] is False


def test_q11_eligibility_law():
    per_pair = {f"P{i}": 401 for i in range(11)}
    q = q11_eligibility(per_pair)
    assert q["pooled"]["eligible_instants"] == 4411
    assert q["pooled"]["verdict"] == "ELIGIBLE"
    assert q["eligible_overall"] is True
    per_pair["P7"] = 250                        # below the frozen 300
    q = q11_eligibility(per_pair)
    assert q["per_pair"]["P7"]["verdict"] == "NOT_RUN_INVALID"
    assert q["eligible_overall"] is False
    q = q11_eligibility({f"P{i}": 300 for i in range(11)})   # 3300 pooled
    assert q["pooled"]["verdict"] == "ELIGIBLE"
    q = q11_eligibility({f"P{i}": 299 for i in range(11)})
    assert q["pooled"]["verdict"] == "NOT_RUN_INVALID"


# ----------------------------------------------------------------------- #
# 8. R1-R6 scaffolding over the frozen folds (hand-computed)
# ----------------------------------------------------------------------- #

def test_frozen_folds_boundaries():
    assert [f["fold_id"] for f in FOLDS_FROZEN] \
        == ["fold-1", "fold-2", "fold-3"]
    assert fold_of("2019-01-04") == "fold-1"    # counted-window start
    assert fold_of("2021-08-31") == "fold-1"
    assert fold_of("2021-09-01") == "fold-2"
    assert fold_of("2024-04-30") == "fold-2"
    assert fold_of("2024-05-01") == "fold-3"
    assert fold_of("2026-09-11") == "fold-3"    # counted-window end
    assert fold_of("2019-01-03") is None
    assert fold_of("2026-09-12") is None
    with pytest.raises(FoldRefused):
        trades_to_folds([{"trade_id": "T", "entry_release_date":
                          "2018-12-31"}])


def test_r3_folds_hand_computed():
    assert r3_folds({"fold-1": 10.0, "fold-2": -5.0,
                     "fold-3": 3.0})["verdict"] == "PASS"
    assert r3_folds({"fold-1": 10.0, "fold-2": -5.0,
                     "fold-3": -3.0})["verdict"] == "FAIL"
    out = r3_folds({"fold-1": 10.0, "fold-2": -5.0})
    assert out["verdict"] == "FAIL"             # unmeasured fold: no pass
    assert out["folds"]["fold-3"]["positive"] is None


def test_r4_profit_factor_hand_computed():
    m = {"trades": 3, "profit_factor": 15.0 / 4.0}
    out = r4_profit_factor(m)
    assert out["verdict"] == "PASS"
    assert out["profit_factor"] == pytest.approx(3.75)
    assert out["margin_above_1_10"] == pytest.approx(2.65)
    out = r4_profit_factor({"trades": 2, "profit_factor": 5.0 / 10.0})
    assert out["verdict"] == "FAIL"
    assert out["margin_above_1_10"] == pytest.approx(-0.60)
    # no losing trades: PF unbounded -> honest PASS-with-None, not inf
    out = r4_profit_factor({"trades": 2, "profit_factor": None})
    assert out["verdict"] == "PASS" and out["profit_factor"] is None
    out = r4_profit_factor({"trades": 0, "profit_factor": None})
    assert out["verdict"] == "NOT_RUN"


def test_r1_r5_expectancy_and_stress():
    m = metrics_for(100.0, 4, 40)
    assert r1_expectancy(m)["verdict"] == "PASS"
    assert r5_stress(m)["verdict"] == "PASS"
    assert r5_stress(m)["stress_tier"] == 2.0
    assert r1_expectancy(metrics_for(-1.0, 4, 40))["verdict"] == "FAIL"
    assert r1_expectancy({"per_trade_edge": None})["verdict"] == "NOT_RUN"
    assert r5_stress({"per_trade_edge": None})["verdict"] == "NOT_RUN"


def test_r6_non_concentration_hand_computed():
    folds = {"fold-1": 10.0, "fold-2": 8.0, "fold-3": 6.0}
    m = {"net_pnls": [10.0, 8.0, 6.0], "gross_pnls": [40.0, 35.0, 25.0],
         "trades": 3}
    out = r6_non_concentration(m, folds)
    assert out["drop_one_survival"] is True
    assert out["max_event_gross_share"] == pytest.approx(0.40)
    assert out["verdict"] == "PASS"
    # single event > 50% of gross -> FAIL even with survival
    m = {"net_pnls": [10.0, 8.0, 6.0], "gross_pnls": [60.0, 30.0, 10.0],
         "trades": 3}
    out = r6_non_concentration(m, folds)
    assert out["concentrated"] is True
    assert out["verdict"] == "FAIL"
    # drop-one-fold breaks: removing fold-1 flips the kept total negative
    folds = {"fold-1": 100.0, "fold-2": -40.0, "fold-3": -40.0}
    m = {"net_pnls": [100.0, -40.0, -40.0],
         "gross_pnls": [100.0, -40.0, -40.0], "trades": 3}
    out = r6_non_concentration(m, folds)
    assert out["drop_one_survival"] is False
    assert out["verdict"] == "FAIL"


def test_evaluate_stage_a_survivor_and_kill_paths():
    anchor = metrics_for(100.0, 4, 40)
    folds = {"fold-1": 40.0, "fold-2": 30.0, "fold-3": 30.0}
    clean = {"PRICE_ONLY_SHADOW": metrics_for(20.0, 4, 40),
             "RELEASE_CLOCK_SHADOW": metrics_for(10.0, 4, 40),
             "SHIFTED_RELEASE_PLACEBO": metrics_for(5.0, 4, 40)}
    m = dict(anchor, net_pnls=[25.0] * 4, gross_pnls=[25.0] * 4,
             profit_factor=None)
    out = evaluate_stage_a(m, clean, folds)
    assert out["survivor"] is True
    assert out["verdict"] == "PROVISIONAL_STAGE_A_SURVIVOR"
    # a designated killer strictly greater per-decision -> KILL
    hot = {"PRICE_ONLY_SHADOW": metrics_for(200.0, 4, 40),
           "RELEASE_CLOCK_SHADOW": metrics_for(5.0, 4, 40),
           "SHIFTED_RELEASE_PLACEBO": metrics_for(1.0, 4, 40)}
    out = evaluate_stage_a(m, hot, folds)
    assert out["survivor"] is False
    assert out["r2_any_kill"] is True
    # R3 failure: only one positive fold
    out = evaluate_stage_a(m, clean, {"fold-1": 90.0, "fold-2": -50.0,
                                      "fold-3": -40.0})
    assert out["survivor"] is False
    assert out["rules"]["R3"]["verdict"] == "FAIL"


def test_pbo_fail_closed_law_with_precedent_citation():
    out = pbo_verdict(3)
    assert out["verdict"] == "NOT_RUN_CELLS_LT_8"
    assert out["booked_cells"] == 3 and out["minimum_cells"] == 8
    alt = out["alternative_rule"]
    # the frozen alternative is the FOREX-NG1 precedent rule cited
    # inside the S freeze (section3 law_sources)
    assert alt["git_commit"] == "d0992d17df8e2dfde57c9a0806a5798f14021a4f"
    assert alt["source"] == \
        "research/control/forex_ng1_run/selection_freeze.json"
    assert "R1-R6" in alt["law"] or "rule order" in alt["law"]
    assert_structural(out)
    assert pbo_verdict(8)["verdict"] == "MEASURABLE_AT_E"


# ----------------------------------------------------------------------- #
# 9. Config assembly: the 3 booked cells (structural; binding freeze)
# ----------------------------------------------------------------------- #

def test_booked_arm_config_digests_recompute():
    with open(os.path.join(RUN_DIR, "s", "selection_freeze.json"),
              encoding="utf-8") as fh:
        freeze = json.load(fh)
    out = assemble_booked_arms(freeze)
    assert out["single_family"] == "COMMNG1-A4-P2"
    assert out["booked_cells"] == 3 and out["unbooked_cells"] == 3
    assert out["trial_budget_cells"] == 6
    assert out["all_digests_match"] is True
    assert out["digests_pairwise_distinct"] is True
    recorded = {a["arm_id"]: a["recorded_digest"] for a in out["arms"]}
    # the freeze's recorded digests, pinned here verbatim
    assert recorded == {
        "COMMNG1-A4-P2-ARM1-NEUTRAL":
            "6c12044f88e5284297f50560587e041ccac3012454e9659340b348eb5d6e67d8",
        "COMMNG1-A4-P2-ARM2-TAILWIDE":
            "f7cabf47612b612586ebf702ccd33e6212bce92421faa399f8e241262f5e3623",
        "COMMNG1-A4-P2-ARM3-WINDOWSHORT":
            "ab57e6db76e23ae61733e3b85f54a1e7ee02b27a871ab0789cf1503a1530577e",
    }
    params = {a["arm_id"]: a["parameters"] for a in out["arms"]}
    # ANCHOR: w=104 tails .10/.90; TAILWIDE: .20/.80; WINDOWSHORT: w=52
    assert params["COMMNG1-A4-P2-ARM1-NEUTRAL"] == {
        "percentile_window_weeks_w": 104, "tail_q_lo": 0.1,
        "tail_q_hi": 0.9, "trigger_tau_geometry": 0.02,
        "carry_bound_weeks_h_max": 13}
    assert params["COMMNG1-A4-P2-ARM2-TAILWIDE"]["tail_q_lo"] == 0.2
    assert params["COMMNG1-A4-P2-ARM2-TAILWIDE"]["tail_q_hi"] == 0.8
    assert params["COMMNG1-A4-P2-ARM3-WINDOWSHORT"][
        "percentile_window_weeks_w"] == 52
    # tau and h_max fixed across all arms (variant-axis discipline)
    assert len({p["trigger_tau_geometry"] for p in params.values()}) == 1
    assert len({p["carry_bound_weeks_h_max"] for p in params.values()}) == 1
    # identical restricted set + tier 2.0 everywhere
    for a in out["arms"]:
        assert len(a["bookable_pairs"]) == 11
        assert a["primary_tier"] == 2.0


# ----------------------------------------------------------------------- #
# 10. --dry-run-plumbing self-check on SYNTHETIC data (counts only)
# ----------------------------------------------------------------------- #

def synthetic_freeze(tmp_pairs):
    return {
        "section2_arm_plan": {
            "single_family": "SYNTH-FAM",
            "bookable_set": {"pairs": list(tmp_pairs)},
            "arms": [
                {"arm_id": "SYN-ARM1", "role": "ANCHOR",
                 "selection_status": "BOOKED",
                 "arm_config": {"family": "SYNTH-FAM",
                                "parameters": dict(PARAMS),
                                "bookable_pairs": tmp_pairs,
                                "cost_treatment": {"primary_tier": 2.0}},
                 "arm_config_digest": None},
            ],
        },
        "trial_accounting": {"trial_budget_cells": 6, "booked_cells": 1,
                             "unbooked_cells": 5,
                             "booked_arm_ids": ["SYN-ARM1"]},
    }


def test_dry_run_plumbing_self_check_synthetic():
    pairs = ["SYN01/LEGA", "SYN02/LEGB"]
    fz = synthetic_freeze(pairs)
    for arm in fz["section2_arm_plan"]["arms"]:
        from research.assets.commodities_ng1.runners.dry_run import (
            arm_config_digest,
        )
        arm["arm_config_digest"] = arm_config_digest(arm["arm_config"])
    reps = tuesdays(date(2018, 1, 2), 60)

    def cot_loader():
        out = {}
        for code in ("SYN01", "SYN02"):
            out[code] = [{"report_date": d, "open_interest": 1000,
                          "noncomm_long": 100 + (d.day ^ 63) % 700,
                          "noncomm_short": 50,
                          "noncomm_spreading": 0, "comm_long": 20,
                          "comm_short": 30}
                         for d in reps]
        return out

    sessions = weekday_sessions(date(2017, 12, 1), 70)
    closes = synthetic_closes(sessions)

    def etp_loader(symbol):
        return list(sessions), dict(closes), set()

    out = plumbing_self_check(fz, cot_loader, etp_loader, pairs=None,
                              p2_per_pair_census=None)
    assert out["bookable_pair_count"] == 2
    assert out["all_digests_match"] is True
    for pid, v in out["per_pair"].items():
        assert v["counted_instants"] == 8        # 60 - 52 warmup
        assert v["chain_rows"] == 60
        assert v["arm_decision_counts"][0]["counted_instants"] == 8
        assert v["arm_decision_counts"][0]["held_decision_count"] \
            + v["arm_decision_counts"][0]["flat_decision_count"] == 8
    assert out["pooled_counted_instants"] == 16
    # no-PnL law: no KEY anywhere carries outcome vocabulary
    def keys_of(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield str(k)
                yield from keys_of(v)
        elif isinstance(o, (list, tuple)):
            for v in o:
                yield from keys_of(v)
    banned = ("pnl", "expectancy", "edge", "profit_factor")
    assert not any(b in k.lower() for k in keys_of(out) for b in banned)
    assert_structural(out)


def test_dry_run_census_identity_on_synthetic_census():
    pairs = ["SYN01/LEGA"]
    fz = synthetic_freeze(pairs)
    from research.assets.commodities_ng1.runners.dry_run import (
        arm_config_digest,
    )
    fz["section2_arm_plan"]["arms"][0]["arm_config_digest"] = \
        arm_config_digest(fz["section2_arm_plan"]["arms"][0]["arm_config"])
    reps = tuesdays(date(2018, 1, 2), 60)

    def cot_loader():
        return {"SYN01": [{"report_date": d, "open_interest": 1000,
                           "noncomm_long": 100, "noncomm_short": 50,
                           "noncomm_spreading": 0, "comm_long": 20,
                           "comm_short": 30} for d in reps]}

    sessions = weekday_sessions(date(2017, 12, 1), 70)
    chain = build_pair_chain(cot_loader()["SYN01"], sessions,
                             synthetic_closes(sessions))
    window_rows = [i for i, r in enumerate(chain["rows"])
                   if r["release_date"] >= date(2018, 1, 1)]
    counted_window = window_rows[52:]
    mapped = [i for i in counted_window
              if chain["rows"][i]["decision_session"] is not None]
    census = {"SYN01/LEGA": {"floor_evaluation": {
        "counted_expected_releases": len(counted_window),
        "grid_eligible_instants": len(mapped),
        "counted_first_release":
            chain["rows"][mapped[0]]["release_date"].isoformat(),
        "counted_last_release":
            chain["rows"][counted_window[-1]]["release_date"].isoformat(),
        "unmapped_release_dates_counted": [],
    }}}

    def etp_loader(symbol):
        return list(sessions), synthetic_closes(sessions), set()

    out = plumbing_self_check(fz, cot_loader, etp_loader,
                              p2_per_pair_census=census)
    assert out["per_pair"]["SYN01/LEGA"]["census_identity_verified"] is True


def test_no_pnl_law_scanner():
    assert_structural({"a": {"b": [1, 2, {"c": "x"}]}})
    with pytest.raises(ValueError, match="no-PnL"):
        assert_structural({"net_pnl": 1.0})
    with pytest.raises(ValueError, match="no-PnL"):
        assert_structural({"results": [{"expectancy": 0.1}]})
    with pytest.raises(ValueError, match="no-PnL"):
        assert_structural({"GROSS": 1.0})


# ----------------------------------------------------------------------- #
# 11. Frozen laws carried verbatim
# ----------------------------------------------------------------------- #

def test_shifted_release_k_frozen_at_4():
    from research.assets.commodities_ng1.runners import battery
    assert battery.SHIFTED_RELEASE_K_FROZEN == 4
    assert battery.KILLER_ROLES == ("PRICE_ONLY_SHADOW",
                                    "RELEASE_CLOCK_SHADOW",
                                    "SHIFTED_RELEASE_PLACEBO")
    assert battery.Q11_MIN_ELIGIBLE_PER_PAIR == 300
    assert battery.Q11_MIN_ELIGIBLE_POOLED == 3300


def test_freeze_battery_binding_present():
    """The implemented battery matches the binding freeze section6."""
    with open(os.path.join(RUN_DIR, "s", "selection_freeze.json"),
              encoding="utf-8") as fh:
        freeze = json.load(fh)
    sec6 = freeze["section6_i_phase_control_battery_binding"]
    roles = [c["role"] for c in sec6["mandatory_controls"]]
    assert roles == ["PRICE_ONLY_SHADOW", "RELEASE_CLOCK_SHADOW",
                     "SHIFTED_RELEASE_PLACEBO"]
    placebo = [c for c in sec6["mandatory_controls"]
               if c["role"] == "SHIFTED_RELEASE_PLACEBO"][0]
    assert placebo["stale_releases_k"] == 4
    killers = sec6["falsification_rule_binding"]["killer_controls"]
    assert tuple(killers) == (
        "PRICE_ONLY_SHADOW", "RELEASE_CLOCK_SHADOW",
        "SHIFTED_RELEASE_PLACEBO")
    # frozen folds identical to the scaffolding's folds
    frozen = [(f["fold_id"], f["release_date_start"],
               f["release_date_end"])
              for f in freeze["section3_stage_a_rules_r1_r6"]
              ["folds_frozen"]]
    assert frozen == [(f["fold_id"], f["release_date_start"],
                       f["release_date_end"]) for f in FOLDS_FROZEN]


# ----------------------------------------------------------------------- #
# 13. Z-R1 remediation: empty booked population -> DECLARED NOT_EXECUTABLE
# ----------------------------------------------------------------------- #

def test_book_ledger_empty_population_declared_not_executable(monkeypatch):
    """The Z-report defect class: an empty booked population must be a
    DECLARED NOT_EXECUTABLE verdict row -- the kernel book and the ROOT
    reconciliation are never invoked on an empty ledger (invoking them
    crashed with TypeError ending_equity=None at the Z dry-run: the
    RELEASE_CLOCK_SHADOW single lifetime trade excluded by the
    split-boundary law left an EMPTY booked population)."""
    def _refuse(*a, **k):
        raise AssertionError("kernel invoked on an empty booked population")
    monkeypatch.setattr(KX, "dual_book_ledger", _refuse)
    monkeypatch.setattr(KX, "reconcile_ledger", _refuse)
    booked = book_ledger([], leg_constants(),
                         empty_reason="all booked trades excluded by the "
                                      "split-boundary law",
                         excluded_trades=1)
    assert booked["verdict"] == "NOT_EXECUTABLE"
    assert booked["declared"] is True
    assert booked["outcome_class"] == "EMPTY_BOOKED_POPULATION"
    assert booked["booked_trades"] == 0
    assert booked["excluded_trades"] == 1
    assert "split-boundary" in booked["reason"]
    assert booked["kernel_book"] is None
    assert booked["reconciliation"] is None
    assert booked["disclosure"]      # reason disclosure present
    # the no-PnL key law holds on the declared row
    assert_structural(booked)
    # the constructor itself declares (never a silent pass either way)
    d = empty_booked_population_verdict("synthetic reason",
                                        excluded_trades=0)
    assert d["verdict"] == "NOT_EXECUTABLE" and d["declared"] is True
    assert d["excluded_trades"] == 0


def test_book_ledger_nonempty_path_shape_unchanged():
    """Non-empty booking path unchanged: the same
    {schema, ledger, reconciliation} shape with a reconciled identity."""
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = dict(synthetic_closes(sessions))
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 20)] = 90.0
    chain = counted_chain(MONDAYS, RELEASES)
    res = decision_trades(chain, [1.0, 1.0, 0.0, 0.0], "TESTLEG",
                          sessions, closes)
    assert len(res["trades"]) == 1
    booked = book_ledger(res["trades"], leg_constants())
    assert set(booked) == {"schema", "ledger", "reconciliation"}
    assert booked["reconciliation"]["identity_ok"] is True
    assert booked["ledger"]["trades"] == 1


def test_release_clock_single_trade_boundary_exclusion_declares_not_executable():
    """The Z-incident scenario end-to-end on synthetic data: a fixed-sign
    RELEASE_CLOCK_SHADOW books exactly ONE lifetime trade; it spans a
    committed share-base boundary and the split-boundary law excludes it
    -- the empty booked population declares NOT_EXECUTABLE (no crash)
    and the verdict propagates to the control verdict row."""
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = dict(synthetic_closes(sessions))
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 27)] = 95.0
    chain = counted_chain(MONDAYS, RELEASES)
    clock = release_clock_positions(len(chain["rows"]))  # fixed +1 forever
    res = decision_trades(chain, clock, "TESTLEG", sessions, closes,
                          split_boundary_dates={date(2020, 1, 15)})
    assert res["trades"] == []              # the EMPTY booked population
    assert len(res["split_boundary_excluded"]) == 1
    booked = book_ledger(
        res["trades"], leg_constants(),
        empty_reason="every booked trade excluded by the split-boundary "
                     "law (the single lifetime clock trade spans a "
                     "share-base boundary)",
        excluded_trades=len(res["split_boundary_excluded"]))
    assert booked["verdict"] == "NOT_EXECUTABLE"   # declared, no exception
    assert booked["excluded_trades"] == 1
    row = control_verdict_row(booked)
    assert row["verdict"] == "NOT_EXECUTABLE"      # propagates verbatim
    assert row["declared"] is True
    assert row["reason"] == booked["reason"]
    assert_structural(row)


def test_control_verdict_rows_propagation_and_fail_closed():
    """Control verdict rows: an executed book PASSes on a reconciled
    identity; a broken identity FAILs (fail-closed, never silent); the
    DECLARED NOT_EXECUTABLE book propagates through the battery-level
    per-role rows."""
    sessions = weekday_sessions(date(2019, 12, 2), 8)
    closes = dict(synthetic_closes(sessions))
    closes[date(2020, 1, 6)] = 100.0
    closes[date(2020, 1, 20)] = 90.0
    chain = counted_chain(MONDAYS, RELEASES)
    res = decision_trades(chain, [1.0, 1.0, 0.0, 0.0], "TESTLEG",
                          sessions, closes)
    executed = book_ledger(res["trades"], leg_constants())
    ok_row = control_verdict_row(executed)
    assert ok_row["verdict"] == "PASS" and ok_row["declared"] is False
    assert ok_row["booked_trades"] == 1
    # a broken reconciliation identity is FAIL -- never silent
    broken = {"schema": executed["schema"],
              "ledger": executed["ledger"],
              "reconciliation": dict(executed["reconciliation"],
                                     identity_ok=False)}
    assert control_verdict_row(broken)["verdict"] == "FAIL"
    # per-role rows: an executed role and a declared role side by side
    declared = empty_booked_population_verdict(
        "synthetic: no trade survived the split-boundary exclusion",
        excluded_trades=1)
    rows = control_verdict_rows({"ANCHOR": executed,
                                 "RELEASE_CLOCK_SHADOW": declared})
    assert rows["ANCHOR"]["verdict"] == "PASS"
    assert rows["RELEASE_CLOCK_SHADOW"]["verdict"] == "NOT_EXECUTABLE"
    assert rows["RELEASE_CLOCK_SHADOW"]["excluded_trades"] == 1
    assert rows["RELEASE_CLOCK_SHADOW"]["declared"] is True
    for r in rows.values():
        assert_structural(r)
