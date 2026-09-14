"""VOL-NG1 I-phase runner-machinery tests (task vol-ng1-i-implementation).

SYNTHETIC FIXTURES ONLY: every runner, control, evaluator and kernel
test runs on hand-computed synthetic bars / synthetic metric fixtures.
NO scored execution, NO outcome numbers on real data, NO real-data PnL
anywhere (the real-substrate step of the dry-run self-check is limited
to structural plumbing: digests, series lengths, config assembly).

Hand-computed fixtures:
- A4-P2 slope/second-difference series with EXACT expected latch states
  for the frozen m axis {2,3,4} (worked by hand in this file's
  comments);
- the kernel's degenerate compatibility round trip (notional 10_000,
  40 -> 44, 2.0% stress spread) with exact per-tier NET books;
- the cost-path control's per-tier ladder on a single hand-built round
  trip (execution scaled by tier, Q-16 path line explicit and
  tier-invariant);
- the placebo law (matched marginals, destroyed ordering, seed
  determinism);
- R1-R6 per-rule PASS/FAIL/NOT_RUN fixtures.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.assets.vol_ng1 import accounting as acc              # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca             # noqa: E402
from research.assets.vol_ng1.runners import arms as ar             # noqa: E402
from research.assets.vol_ng1.runners import battery as bat         # noqa: E402
from research.assets.vol_ng1.runners import config as cfg          # noqa: E402
from research.assets.vol_ng1.runners import dryrun as dr           # noqa: E402
from research.assets.vol_ng1.runners import evaluator as ev        # noqa: E402
from research.control.vol_ng1_run.d2 import d2_novelty as dn       # noqa: E402

SHORT, FLAT, LONG = 1.0, 0.0, -1.0
INVALID = None


# --------------------------------------------------------------------------- #
# frozen config assembly: digests, budget, folds, battery constants
# --------------------------------------------------------------------------- #
def test_digest_law_reproduces_all_six_freeze_digests():
    fz = cfg.load_selection_freeze()
    arms = cfg.assemble_arm_configs(fz)
    assert len(arms) == 6
    for aid, arm in arms.items():
        raw = json.dumps(arm["config"], sort_keys=True,
                         separators=(",", ":"), ensure_ascii=True)
        assert cfg.arm_config_digest(arm["config"]) == \
            arm["recorded_arm_config_digest"]
        import hashlib
        assert hashlib.sha256(raw.encode("utf-8")).hexdigest() == \
            arm["recorded_arm_config_digest"]
        assert arm["digest_match"] is True
    digests = [a["arm_config_digest"] for a in arms.values()]
    assert len(set(digests)) == 6


def test_budget_and_family_composition():
    arms = cfg.assemble_arm_configs()
    cells = sorted(arms.values(), key=lambda a: a["budget_cell"])
    assert [a["budget_cell"] for a in cells] == [1, 2, 3, 4, 5, 6]
    a4 = [a for a in cells if a["family_key"] == cfg.FAMILY_A4_P2]
    a5 = [a for a in cells if a["family_key"] == cfg.FAMILY_A5_P2]
    assert len(a4) == 3 and len(a5) == 3
    assert [a["config"]["latch_m_sessions"] for a in a4] == [3, 4, 2]
    assert [(a["config"]["asym_threshold"],
             a["config"]["latch_sessions"]) for a in a5] == \
        [(0.5, 2), (0.75, 3), (0.25, 1)]
    roles = sorted(a["role"] for a in cells)
    assert roles.count("ANCHOR") == 2
    assert roles.count("NEIGHBOUR_CONSERVATIVE") == 2
    assert roles.count("NEIGHBOUR_AGGRESSIVE") == 2


def test_battery_bindings_and_frozen_constants():
    fz = cfg.load_selection_freeze()
    arms = cfg.assemble_arm_configs(fz)
    binding = ["index_only_shadow", "cost_path_control",
               "calendar_clock_shadow", "placebo",
               "invalid_null_distinction", "family_falsification_rule"]
    for arm in arms.values():
        assert arm["battery_binding"] == binding
    assert cfg.CALENDAR_SHIFT_K_SESSIONS == \
        fz["i_phase_control_battery"]["controls"]["calendar_clock_shadow"][
            "calendar_shift_k_sessions"] == 5
    assert cfg.PLACEBO_SEED == \
        fz["i_phase_control_battery"]["controls"]["placebo"][
            "placebo_seed"] == 20260912
    assert cfg.COST_TIER_LADDER == (1.0, 1.5, 2.0)
    assert cfg.PRIMARY_TIER == 2.0
    assert cfg.FROZEN_COST_CONTRACT_SHA256 == \
        fz["cost_contract_binding"]["cost_contract_json_sha256"]


def test_frozen_folds_parse_from_freeze_bytes():
    fz = cfg.load_selection_freeze()
    folds = cfg.frozen_folds(fz)
    freeze_windows = [(r["fold"], tuple(r["window"]))
                      for r in fz["rule_set_r1_r6"]["frozen_folds"]]
    assert [(n, (lo.isoformat(), hi.isoformat())) for n, (lo, hi)
            in folds] == freeze_windows
    assert folds[0][1][0].isoformat() == "2019-01-24"
    assert folds[-1][1][1].isoformat() == "2026-09-10"
    assert cfg.fold_of("2020-06-15", folds) == 1
    assert cfg.fold_of("2022-06-15", folds) == 2
    assert cfg.fold_of("2025-06-15", folds) == 3
    with pytest.raises(cfg.ConfigError):
        cfg.fold_of("2018-06-15", folds)


# --------------------------------------------------------------------------- #
# A4-P2 runner: hand-computed decision series on the frozen m axis
# --------------------------------------------------------------------------- #
#: Hand-worked slope path S and its second differences (the S path is
#: RECONSTRUCTED from a chosen clean D path so every D value sits far
#: from the 0 threshold -- the latch never rides on rounding noise):
#:   S    = [0.00, 0.00, 0.02, 0.06, 0.11, 0.13, 0.10, 0.03, -0.06,
#:           -0.16]
#:   D_t  = S_t - 2 S_(t-1) + S_(t-2)
#:        = [None, None, 0.02, 0.02, 0.01, -0.03, -0.05, -0.04, -0.02,
#:           -0.01]
#: Expected latch states (trailing m valid D values, threshold 0):
#:   m=2: [N, N, N, +1, +1,  0, -1, -1, -1, -1]
#:   m=3: [N, N, N, N,  +1,  0,  0, -1, -1, -1]
#:   m=4: [N, N, N, N,  N,   0,  0,  0, -1, -1]
A4_S = [0.00, 0.00, 0.02, 0.06, 0.11, 0.13, 0.10, 0.03, -0.06, -0.16]
A4_EXPECTED = {
    2: [INVALID, INVALID, INVALID, SHORT, SHORT, FLAT, LONG, LONG, LONG,
        LONG],
    3: [INVALID, INVALID, INVALID, INVALID, SHORT, FLAT, FLAT, LONG,
        LONG, LONG],
    4: [INVALID, INVALID, INVALID, INVALID, INVALID, FLAT, FLAT, FLAT,
        LONG, LONG],
}


def _a4_hand_grid() -> list[str]:
    return dr.synthetic_sessions(10)


def _a4_hand_ctx(vix_path=None, drop_session: str | None = None) -> dict:
    dates = _a4_hand_grid()
    vix9d = {d: 100.0 for d in dates}
    vix3m = {d: 100.0 * math.exp(2.0 * s) for d, s in zip(dates, A4_S)}
    vix = {d: 20.0 for d in dates}
    if vix_path is not None:
        vix = dict(zip(dates, vix_path))
    if drop_session is not None:
        del vix9d[drop_session]
    return {
        "grid": dates,
        "index": {"VIX9D": vix9d, "VIX": vix, "VIX3M": vix3m},
        "adj": {},                     # A4 state consumes indices ONLY
        "leg_subset": ("SVXY", "UVXY", "VIXY", "VXX"),
        "proxy_leg": "VXX",
        "proxy_lookback_sessions": 21,
        "proxy_annualization": 252.0,
    }


def _a4_arm(m: int):
    return {"family_form": "slope_second_difference_regime",
            "d_threshold": 0.0, "latch_m_sessions": m,
            "leg_subset": ["SVXY", "UVXY", "VIXY", "VXX"]}


@pytest.mark.parametrize("m", [2, 3, 4])
def test_a4_hand_computed_decision_series_frozen_m_axis(m):
    runner = ar.SlopeAccelerationRunner(f"VOLNG1-A4-P2-m{m}", _a4_arm(m))
    state = runner.build_state(_a4_hand_ctx())
    got = [state[d] for d in _a4_hand_grid()]
    assert got == A4_EXPECTED[m], f"m={m}: {got}"


def test_a4_frozen_form_vix_invariance():
    """The frozen slope functional algebraically cancels the VIX close
    (S = 0.5*(ln VIX3M - ln VIX9D)); the runner consumes all three
    granted indices exactly as declared and the invariance is
    DISCLOSED, never exploited."""
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m2", _a4_arm(2))
    base = runner.build_state(_a4_hand_ctx())
    alt = runner.build_state(
        _a4_hand_ctx(vix_path=[17.0 + 3.0 * math.sin(0.7 * i)
                               for i in range(10)]))
    assert base == alt


def test_a4_missing_session_is_invalid_fail_closed():
    """A missing session is INVALID and poisons the trailing windows
    (Q-11): never coerced to flat."""
    dates = _a4_hand_grid()
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m2", _a4_arm(2))
    state = runner.build_state(_a4_hand_ctx(drop_session=dates[4]))
    got = [state[d] for d in dates]
    # D_4/D_5/D_6 invalidated by the missing S_4; D_7/D_8/D_9 recover:
    #   D_7 = 0.03 - 2*0.10 + 0.13 = -0.04; D_8 = -0.06 - 2*0.03 + 0.10
    #         = -0.02; D_9 = -0.16 - 2*(-0.06) + 0.03 = -0.01
    # m=2 states: t7 INVALID (D_6 in window), t8 [-0.02,-0.04] -> -1,
    #             t9 [-0.01,-0.02] -> -1
    assert got == [INVALID, INVALID, INVALID, SHORT, INVALID, INVALID,
                   INVALID, INVALID, LONG, LONG]


def test_a4_anchor_equals_d2_committed_builder():
    """The freeze binds the ANCHOR to the D2 frozen defaults verbatim:
    the runner state must equal the D2 committed state builder
    unchanged, on the same context."""
    syn = dr.synthetic_universe(60)
    legs = ("SVXY", "UVXY", "VIXY", "VXX")
    ctx = ar.build_context_from_raw(syn["index"], syn["raw_bars"],
                                    syn["events_by_leg"], legs)
    ctx["grid"] = ar.grid_of(ctx)
    fz = cfg.load_selection_freeze()
    anchor = next(a for a in fz["arm_configuration_plan"]["arms"]
                  if a["arm_id"] == "VOLNG1-A4-P2-ANCHOR")
    runner = ar.runner_for_arm(cfg.assemble_arm_configs(fz)[
        "VOLNG1-A4-P2-ANCHOR"])
    mine = runner.build_state(ctx)
    theirs, _meta = dn.build_a4p2_state(ctx)
    assert mine == theirs
    assert anchor["config"]["latch_m_sessions"] == 3


def test_runner_refuses_config_outside_frozen_axis():
    with pytest.raises(ar.RunnerError):
        ar.SlopeAccelerationRunner("bad", _a4_arm(5))
    with pytest.raises(ar.RunnerError):
        bad = {"family_form": "premium_state_asymmetry_short_vs_mid",
               "asym_threshold": 0.6, "latch_sessions": 2,
               "leg_subset": [], "proxy_leg_short_bucket": "VXX",
               "mid_reference_leg": "VXZ",
               "bucket_map": {"front": [], "mid": []}}
        ar.PremiumAsymmetryRunner("bad", bad)


# --------------------------------------------------------------------------- #
# A5-P2 runner: independent recomposition + D2 anchor equality
# --------------------------------------------------------------------------- #
def _indep_a5_state(vix: dict, vxx: dict, vxz: dict, dates: list[str],
                    thr: float, latch: int) -> dict:
    """Independent re-implementation of the declared A5-P2 functional
    (fresh code, same frozen formulas) for cross-checking the runner."""
    def rv(closes: dict) -> dict:
        out = {}
        for i, d in enumerate(dates):
            if i < 21:
                out[d] = None
                continue
            w = [closes[dates[i - k]] for k in range(1, 22)]
            w.append(closes[d])          # 21 prior closes + the current
            rets = [math.log(w[k + 1] / w[k]) for k in range(21)]
            out[d] = float(np.std(rets, ddof=0)) * math.sqrt(252.0)
        return out

    def z(series: dict) -> dict:
        out = {}
        hist: list = []
        for d in dates:
            v = series.get(d)
            if v is None:
                out[d] = None
                continue
            if len(hist) < 63:
                hist.append(v)
                out[d] = None
                continue
            arr = np.asarray(hist + [v], dtype=float)
            sd = float(arr.std(ddof=0))
            out[d] = None if sd == 0.0 else (float(v) - float(arr.mean())) \
                / sd
            hist.append(v)
        return out

    z_vix = z({d: vix.get(d) for d in dates})

    def spread(z_rv_side: dict) -> dict:
        out = {}
        for d in dates:
            a, b = z_vix[d], z_rv_side[d]
            out[d] = None if (a is None or b is None) else a - b
        return out

    sp_short = spread(z(rv(vxx)))
    sp_mid = spread(z(rv(vxz)))
    codes: dict = {}
    for d in dates:
        a, b = sp_short[d], sp_mid[d]
        if a is None or b is None:
            codes[d] = None
            continue
        asym = a - b
        codes[d] = SHORT if asym > thr else (
            LONG if asym < -thr else FLAT)
    out = {}
    cur = pending = None
    run = 0
    for d in dates:
        raw = codes[d]
        if raw is None:
            pending, run = None, 0
            out[d] = None
            continue
        if cur is None:
            cur = raw
        elif raw == cur:
            pending, run = None, 0
        elif raw == pending:
            run += 1
            if run >= latch:
                cur, pending, run = raw, None, 0
        else:
            pending, run = raw, 1
        out[d] = cur
    return out


@pytest.fixture(scope="module")
def syn_universe():
    return dr.synthetic_universe(180)


SYN_COST_SOURCE = dr.synthetic_universe(180)["cost_source"]


@pytest.fixture(scope="module")
def dry_out():
    return dr.run_dry_run(skip_tests=True, write_artifacts=False)


@pytest.fixture(scope="module")
def syn_ctx6(syn_universe):
    ctx = ar.build_context_from_raw(
        syn_universe["index"], syn_universe["raw_bars"],
        syn_universe["events_by_leg"],
        ("SVXY", "UVXY", "VIXY", "VXX", "VIXM", "VXZ"))
    ctx["grid"] = ar.grid_of(ctx)
    return ctx


def _a5_runner(thr: float, latch: int) -> ar.PremiumAsymmetryRunner:
    return ar.PremiumAsymmetryRunner(
        f"VOLNG1-A5-P2-{thr}-{latch}",
        {"family_form": "premium_state_asymmetry_short_vs_mid",
         "asym_threshold": thr, "latch_sessions": latch,
         "leg_subset": ["SVXY", "UVXY", "VIXY", "VXX", "VIXM", "VXZ"],
         "proxy_leg_short_bucket": "VXX", "mid_reference_leg": "VXZ",
         "bucket_map": {"front": ["VXX", "UVXY", "SVXY", "VIXY"],
                        "mid": ["VIXM", "VXZ"]}})


def test_a5_independent_recomputation_matches_runner(syn_ctx6):
    """The full A5 anchor pipeline equals a fresh independent
    implementation of the declared functional (RV proxy of the
    event-adjusted closes -> expanding z -> asymmetry -> threshold ->
    debounce latch)."""
    dates = syn_ctx6["grid"]
    runner = _a5_runner(0.5, 2)
    got = runner.build_state(syn_ctx6)
    want = _indep_a5_state(syn_ctx6["index"]["VIX"],
                           syn_ctx6["adj"]["VXX"],
                           syn_ctx6["adj"]["VXZ"], dates, 0.5, 2)
    assert got == want
    valid = [d for d in dates if got[d] is not None]
    # warmup: rv(21) + expanding-z min-history 63 must keep the early
    # grid INVALID (fail-closed, never coerced)
    assert len(valid) > 0
    assert all(got[d] is None for d in dates[:80])
    assert dates.index(valid[0]) >= 84


def test_a5_anchor_equals_d2_committed_builder(syn_ctx6):
    fz = cfg.load_selection_freeze()
    anchor = cfg.assemble_arm_configs(fz)["VOLNG1-A5-P2-ANCHOR"]
    assert (anchor["config"]["asym_threshold"],
            anchor["config"]["latch_sessions"]) == (0.5, 2)
    runner = ar.runner_for_arm(anchor)
    mine = runner.build_state(syn_ctx6)
    theirs, _meta = dn.build_a5p2_state(syn_ctx6)
    assert mine == theirs


def test_a5_neighbour_axes_change_the_state(syn_ctx6):
    anchor = _a5_runner(0.5, 2).build_state(syn_ctx6)
    strict = _a5_runner(0.75, 3).build_state(syn_ctx6)
    fast = _a5_runner(0.25, 1).build_state(syn_ctx6)
    assert anchor != strict
    assert anchor != fast
    # the INVALID pattern is determined by the warmup (rv 21 + z
    # min-history 63), NOT by the frozen axis: identical across arms
    dates = syn_ctx6["grid"]
    invalid_pattern = {d for d in dates if anchor[d] is None}
    for other in (strict, fast):
        assert {d for d in dates if other[d] is None} == invalid_pattern
    # every state is on the declared pole encoding
    for s in (anchor, strict, fast):
        assert set(v for v in s.values() if v is not None) <= \
            {SHORT, FLAT, LONG}


# --------------------------------------------------------------------------- #
# leg consumption: ONLY through the event-adjusted layer
# --------------------------------------------------------------------------- #
def test_leg_consumption_requires_event_adjusted_layer(syn_universe):
    """A 4:1 split WITHOUT an explicit event decision is an uncovered
    step: the context builder refuses (fail-closed), and WITH the
    explicit SPLIT event the adjusted series is continuous by the
    designed market ratio."""
    dates = syn_universe["dates"]
    raw = syn_universe["raw_bars"]["VXX"]
    events = syn_universe["events_by_leg"]["VXX"]
    with pytest.raises(ar.RunnerError):
        ar.build_context_from_raw(syn_universe["index"],
                                  {"VXX": raw}, {"VXX": []}, ("VXX",))
    uncovered = ca.scan_uncovered_steps(raw, [])
    assert uncovered and uncovered[0]["date"] == dates[60]
    adj = ca.event_adjusted_closes(raw, events)
    i = dates.index(dates[60])
    prev, cur = adj[dates[i - 1]], adj[dates[i]]
    # designed adjusted path is continuous by construction: the split
    # step is cancelled, leaving only the designed market move
    assert abs(cur / prev - 1.0) < 0.05
    raw_ratio = (raw[i]["close"] / raw[i - 1]["close"])
    assert 3.5 < raw_ratio < 4.5        # the mechanical 4:1 step in raw


def test_runner_refuses_leg_without_adjusted_series():
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m2", _a4_arm(2))
    ctx = _a4_hand_ctx()
    ctx["grid"] = ctx["grid"]
    ctx["adj"] = {}
    with pytest.raises(ar.RunnerError):
        ar.run_cell(runner, ctx, {})


# --------------------------------------------------------------------------- #
# V7 close+1 decision-instant law
# --------------------------------------------------------------------------- #
def test_v7_close_plus_1_no_same_bar_and_refused_tail():
    syn = dr.synthetic_universe(60)
    ctx = ar.build_context_from_raw(syn["index"], syn["raw_bars"],
                                    syn["events_by_leg"],
                                    ("SVXY", "UVXY", "VIXY", "VXX"))
    ctx["grid"] = ar.grid_of(ctx)
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m2", _a4_arm(2))
    res = ar.run_cell(runner, ctx, syn["cost_source"])
    grid = ctx["grid"]
    for row in res.decisions:
        assert row["exec_session"] == grid[grid.index(
            row["decision_session"]) + 1]      # strictly the NEXT session
    # the final grid session can never host a decision (V7)
    assert res.decisions[-1]["decision_session"] != grid[-1]
    for rt in res.round_trips:
        assert rt["exit_session"] != rt["entry_session"] or \
            rt["exit_reason"] == "forced_window_end"


# --------------------------------------------------------------------------- #
# P1 kernel: dual-book round trips, cost once per fill
# --------------------------------------------------------------------------- #
def test_kernel_degenerate_compatibility_case_hand_computed():
    rt = acc.book_round_trip(direction=1, notional_usd=10_000.0,
                             entry_price=40.0, exit_price=44.0,
                             stress_spread_frac=0.02)
    assert rt["gross_pnl_usd"] == pytest.approx(1_000.0)
    assert rt["fills"]["1.0"]["fills"] == 2
    assert rt["fills"]["1.0"]["cost_per_fill_usd"] == pytest.approx(100.0)
    assert rt["net_pnl_usd_by_tier"]["1.0"] == pytest.approx(800.0)
    assert rt["net_pnl_usd_by_tier"]["1.5"] == pytest.approx(700.0)
    assert rt["net_pnl_usd_by_tier"]["2.0"] == pytest.approx(600.0)
    ledger = acc.dual_book_ledger([rt], starting_equity=100_000.0)
    assert ledger["dual_book_equality_ok"] is True
    assert ledger["books"]["GROSS"]["ending_equity"] == \
        pytest.approx(101_000.0)
    assert ledger["books"]["NET_2.0"]["ending_equity"] == \
        pytest.approx(100_600.0)
    assert ledger["primary_book"] == "NET_2.0"


def test_kernel_refuses_scored_outcomes():
    with pytest.raises(acc.AccountingRefused):
        acc.compute_outcomes([], scored=False)
    with pytest.raises(acc.AccountingRefused):
        acc.compute_outcomes([], scored=True, market_authority="AUTHORIZED")


def test_runner_kernel_events_cost_once_per_fill(syn_ctx6, syn_universe):
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m2", _a4_arm(2))
    res = ar.run_cell(runner, syn_ctx6, syn_universe["cost_source"])
    assert res.meta["fills"] == 2 * res.meta["round_trips"]
    assert res.meta["kernel_events"] == res.meta["round_trips"]
    for kev in res.kernel_events:
        book = kev["book"]
        src = syn_universe["cost_source"][kev["leg"]]
        assert book["fills"]["2.0"]["fills"] == 2
        expect_fill = book["notional_usd"] * (src["stress_spread_frac"]
                                              / 2.0) * 2.0
        assert book["fills"]["2.0"]["cost_per_fill_usd"] == \
            pytest.approx(expect_fill)
        assert book["net_pnl_usd_by_tier"]["2.0"] == pytest.approx(
            book["gross_pnl_usd"] - 2.0 * expect_fill)
        assert kev["primary_book"] == 2.0


# --------------------------------------------------------------------------- #
# cost-path control: the measured path-cost ladder, hand-computed
# --------------------------------------------------------------------------- #
def test_cost_path_control_hand_computed_ladder():
    """One hand-built VXX round trip: notional 10_000, 40 -> 44,
    spread 2.0%, path adverse tail 12 bps/day, held 5 sessions.
      execution(t) = 2 fills x notional x 1% x t  = 200/300/400
      path line    = 10_000/1e4 x 12 bps x 5      = 60 (tier-invariant)
      net stress   = 1_000 - exec(t) - 60         = 740/640/540
    """
    rt = {"leg": "VXX", "direction": 1, "entry_session": "d0",
          "entry_price": 40.0, "exit_session": "d5", "exit_price": 44.0,
          "exit_reason": "signal_flat", "fold": 1, "held_sessions": 5,
          "notional_usd": 10_000.0, "bucket": "SHORT"}
    book = acc.book_round_trip(direction=1, notional_usd=10_000.0,
                               entry_price=40.0, exit_price=44.0,
                               stress_spread_frac=0.02)
    result = ar.CellResult(arm_id="X", family_key=cfg.FAMILY_A4_P2,
                           grid=["d0", "d5"], round_trips=[rt],
                           kernel_events=[{"round_trip_index": 0,
                                           "book": book}],
                           fills=[{"leg": "VXX", "session": "d0"},
                                  {"leg": "VXX", "session": "d5"}])
    cpc = bat.cost_path_control(result, dr.synthetic_universe(4)[
        "cost_source"])
    tiers = cpc["totals_by_tier"]
    assert tiers["1.0"]["execution_cost_usd_total"] == pytest.approx(200.0)
    assert tiers["1.5"]["execution_cost_usd_total"] == pytest.approx(300.0)
    assert tiers["2.0"]["execution_cost_usd_total"] == pytest.approx(400.0)
    for t in ("1.0", "1.5", "2.0"):
        assert tiers[t]["q16_path_line_usd_total_explicit"] == \
            pytest.approx(60.0)
    assert tiers["1.0"]["net_stress_usd_total"] == pytest.approx(740.0)
    assert tiers["1.5"]["net_stress_usd_total"] == pytest.approx(640.0)
    assert tiers["2.0"]["net_stress_usd_total"] == pytest.approx(540.0)
    assert cpc["n_fills"] == 2 and cpc["n_round_trips"] == 1
    assert cpc["buckets_present"] == ["SHORT"]


def test_cost_path_control_pays_both_buckets_on_rotations(syn_ctx6,
                                                          syn_universe):
    runner = ar.runner_for_arm(cfg.assemble_arm_configs()[
        "VOLNG1-A5-P2-ANCHOR"])
    res = ar.run_cell(runner, syn_ctx6, syn_universe["cost_source"])
    cpc = bat.cost_path_control(res, syn_universe["cost_source"])
    assert cpc["both_bucket_paths_paid"] is True
    assert set(cpc["buckets_present"]) == {"SHORT", "MID"}
    per_leg_formula = {p["leg"]: p["path_formula"] for p in
                       cpc["per_round_trip"]}
    for leg, formula in per_leg_formula.items():
        want = "ln(VIX9D/VIX)/21" if leg in ("VXX", "UVXY", "SVXY",
                                             "VIXY") \
            else "ln(VIX3M/VIX6M)/90"
        assert formula == want


# --------------------------------------------------------------------------- #
# index-only shadow
# --------------------------------------------------------------------------- #
def test_a5_index_only_shadow_consumes_no_etp_price(syn_ctx6):
    runner = ar.runner_for_arm(cfg.assemble_arm_configs()[
        "VOLNG1-A5-P2-ANCHOR"])
    shadow = bat.index_only_shadow(runner, syn_ctx6)
    assert shadow.notes["no_etp_price_in_state"] is True
    assert shadow.distinct_from_arm is True     # arm consumes ETP sides
    # invariance proof: destroying the ETP series cannot move the shadow
    ctx2 = dict(syn_ctx6)
    ctx2["adj"] = {leg: {d: 1.0 for d in syn_ctx6["grid"]}
                   for leg in syn_ctx6["adj"]}
    assert bat.a5_index_only_state(
        ctx2, 0.5, 2) == shadow.decision_state


def test_a4_index_only_shadow_is_the_arm_state_by_law(syn_ctx6):
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m3", _a4_arm(3))
    shadow = bat.index_only_shadow(runner, syn_ctx6)
    assert shadow.decision_state == runner.build_state(syn_ctx6)
    assert shadow.notes["no_etp_price_in_state"] is True


# --------------------------------------------------------------------------- #
# calendar-clock shadow (k=5)
# --------------------------------------------------------------------------- #
def test_calendar_clock_shadow_k5_shift_and_distinctness(syn_ctx6):
    runner = ar.SlopeAccelerationRunner("VOLNG1-A4-P2-m2", _a4_arm(2))
    shadow = bat.calendar_clock_shadow(runner, syn_ctx6)
    grid = syn_ctx6["grid"]
    state = runner.build_state(syn_ctx6)
    assert shadow.notes["calendar_shift_k_sessions"] == 5
    for i, d in enumerate(grid):
        want = state.get(grid[i - 5]) if i >= 5 else None
        assert shadow.decision_state[d] == want
    assert shadow.distinct_from_arm is True


def test_calendar_clock_shadow_constant_state_is_not_distinct(syn_ctx6):
    """A placement that survives the re-clock unchanged is a calendar
    artefact and dies: a CONSTANT regime state places identically after
    the k=5 re-clock (measured on the common valid span)."""
    class _ConstRunner(ar.SlopeAccelerationRunner):
        def build_state(self, ctx):
            return {d: SHORT for d in ctx["grid"]}

    runner = _ConstRunner("const", _a4_arm(2))
    shadow = bat.calendar_clock_shadow(runner, syn_ctx6)
    assert shadow.distinct_from_arm is False


# --------------------------------------------------------------------------- #
# placebo (ORDSHUF, seed 20260912)
# --------------------------------------------------------------------------- #
def test_placebo_determinism_marginals_and_order(syn_ctx6):
    runner = ar.runner_for_arm(cfg.assemble_arm_configs()[
        "VOLNG1-A4-P2-ANCHOR"])
    p1 = bat.placebo(runner, syn_ctx6)
    p2 = bat.placebo(runner, syn_ctx6)
    assert p1.decision_state == p2.decision_state      # seed determinism
    assert p1.notes["placebo_seed"] == 20260912
    state = runner.build_state(syn_ctx6)
    grid = syn_ctx6["grid"]

    def marginals(s):
        vals = sorted(repr(s[d]) for d in grid)
        return vals
    assert marginals(p1.decision_state) == marginals(state)  # matched
    assert p1.distinct_from_arm is True                     # destroyed


def test_placebo_different_seed_gives_different_series(syn_ctx6):
    runner = ar.runner_for_arm(cfg.assemble_arm_configs()[
        "VOLNG1-A4-P2-ANCHOR"])
    p1 = bat.placebo(runner, syn_ctx6, seed=20260912)
    p3 = bat.placebo(runner, syn_ctx6, seed=20260913)
    assert p1.decision_state != p3.decision_state


# --------------------------------------------------------------------------- #
# invalid-null distinction (Q-11)
# --------------------------------------------------------------------------- #
def test_invalid_null_audit_on_warmup(syn_ctx6, syn_universe):
    runner = ar.runner_for_arm(cfg.assemble_arm_configs()[
        "VOLNG1-A5-P2-ANCHOR"])
    res = ar.run_cell(runner, syn_ctx6, syn_universe["cost_source"])
    assert res.invalid_instants > 0
    audit = bat.invalid_null_audit(res)
    assert audit["verdict"] == "PASS"
    assert audit["decisions_from_invalid"] == 0
    assert audit["invalid_instants"] == res.invalid_instants
    state = res.decision_state
    warm = [d for d in syn_ctx6["grid"][:80]]
    assert all(state[d] is None for d in warm)   # never coerced to flat


# --------------------------------------------------------------------------- #
# R1-R6 fail-closed evaluator (hand-built metric fixtures)
# --------------------------------------------------------------------------- #
PASSING_METRICS = {
    "expectancy_net_tier2": 0.02,
    "arm_expectancy_net_tier2": 0.02,
    "index_control_expectancy_net_tier2": -0.01,
    "calendar_shadow_placement_distinct": True,
    "placebo_differential_significant": False,
    "fold_expectancies_net_tier2": {"1": 0.01, "2": 0.02, "3": -0.01},
    "profit_factor_net_tier2": 1.30,
    "stress_tier2_expectancy_net": 0.015,
    "drop_one_fold_positive": {"1": True, "2": True, "3": True},
    "max_single_round_trip_gross_share": 0.10,
}


def test_evaluator_survivor_requires_all_rules():
    out = ev.evaluate_stage_a(PASSING_METRICS)
    assert out["verdict"] == "PROVISIONAL_STAGE_A_SURVIVOR"
    assert set(out["rule_verdicts"].values()) == {"PASS"}


def test_r1_r3_r4_r5_r6_individual_laws():
    assert ev.evaluate_r1({"expectancy_net_tier2": 0.0}) == ev.FAIL
    assert ev.evaluate_r1({"expectancy_net_tier2": 0.001}) == ev.PASS
    assert ev.evaluate_r1({}) == ev.NOT_RUN
    folds3 = {"fold_expectancies_net_tier2": {"1": 0.01, "2": 0.01,
                                              "3": -5.0}}
    assert ev.evaluate_r3(folds3) == ev.PASS
    assert ev.evaluate_r3({"fold_expectancies_net_tier2":
                           {"1": 0.01, "2": -5.0, "3": -5.0}}) == ev.FAIL
    assert ev.evaluate_r3({"fold_expectancies_net_tier2":
                           {"1": 0.01, "2": -5.0}}) == ev.NOT_RUN
    r4 = ev.evaluate_r4({"profit_factor_net_tier2": 1.05})
    assert r4["verdict"] == ev.FAIL and r4["margin_to_bar"] == \
        pytest.approx(-0.05)
    assert ev.evaluate_r4({"profit_factor_net_tier2": 1.10})["verdict"] \
        == ev.PASS
    assert ev.evaluate_r4({})["verdict"] == ev.NOT_RUN
    assert ev.evaluate_r5({"stress_tier2_expectancy_net": -0.001}) == \
        ev.FAIL
    assert ev.evaluate_r5({}) == ev.NOT_RUN
    drop = {"drop_one_fold_positive": {"1": True, "2": True,
                                       "3": False},
            "max_single_round_trip_gross_share": 0.1}
    assert ev.evaluate_r6(drop) == ev.FAIL
    conc = {"drop_one_fold_positive": {"1": True, "2": True,
                                       "3": True},
            "max_single_round_trip_gross_share": 0.6}
    assert ev.evaluate_r6(conc) == ev.FAIL
    assert ev.evaluate_r6({"drop_one_fold_positive": {"1": True,
                                                      "2": True,
                                                      "3": True}}) == \
        ev.NOT_RUN


def test_r2_three_veto_limbs_and_not_run():
    base = dict(PASSING_METRICS)
    assert ev.evaluate_r2(base) == ev.PASS
    a = dict(base, index_control_expectancy_net_tier2=0.02)
    assert ev.evaluate_r2(a) == ev.FAIL      # limb (a): out-earns >= 0.5x
    b = dict(base, calendar_shadow_placement_distinct=False)
    assert ev.evaluate_r2(b) == ev.FAIL      # limb (b): not distinct
    c = dict(base, placebo_differential_significant=True)
    assert ev.evaluate_r2(c) == ev.FAIL      # limb (c): placebo fires
    d = {k: v for k, v in base.items()
         if k != "placebo_differential_significant"}
    assert ev.evaluate_r2(d) == ev.NOT_RUN   # any missing limb blocks


def test_evaluator_not_run_blocks_survivor_fail_closed():
    m = dict(PASSING_METRICS)
    del m["stress_tier2_expectancy_net"]
    out = ev.evaluate_stage_a(m)
    assert out["rule_verdicts"]["R5_STRESS"] == ev.NOT_RUN
    assert out["verdict"] == ev.NOT_RUN      # never an inferred PASS
    dead = ev.evaluate_stage_a(dict(PASSING_METRICS,
                                    expectancy_net_tier2=-0.01))
    assert dead["verdict"] == "STAGE_A_DEAD"


def test_pbo_law_six_cells_not_run_with_frozen_alternative():
    out = ev.pbo_law(6)
    assert out["verdict"] == ev.NOT_RUN
    assert out["n_cells"] == 6 and out["min_cells"] == 8
    assert "6" in out["reason"] and "8" in out["reason"]
    assert out["alternative_rule_binding_site"] == "R6_NON_CONCENTRATION"
    for sha in cfg.PBO_PRECEDENT_COMMITS:
        assert sha in out["alternative_rule_applied"]
    assert cfg.PBO_PRECEDENT_COMMITS == (
        "d0992d17df8e2dfde57c9a0806a5798f14021a4f",
        "f6c17886c32025242fdf21ffb8565666d64cbaec")
    big = ev.pbo_law(8)
    assert big["verdict"] == ev.NOT_RUN      # no fabricated PBO number


# --------------------------------------------------------------------------- #
# --dry-run-plumbing self-check (in-process; artifacts NOT rewritten)
# --------------------------------------------------------------------------- #
def test_dry_run_plumbing_end_to_end(syn_universe):
    out = dr.run_dry_run(skip_tests=True, write_artifacts=False)
    report, gate = out["report"], out["gate"]
    assert report["verdict"] == "DRY_RUN_CLEAN"
    step_a = report["step_a_configs"]
    assert step_a["n_cells"] == 6
    assert step_a["digests_all_match"] and \
        step_a["digests_pairwise_distinct"]
    assert step_a["budget_cells"] == [1, 2, 3, 4, 5, 6]
    step_b = report["step_b_representation"]
    assert step_b["all_series_granted"] is True
    assert all(step_b["series_digests_match_freeze"].values())
    rep = step_b["representation"]
    assert rep["grid_sessions_total_matches_freeze"] is True
    assert rep["bookable_matches_freeze"] is True
    assert rep["tail_matches_freeze"] is True
    assert step_b["corp_actions"]["residual_below_1e4_tol"] is True
    step_c = report["step_c_pipeline_synthetic"]
    assert step_c["n_cells"] == 6
    for aid, cell in step_c["cells"].items():
        sc = cell["structural_counts"]
        assert sc["fills_eq_2x_round_trips"] is True
        assert sc["kernel_events"] == sc["round_trips"]
        assert cell["controls"]["calendar_clock_shadow"]["k_sessions"] == 5
        assert cell["controls"]["placebo"]["seed"] == 20260912
        assert cell["controls"]["invalid_null_distinction"][
            "verdict"] == "PASS"
        assert cell["controls"]["cost_path_control"]["runnable"] is True
    assert step_c["pbo_law"]["verdict"] == "NOT_RUN"
    # the in-process invocation runs with --skip-tests: the pytest item
    # is honestly NOT_RUN (never an inferred PASS) and blocks the gate
    # overall; the executable path records the measured exit code
    pytest_item = {i["item"]: i for i in gate["items"]}[
        "pytest_tests_vol_ng1_i"]
    assert pytest_item["verdict"] == "NOT_RUN"
    assert pytest_item["measured"]["exit_code"] is None
    assert gate["overall"] == "NOT_RUN"
    # structural-only law on the published artifacts
    blob = json.dumps(report)
    assert not re.search(r"pnl|expectancy|profit_factor|sharpe", blob,
                         re.IGNORECASE) or "_note" in blob
    dr.assert_structural_only(report, "test")
    dr.assert_structural_only(gate, "test")


def test_gate_items_all_pass_and_measure_freeze_values():
    fz = cfg.load_selection_freeze()
    out = dr.run_dry_run(skip_tests=True, write_artifacts=False)
    gate = out["gate"]
    names = {i["item"]: i for i in gate["items"]}
    # every item measured, none FAIL; the ONLY NOT_RUN is the pytest
    # item (tests not run by this in-process invocation)
    assert not any(i["verdict"] == "FAIL" for i in gate["items"])
    not_run = [i for i in gate["items"] if i["verdict"] == "NOT_RUN"]
    assert [i["item"] for i in not_run] == ["pytest_tests_vol_ng1_i"]
    assert all(i["verdict"] == "PASS" for i in gate["items"]
               if i["verdict"] != "NOT_RUN")
    rep = names["representation_remeasured_matches_freeze"]["measured"]
    freeze_rep = fz["representation_freeze"]["common_grid"]
    assert rep["grid_sessions_total"] == freeze_rep["grid_sessions_total"]
    assert rep["bookable_instants"] == freeze_rep["bookable_instants"]
    assert rep["first_bookable_instant"] == \
        freeze_rep["first_bookable_instant"]
    assert rep["v7_tail_refused_sessions"] == \
        freeze_rep["v7_tail_refused_sessions"]
    ca_m = names["corp_actions_mandatory_layer"]["measured"]
    assert ca_m["inventory_total_steps"] == 27
    pbo_m = names["pbo_law_cells6_not_run_alternative_r6"]["measured"]
    assert pbo_m["n_cells"] == 6 and pbo_m["verdict"] == "NOT_RUN"
