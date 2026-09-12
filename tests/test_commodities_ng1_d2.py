"""COMMODITIES-NG1 D2 novelty-measurement tests (task
commodities-ng1-d2-novelty).

Laws under test
---------------
1. Correlation core: Spearman/Pearson against HAND-COMPUTED values on tiny
   known series (perfect +/-1, the exact 8-point case 39/42 and
   1 - 18/504, average-rank ties).
2. Tail-bucket and holding semantics: percentile-rank tails and the
   hold-for-h/latest-arm-wins law, hand-derived on synthetic series.
3. Anchor decision-state machines (A4-P1 reversal, A4-P2 carry-until-
   trigger, A5-P1 disagreement cells, A5-P2 acceleration tails) and the
   price-only shadow analogues, on hand-computed synthetic chains.
4. Verdict law: pooled |rho| <= 0.20 = ELIGIBLE else VETO; any
   UNMEASURABLE shadow => VETO_PENDING_UNMEASURABLE (fail-closed,
   never-PASS-by-absence); margin to ceiling recorded (P-2).
5. Committed panel (commit-2 artifact, skipped when absent): schema,
   verdict recomputation from the recorded shadow rows, digest pins of
   every consumed input, pair universe identity with the proposals'
   declared bookable set, counted-instant identity with the P2 census,
   and a NO-OUTCOME vocabulary scan (decision states only, no PnL).
6. P-12 negative test: the commit-1 files contain NO measured rho values
   (targeted regex + AST scan; the scanner itself is tested against
   violating fixtures).  The declared ceiling constant is the only
   permitted rho-family number and is whitelisted by name.

No returns are computed anywhere; conditional states only.
"""

from __future__ import annotations

import ast
import json
import math
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

WORKTREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKTREE))

D2_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run" / "d2"
sys.path.insert(0, str(D2_DIR))

import measure_novelty as MN  # noqa: E402

RUN_DIR = WORKTREE / "research" / "control" / "commodities_ng1_run"
PANEL_PATH = D2_DIR / "d2_novelty_panel.json"
P2_PATH = RUN_DIR / "p2_gate.json"
COT_PATH = RUN_DIR / "p0_cot_weekly_targets.csv"

SHADOW_KEYS = ("momentum_63s", "generic_dow_tue", "v16_close_displace_fade",
               "price_only_shadow")
VERDICTS = {"ELIGIBLE", "VETO", "VETO_PENDING_UNMEASURABLE"}


# ----------------------------------------------------------------------- #
# fixtures / helpers
# ----------------------------------------------------------------------- #

@pytest.fixture
def small_params():
    """Swap the frozen parameters for small hand-checkable values; restore
    afterwards.  (The production run always uses the frozen values.)"""
    saved = {k: dict(v) for k, v in MN.FROZEN_PARAMETERS.items()}
    MN.FROZEN_PARAMETERS.update({
        "percentile_window_weeks": {"value": 4},
        "tail_cut": {"value": 0.25},
        "holding_weeks_a4_reversal": {"value": 2},
        "carry_bound_weeks_a4p2": {"value": 13},
        "trigger_tau_geometry": {"value": 0.05},
        "accel_window_weeks_a5p2": {"value": 1},
        "holding_weeks_a5p2": {"value": 2},
        "tau_price_weekly_a4p2": {"value": 0.02},
    })
    yield
    MN.FROZEN_PARAMETERS.clear()
    MN.FROZEN_PARAMETERS.update(saved)


def mk_rows(g=None, spec=None, comm=None, cend=None, oi=None, n=None):
    """Synthetic chain rows in the measure_novelty row shape."""
    series = [s for s in (g, spec, comm, cend, oi) if s is not None]
    if n is None:
        n = max((len(s) for s in series), default=0)
    w_acc = int(MN.P("accel_window_weeks_a5p2"))
    rows = []
    for i in range(n):
        cn = comm[i] if comm else 50.0
        oi_v = oi[i] if oi else 100.0
        rows.append({
            "report_date": date(2016, 1, 4) + timedelta(weeks=i),
            "release_instant": None,
            "release_date": date(2016, 1, 8) + timedelta(weeks=i),
            "rule_source": "test",
            "decision_session": None,
            "g": g[i] if g else 0.0,
            "spec_net": spec[i] if spec else 100.0,
            "comm_net": cn,
            "open_interest": oi_v,
            "accel": None,
            "cend_close": cend[i] if cend else None,
        })
    if comm is not None:
        for i in range(2 * w_acc, n):
            rows[i]["accel"] = (rows[i]["comm_net"]
                                - 2.0 * rows[i - w_acc]["comm_net"]
                                + rows[i - 2 * w_acc]["comm_net"]) \
                / rows[i]["open_interest"]
    return rows


# ----------------------------------------------------------------------- #
# 1. correlation core (hand-computed)
# ----------------------------------------------------------------------- #

def test_pearson_perfect_and_inverse():
    assert MN.pearson([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == pytest.approx(1.0)
    assert MN.pearson([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == pytest.approx(-1.0)


def test_pearson_exact_eight_point_case():
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    y = [1, 3, 2, 4, 6, 5, 8, 7]
    # hand: sum dx*dy = 39, sum dx^2 = sum dy^2 = 42 -> 39/42
    assert MN.pearson(x, y) == pytest.approx(39.0 / 42.0)


def test_spearman_exact_eight_point_case():
    x = [1, 2, 3, 4, 5, 6, 7, 8]
    y = [1, 3, 2, 4, 6, 5, 8, 7]
    # y is a permutation of 1..8, so its ranks are itself; d = [0,-1,1,0,
    # -1,1,-1,1] -> sum d^2 = 6 -> 1 - 36/504 = 39/42 (ties-free case,
    # so the closed form must equal Pearson on the raw values)
    assert MN.spearman(x, y) == pytest.approx(1.0 - 36.0 / 504.0)
    assert MN.spearman(x, y) == pytest.approx(39.0 / 42.0)


def test_spearman_average_rank_ties():
    x = [1, 2, 2, 4]
    y = [1, 3, 5, 7]
    # ranks x = [1, 2.5, 2.5, 4]; hand Pearson on ranks = 4.5/sqrt(4.5*5)
    assert MN.average_ranks(x) == [1.0, 2.5, 2.5, 4.0]
    assert MN.spearman(x, y) == pytest.approx(4.5 / math.sqrt(4.5 * 5.0))


def test_pearson_ties_hand_computed():
    x = [1, 2, 2, 4]
    y = [1, 3, 5, 7]
    # hand: 9/sqrt(4.75*20)
    assert MN.pearson(x, y) == pytest.approx(9.0 / math.sqrt(95.0))


def test_degenerate_series_return_none():
    assert MN.pearson([1, 1, 1], [1, 2, 3]) is None
    assert MN.spearman([1, 1, 1], [1, 2, 3]) is None
    sp, pe = MN.correlation_pair([1.0], [2.0])
    assert sp is None and pe is None
    sp, pe = MN.correlation_pair([], [])
    assert sp is None and pe is None


# ----------------------------------------------------------------------- #
# 2. percentile tails + holding law (hand-derived)
# ----------------------------------------------------------------------- #

def test_percentile_tail_lo_hi_and_none():
    cut = 0.25
    # unique maximum: rank 1.0 -> hi
    assert MN.percentile_tail([1, 2, 3, 4], 3, 4, cut) == "hi"
    # unique minimum: rank 1/4 <= 0.25 -> lo
    assert MN.percentile_tail([5, 6, 7, 1], 3, 4, cut) == "lo"
    # mid: rank 0.5 -> None
    assert MN.percentile_tail([4, 4, 1, 2], 3, 4, cut) is None
    # tied maximum cluster at the evaluated point: rank 4/4 -> hi
    assert MN.percentile_tail([2, 4, 4, 4], 3, 4, cut) == "hi"
    # tied minimum cluster: rank 3/4 -> hi?? no: x=2 is the max there;
    # a tied-minimum cluster evaluates LO only at its own value:
    assert MN.percentile_tail([4, 4, 4, 2], 3, 4, cut) == "lo"
    # rank exactly at both cuts only when cut >= 0.5 -> degenerate refusal
    assert MN.percentile_tail([2, 1], 1, 2, 0.5) is None
    # insufficient history -> None
    assert MN.percentile_tail([1, 2, 3, 4], 1, 4, cut) is None


def test_hold_positions_latest_arm_wins():
    arm = [1.0, 0.0, 0.0, -1.0, 0.0]
    assert MN.hold_positions(arm, 2) == [1.0, 1.0, 0.0, -1.0, -1.0]
    assert MN.hold_positions(arm, 1) == [1.0, 0.0, 0.0, -1.0, 0.0]
    assert MN.hold_positions(arm, 4) == [1.0, 1.0, 1.0, -1.0, -1.0]


# ----------------------------------------------------------------------- #
# 3. anchor decision-state machines (synthetic, hand-computed)
# ----------------------------------------------------------------------- #

def test_state_a4p1_reversal_arms_and_holds(small_params):
    g = [10, 10, 10, 10, 1, 1, 10, 10, 10, 10, 1, 1, 10]
    rows = mk_rows(g=g)
    pos = MN.state_a4p1(rows)
    # hand-derived (percentile window 4 needs i>=3):
    #   i3: [10,10,10,10] rank 1.0 -> hi arm -1
    #   i4: [10,10,10,1] rank 0.25 -> lo arm +1; i5: rank 0.5 mid
    #   i6: [10,1,1,10] rank 0.75 -> hi arm -1; i7..i9: rank 1.0 hi
    #   i10: lo arm +1; i11 mid; i12: rank 0.75 hi arm -1
    # h=2, latest arm wins
    assert pos == [0.0, 0.0, 0.0, -1.0, 1.0, 1.0, -1.0, -1.0, -1.0,
                   -1.0, 1.0, 1.0, -1.0]


def test_state_a4p2_entry_hold_and_tail_exit(small_params):
    g = [0.10, 0.12, 0.08, 0.11, 0.30, 0.32, 0.31, 0.33, 0.31, 0.315]
    spec = [100.0] * 10
    rows = mk_rows(g=g, spec=spec)
    pos = MN.state_a4p2(rows)
    # hand-derived (window 4 -> first full window at i=3; the evaluated
    # value is INSIDE its own window):
    #   i3: [0.10,0.12,0.08,0.11] rank 4/4 -> hi, transition -> enter +1
    #   i4..i7: rank 1.0 hi, |weekly flow| < tau=0.05 -> hold
    #   i8: [0.32,0.31,0.33,0.31] x=0.31 rank 2/4 -> mid -> exit
    #   i9: [0.31,0.33,0.31,0.315] x=0.315 rank 3/4 -> hi, fresh
    #       transition (prev mid) -> re-enter +1
    assert pos[0] == 0.0 and pos[1] == 0.0 and pos[2] == 0.0
    assert pos[3] == 1.0 and pos[4] == 1.0 and pos[5] == 1.0
    assert pos[6] == 1.0 and pos[7] == 1.0
    assert pos[8] == 0.0 and pos[9] == 1.0


def test_state_a4p2_bound_exit_and_no_instant_rearm(small_params):
    # constant hi-tail run: bound h_max = 13 -> held i3..i15 (entry i3 +
    # 12), exit at i16; re-arm requires leaving the tail (never instant).
    g = [0.30] * 30
    spec = [100.0] * 30
    rows = mk_rows(g=g, spec=spec)
    pos = MN.state_a4p2(rows)
    for i in range(0, 3):
        assert pos[i] == 0.0, f"instant {i}"
    for i in range(3, 16):        # 13 held instants
        assert pos[i] == 1.0, f"instant {i}"
    for i in range(16, 30):       # bound hit, no re-arm inside the tail
        assert pos[i] == 0.0, f"instant {i}"


def test_state_a5p1_disagreement_cells(small_params):
    cend = [100.0, 99.0, 101.0, 90.0, 90.0]
    spec = [100.0, 110.0, 120.0, 120.0, 100.0]
    rows = mk_rows(spec=spec, cend=cend)
    pos = MN.state_a5p1(rows)
    # i=0: no prior -> None
    assert pos[0] is None
    # i=1: s_flow=+1, s_price=-1 -> disagreement -> flow side +1
    assert pos[1] == 1.0
    # i=2: s_flow=+1, s_price=+1 -> agreement -> inert 0
    assert pos[2] == 0.0
    # i=3: s_flow=0 -> inert 0
    assert pos[3] == 0.0
    # i=4: s_flow=-1, s_price=0 -> inert 0
    assert pos[4] == 0.0


def test_state_a5p2_acceleration_tail_hold(small_params):
    cn = [100, 100, 100, 100, 100, 90, 100, 100, 100, 100]
    rows = mk_rows(comm=cn)
    # accel window = 1 -> accel[i] = (cn_i - 2 cn_{i-1} + cn_{i-2})/100:
    # [None, None, 0, 0, 0, -0.10, 0.20, -0.10, 0, 0]
    assert rows[5]["accel"] == pytest.approx(-0.10)
    assert rows[6]["accel"] == pytest.approx(0.20)
    pos = MN.state_a5p2(rows)
    # percentile window 4, cut 0.25 over the accel series (x inside its
    # own window):
    #   i5: [0,0,0,-0.10] rank 1/4 -> lo arm -1
    #   i6: [0,0,-0.10,0.20] rank 4/4 -> hi arm +1
    #   i7: [0,-0.10,0.20,-0.10] rank 2/4 -> mid
    #   i8: [-0.10,0.20,-0.10,0] rank 3/4 -> hi arm +1
    #   i9: [0.20,-0.10,0,0] rank 3/4 -> hi arm +1
    # h=2, latest arm wins:
    assert pos == [0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 1.0, 1.0, 1.0, 1.0]


# ----------------------------------------------------------------------- #
# 3b. shadows (synthetic, hand-computed)
# ----------------------------------------------------------------------- #

def _sessions(n, start=date(2000, 1, 3)):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def test_readable_bar_index():
    dates = _sessions(5)
    assert MN._readable_bar_index(dates, dates[3]) == 2
    assert MN._readable_bar_index(dates, dates[0]) is None


def test_shadow_momentum_63s_sign():
    dates = _sessions(80)
    up = [100.0 + i for i in range(80)]
    chain = mk_rows(n=5)
    for row in chain:
        row["decision_session"] = dates[79]
    pos = MN.shadow_momentum_63s(chain, dates, up)
    assert pos[-1] == 1.0
    down = [100.0 - i for i in range(80)]
    pos = MN.shadow_momentum_63s(chain, dates, down)
    assert pos[-1] == -1.0


def test_shadow_v16_fade_sign():
    dates = _sessions(20)
    up = [100.0 + i for i in range(20)]
    chain = mk_rows(n=5)
    for row in chain:
        row["decision_session"] = dates[19]
    pos = MN.shadow_v16_close_displace_fade(chain, dates, up)
    assert pos[-1] == -1.0          # fades the up-move
    down = [100.0 - i for i in range(20)]
    pos = MN.shadow_v16_close_displace_fade(chain, dates, down)
    assert pos[-1] == 1.0


def test_shadow_generic_dow_tue():
    chain = mk_rows(n=3)
    chain[0]["decision_session"] = date(2026, 1, 5)   # Monday
    chain[1]["decision_session"] = date(2026, 1, 6)   # Tuesday (shifted)
    chain[2]["decision_session"] = None               # unmapped
    pos = MN.shadow_generic_dow_tue(chain)
    assert pos[0] == 1.0
    assert pos[1] == -1.0
    assert pos[2] is None


def test_shadow_price_a4p1_mirror_of_anchor(small_params):
    cend = [100.0, 100.0, 100.0, 100.0, 90.0, 90.0, 100.0, 100.0,
            100.0, 100.0, 90.0, 90.0, 100.0]
    rows = mk_rows(cend=cend)
    pos = MN.shadow_price_a4p1(rows)
    # displacement over w=4; percentile window 4 needs i>=7 for full
    # history.  Hand-derived arms (cut 0.25):
    #   i7: disp [-.10,-.10,+.111,0] x=0 rank 0.75 -> hi arm -1
    #   i8: rank 0.75 -> hi; i9: rank 1.0 -> hi
    #   i10: x=-.10 rank 0.25 -> lo arm +1; i11: rank 0.5 mid
    #   i12: x=+.111 rank 0.75 -> hi arm -1;  h=2 latest arm wins
    assert pos[4] == 0.0 and pos[5] == 0.0 and pos[6] == 0.0
    assert pos[7] == -1.0 and pos[8] == -1.0 and pos[9] == -1.0
    assert pos[10] == 1.0 and pos[11] == 1.0
    assert pos[12] == -1.0


def test_shadow_price_a4p2_persistence_trigger(small_params):
    # entry on hi-tail transition, HELD while no opposing weekly move,
    # EXIT on a weekly displacement beyond tau=0.02 opposing the hold,
    # then a fresh entry on the transition into the opposite tail.
    cend = [100.0, 15.0, 100.0, 100.0, 102.0, 15.3, 102.0, 210.0,
            210.0, 203.7, 203.7]
    rows = mk_rows(cend=cend)
    pos = MN.shadow_price_a4p2(rows)
    # disp: i4..i6 = 0.02 (insufficient percentile history -> None),
    # i7 = 210/100-1 = 1.10, rank 1.0 in [0.02,0.02,0.02,1.10] -> hi enter
    assert pos[7] == 1.0
    # i8: disp 210/102-1 = 1.0588, rank 3/4 -> hi; week = 210/210-1 = 0
    # -> no trigger -> held
    assert pos[8] == 1.0
    # i9: disp 203.7/15.3-1 = 13.3137, rank 1.0 -> hi; week = 203.7/210-1
    # = -0.03 opposing the +1 hold beyond tau -> trigger exit; and no
    # instant re-arm while the bucket stays hi
    assert pos[9] == 0.0
    # i10: disp 203.7/102-1 = 0.9971, rank 1/4 -> lo; transition hi->lo
    # -> fresh entry on the carry side of the lo tail (-1)
    assert pos[10] == -1.0


def test_shadow_price_a5p1_price_only_cells(small_params):
    cend = [100.0, 101.0, 100.0, 99.0]
    rows = mk_rows(cend=cend)
    pos = MN.shadow_price_a5p1(rows)
    assert pos[0] is None and pos[1] is None
    # i=2: now=-1 vs prev=+1 -> disagreement, direction by recent side -1
    assert pos[2] == -1.0
    # i=3: now=-1, prev=-1 -> agreement -> 0
    assert pos[3] == 0.0


def test_shadow_price_a5p2_acceleration_tail(small_params):
    # widen the accel window to 2 grid steps for this case (restored by
    # the small_params fixture teardown)
    MN.FROZEN_PARAMETERS["accel_window_weeks_a5p2"] = {"value": 2}
    cend = [100.0] * 4 + [110.0] * 4 + [100.0] * 4 + [110.0] * 4
    rows = mk_rows(cend=cend)
    pos = MN.shadow_price_a5p2(rows)
    # accel window 2: accel[i] = (c_i - 2 c_{i-2} + c_{i-4})/c_i for i>=4:
    #   [.,.,.,., +.0909, +.0909, -.0909, -.0909, -.1, -.1, +.1, +.1,
    #    +.0909, +.0909, -.0909, -.0909]
    # percentile window 4, cut 0.25 (x inside its own window):
    #   i8: [-.0909 tail...] x=-.1 rank 1/4 -> lo arm -1; i9: rank 1/2 mid
    #   i10: x=+.1 rank 4/4 -> hi arm +1; i11: rank 4/4 -> hi arm +1
    #   i12: rank 1/2 mid; i13: rank 1/2 mid
    #   i14: x=-.0909 rank 1/4 -> lo arm -1; i15: rank 1/2 mid
    # h=2, latest arm wins:
    assert pos == [0.0] * 8 + [-1.0, -1.0, 1.0, 1.0, 1.0, 0.0, -1.0, -1.0]


# ----------------------------------------------------------------------- #
# 3c. pair observation + shadow evaluation mechanics
# ----------------------------------------------------------------------- #

def test_pair_observations_pairwise_complete():
    counted = [True, True, True, False]
    anchor = [1.0, None, -1.0, 1.0]
    shadow = [1.0, 1.0, None, -1.0]
    obs = MN.pair_observations(anchor, shadow, counted)
    assert obs == [(1.0, 1.0)]


def test_evaluate_shadow_unmeasurable_when_degenerate():
    anchor = {"p1": [1.0, 1.0, 1.0]}
    shadow = {"p1": [1.0, 1.0, 1.0]}
    counted = {"p1": [True, True, True]}
    row = MN.evaluate_shadow(anchor, shadow, counted)
    assert row["status"] == "UNMEASURABLE"
    assert row["pooled_abs_rho"] is None
    assert row["n_obs_total"] == 3


def test_evaluate_shadow_measured_pooled_formula():
    anchor = {"p1": [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 0.0, 0.0],
              "p2": [0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0]}
    shadow = {"p1": [1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 0.0, 0.0],
              "p2": [0.0, 1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0]}
    counted = {"p1": [True] * 8, "p2": [True] * 8}
    row = MN.evaluate_shadow(anchor, shadow, counted)
    assert row["status"] == "MEASURED"
    # p2 is identity -> its own correlation is exactly +1
    assert row["per_pair"][1]["spearman"] == pytest.approx(1.0)
    assert row["per_pair"][1]["pearson"] == pytest.approx(1.0)
    # pooled stacks both pairs' observations (16 obs); the p1 mismatches
    # dilute the identity pair, so the pooled rho is strictly inside
    # (-1, 1) but the identity contribution keeps it strongly positive
    assert row["n_obs_total"] == 16
    assert 0.3 < row["pooled_abs_rho"] < 1.0
    assert row["pooled_abs_rho"] == pytest.approx(
        max(abs(row["spearman_pooled"]), abs(row["pearson_pooled"])))


# ----------------------------------------------------------------------- #
# 4. verdict law (fail-closed)
# ----------------------------------------------------------------------- #

def _shadow_row(pooled):
    return {"status": "MEASURED", "pooled_abs_rho": pooled}


def test_verdict_eligible_with_margin():
    shadows = {sid: _shadow_row(0.05) for sid in SHADOW_KEYS}
    row = MN.verdict_from_shadows(shadows)
    assert row["verdict"] == "ELIGIBLE"
    assert row["proposal_pooled_abs_rho"] == pytest.approx(0.05)
    assert row["margin_to_ceiling"] == pytest.approx(0.15)
    assert row["unmeasurable_shadows"] == []


def test_verdict_veto_above_ceiling():
    values = {"momentum_63s": 0.05, "generic_dow_tue": 0.01,
              "v16_close_displace_fade": 0.02, "price_only_shadow": 0.31}
    shadows = {sid: _shadow_row(v) for sid, v in values.items()}
    row = MN.verdict_from_shadows(shadows)
    assert row["verdict"] == "VETO"
    assert row["proposal_pooled_abs_rho"] == pytest.approx(0.31)
    assert row["driving_shadow"] == "price_only_shadow"
    assert row["margin_to_ceiling"] == pytest.approx(-0.11)


def test_verdict_fail_closed_on_unmeasurable():
    shadows = {sid: _shadow_row(0.01) for sid in SHADOW_KEYS}
    shadows["generic_dow_tue"] = {"status": "UNMEASURABLE",
                                  "pooled_abs_rho": None}
    row = MN.verdict_from_shadows(shadows)
    assert row["verdict"] == "VETO_PENDING_UNMEASURABLE"
    assert row["proposal_pooled_abs_rho"] is None
    assert row["margin_to_ceiling"] is None
    assert row["unmeasurable_shadows"] == ["generic_dow_tue"]


def test_ceiling_matches_dispatch_packet():
    assert MN.P("novelty_ceiling_abs_rho") == 0.20


# ----------------------------------------------------------------------- #
# 5. committed panel (commit-2 artifact; skipped when absent)
# ----------------------------------------------------------------------- #

requires_panel = pytest.mark.skipif(
    not PANEL_PATH.exists(), reason="d2_novelty_panel.json not yet committed "
                                    "(commit-2 artifact; P-12 order)")


def _load_panel():
    with open(PANEL_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@requires_panel
def test_panel_schema_and_header():
    panel = _load_panel()
    assert panel["schema"] == "commodities_ng1_run/d2_novelty_panel@1"
    assert panel["cycle_id"] == "COMMODITIES-NG1"
    assert panel["task_id"] == "commodities-ng1-d2-novelty"
    assert panel["base_sha"] == MN.BASE_SHA
    assert panel["branch"] == MN.BRANCH
    assert panel["ceiling"]["abs_rho_ceiling"] == 0.20
    assert set(panel["proposals"].keys()) == set(MN.PROPOSAL_IDS)


@requires_panel
def test_panel_pair_universe_matches_declared_bookable_set():
    panel = _load_panel()
    proposals = MN.load_proposals()
    assert panel["pair_universe"] == MN.bookable_pairs(proposals)
    assert len(panel["pair_universe"]) == 11


@requires_panel
def test_panel_per_shadow_pooled_formula_and_margins():
    panel = _load_panel()
    for pid, detail in panel["proposals"].items():
        assert set(detail["shadows"].keys()) == set(SHADOW_KEYS)
        pooled_vals = []
        for sid, row in detail["shadows"].items():
            if row["status"] != "MEASURED":
                assert row["pooled_abs_rho"] is None
                assert row["margin_to_ceiling"] is None
                continue
            expected = max(abs(row["spearman_pooled"]),
                           abs(row["pearson_pooled"]))
            assert row["pooled_abs_rho"] == pytest.approx(expected, abs=1e-9)
            assert row["margin_to_ceiling"] == pytest.approx(
                0.20 - row["pooled_abs_rho"], abs=1e-9)
            assert -1.0 <= row["spearman_pooled"] <= 1.0
            assert -1.0 <= row["pearson_pooled"] <= 1.0
            assert row["n_obs_total"] >= 2
            for pp in row["per_pair"]:
                assert pp["n_obs"] <= 401
                if pp["pair_measurable"]:
                    assert pp["spearman"] is not None
                    assert pp["pearson"] is not None
            pooled_vals.append(row["pooled_abs_rho"])
        assert len(pooled_vals) == len(SHADOW_KEYS)


@requires_panel
def test_panel_verdict_law_recomputed():
    panel = _load_panel()
    for pid, detail in panel["proposals"].items():
        assert detail["verdict"] in VERDICTS
        if detail["unmeasurable_shadows"]:
            assert detail["verdict"] == "VETO_PENDING_UNMEASURABLE"
            assert detail["proposal_pooled_abs_rho"] is None
        else:
            pooled = max(s["pooled_abs_rho"]
                         for s in detail["shadows"].values())
            assert detail["proposal_pooled_abs_rho"] \
                == pytest.approx(pooled)
            expected = "ELIGIBLE" if pooled <= 0.20 else "VETO"
            assert detail["verdict"] == expected
            assert detail["driving_shadow"] in SHADOW_KEYS
            assert detail["margin_to_ceiling"] == pytest.approx(
                0.20 - pooled, abs=1e-9)


@requires_panel
def test_panel_input_digests_match_disk():
    panel = _load_panel()
    inputs = panel["inputs"]
    assert inputs["p2_gate_sha256"] == _sha256(P2_PATH)
    assert inputs["cot_weekly_targets_sha256"] == _sha256(COT_PATH)
    for pid, sha in inputs["proposal_sha256"].items():
        assert sha == _sha256(RUN_DIR / "d1" / "proposals" / f"{pid}.json")
    for rel, sha in inputs["commit1_code_sha256"].items():
        assert sha == _sha256(WORKTREE / rel)
    p2 = json.loads(P2_PATH.read_text(encoding="utf-8"))
    for sym, sha in inputs["etp_eod_sha256"].items():
        assert sha == _sha256(RUN_DIR / "etp_eod" / f"{sym}.csv")
        assert sha == p2["substrate_pins"]["etp_eod_sha256"][sym]


@requires_panel
def test_panel_counted_instants_match_p2_census():
    panel = _load_panel()
    p2 = json.loads(P2_PATH.read_text(encoding="utf-8"))
    for pid, detail in panel["proposals"].items():
        for sid, row in detail["shadows"].items():
            for pp in row["per_pair"]:
                ref = p2["per_pair_census"][pp["pair"]]["floor_evaluation"]
                assert pp["n_obs"] <= ref["grid_eligible_instants"]


@requires_panel
def test_panel_no_outcome_vocabulary():
    banned = ("pnl", "profit", "sharpe", "drawdown", "expectancy",
              "return_", "returns")
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                assert not any(b in str(k).lower() for b in banned), \
                    f"outcome vocabulary key at {path}/{k}"
                walk(v, f"{path}/{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
    walk(_load_panel(), "panel")


@requires_panel
def test_panel_release_clock_shadow_measured_not_absent():
    # never-PASS-by-absence: the calendar shadow must be MEASURED (the
    # weekly grid admits holiday-shifted weekday variation) or the whole
    # proposal must be VETO-pending.
    panel = _load_panel()
    for pid, detail in panel["proposals"].items():
        row = detail["shadows"]["generic_dow_tue"]
        if detail["verdict"] != "VETO_PENDING_UNMEASURABLE":
            assert row["status"] == "MEASURED", (
                "generic_dow_tue unmeasured but proposal not veto-pending")


# ----------------------------------------------------------------------- #
# 6. P-12 negative test: commit-1 files contain no measured rho values
# ----------------------------------------------------------------------- #

RESULT_KEY_PATTERN = re.compile(
    r"[\"']?(pooled_abs_rho|spearman_pooled|pearson_pooled|"
    r"proposal_pooled_abs_rho)[\"']?\s*[:=]\s*[\"']?-?\d")


def test_negative_scan_regex_detects_violations():
    violating = ('{"pooled_abs_rho": 0.31}', "spearman_pooled = 0.123",
                 "'pearson_pooled':-0.9")
    for text in violating:
        assert RESULT_KEY_PATTERN.search(text), text
    clean = ['"pooled_abs_rho": round(max(abs(sp), abs(pe)), 12)',
             '"spearman_pooled": sp_p', "ceiling = 0.20",
             '"novelty_ceiling_abs_rho": {"value": 0.20}']
    for text in clean:
        assert not RESULT_KEY_PATTERN.search(text), text


def test_commit1_files_contain_no_rho_values():
    for rel in MN.COMMIT1_FILES:
        path = WORKTREE / rel
        assert path.exists(), f"commit-1 artifact missing: {rel}"
        text = path.read_text(encoding="utf-8")
        assert not RESULT_KEY_PATTERN.search(text), \
            f"measured rho value pattern found in commit-1 file {rel}"


def test_feasibility_renote_has_no_correlation_keys():
    renote = json.loads((D2_DIR / "feasibility_renote.json")
                        .read_text(encoding="utf-8"))
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                assert not any(t in str(k).lower()
                               for t in ("rho", "spearman", "pearson",
                                         "correlation")), k
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(renote)


def test_measure_module_has_no_numeric_rho_binding():
    source = (WORKTREE / MN.COMMIT1_FILES[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) \
                else [node.target]
            for tgt in targets:
                name = getattr(tgt, "id", None)
                if name and "rho" in name.lower() \
                        and "ceiling" not in name.lower():
                    assert not isinstance(node.value, ast.Constant) or \
                        not isinstance(node.value.value, (int, float)), \
                        f"numeric binding to rho-name {name}"


def test_panel_is_not_a_commit1_file():
    assert "d2_novelty_panel.json" not in " ".join(MN.COMMIT1_FILES)


# ----------------------------------------------------------------------- #
# 5b. real-substrate plumbing (no rho): grid identity on one real pair
# ----------------------------------------------------------------------- #

def test_real_pair_grid_identity_with_p2_census():
    p2 = MN.load_p2_gate()
    pair_id = "001602/DBA"
    cot = MN.load_cot_by_market()
    dates, closes = MN.load_etp_series("DBA")
    chain, counted = MN.build_pair_chain(pair_id, cot, dates, closes)
    assert MN.verify_pair_census(pair_id, chain, counted, p2)
    counted_n = sum(counted)
    ref = p2["per_pair_census"][pair_id]["floor_evaluation"]
    assert counted_n == ref["grid_eligible_instants"] == 401
