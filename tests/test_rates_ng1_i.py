"""RATES-NG1 I-phase runner-machinery tests.

Cycle RATES-NG1, task rates-ng1-i-implementation (dispatch packet
rates-ng1-i-implementation, invocation lead-bg-rates-i-r2; attempt-1
died on an infrastructure quota error mid-task and left a partial
runners/ dir that this lane reviewed, fixed and completed).

SCOPE LAW: every test here runs on SYNTHETIC fixtures ONLY
(runners.fixtures: an explicit-LCG-free deterministic wave substrate;
no PRNG runtime, no real substrate bytes, no plane consumption, no
market data).  The only REAL objects touched are committed ARTIFACTS
read for structural pins (the S selection freeze, the P1 cost
contract, the P2 grid census -- digests, list lengths, frozen
constants) and committed CODE.  NO scored execution on real data and
NO outcome numbers on real data anywhere (I-phase law); the R1-R6 and
battery comparators are exercised on hand-computed SYNTHETIC edge
fixtures only.

Layers:
1.  Frozen-constant pins against the committed freeze/contract bytes.
2.  Cell-config digest assembly (3 cells, frozen digests verbatim).
3.  State machinery: hand-computed coordinates, PIT-expanding OLS
    residuals, quantile cuts, the 3 frozen gate variants, and EXACT
    parity of the NEUTRAL arm with the D2-screened state builder
    (d2_states.proposal_state_a5_p1) on the synthetic bundle.
4.  Position law: hand-traced holding / last-write-wins / fold-end /
    window-end decisions, Q-11 undefined discipline.
5.  Kernel booking: P1 DualBookLedger verbatim, cost once per fill on
    BOTH legs, ACT/365F drag, SHORT mirror-sign surface, dual-book
    equality.
6.  Control battery: level-vs-shape declared executioner, clock-only
    shadow, k=5 misaligned placebo, Q-11 alignment, kill semantics.
7.  R1-R6 scaffolding: per-rule hand-computed pass/fail, survivor law,
    PBO fail-closed < 8 cells with the ng1 precedent citations.
8.  Emission compliance scanner + dry-run plumbing self-check
    (structural counts only) + i-gate payload assembly.

Run the standalone self-check with:
    python tests/test_rates_ng1_i.py --dry-run-plumbing
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import research.assets.rates_ng1.runners as rn  # noqa: E402
from research.assets.rates_ng1 import clock as ck  # noqa: E402
from research.assets.rates_ng1.kernel import CostOnceViolation  # noqa: E402
from research.assets.rates_ng1.runners import (  # noqa: E402
    battery as bat,
    dryrun,
    fixtures as fx,
    rules as rl,
    runner as rr,
)
from research.control.rates_ng1_run.d2 import d2_states as ds  # noqa: E402

FREEZE_PATH = os.path.join(REPO_ROOT, "research", "control",
                           "rates_ng1_run", "s", "selection_freeze.json")
CONTRACT_PATH = os.path.join(REPO_ROOT, "research", "control",
                             "rates_ng1_run", "p1_cost_contract.json")
CENSUS_PATH = os.path.join(REPO_ROOT, "research", "control",
                           "rates_ng1_run", "p2_grid_census.json")

#: sha256 of the committed artifacts at BASE (drift = test failure).
FREEZE_SHA256 = "6e95dfcda132964142764398884389b055305e04a5c3563a088c46013a92d091"
CONTRACT_SHA256 = ("e7db0eef3cf40e334d519fb7dc92cefa0c5913994eb55ffc9d"
                   "03f69dd936c67c")
CENSUS_SHA256 = ("5cb9bdb02d4b065e8062a9619a4b56302d281dede3bb49f51a3e"
                 "0539e2e108a8")

#: Frozen arm_config_digests, verbatim from the freeze (section 2).
FROZEN_DIGESTS = {
    "RATESNG1-A5-P1-ARM-NEUTRAL":
        "33b78baa26e5ee8757eab484d7c6b0fd6e9845dcc3a52c4607e7bbe2b0f90a4c",
    "RATESNG1-A5-P1-ARM-CONSERVATIVE":
        "54ef5defe4aa8e9df4dafccc4ea924b1c3df1f8c59644ee571e55962fe554f1d",
    "RATESNG1-A5-P1-ARM-AGGRESSIVE":
        "cfdad940b518ec5a2ca0de673443e4d0238e71566b8bd4678aa61cebdf82e799",
}

BASE_SHA = "d059892f24a9f3f3ffa397ad8e08704a4755af28"


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture(scope="module")
def freeze() -> dict:
    with open(FREEZE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def contract() -> dict:
    with open(CONTRACT_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def cells(freeze: dict) -> list[dict]:
    return rn.assemble_cell_configs(freeze)


@pytest.fixture(scope="module")
def bundle() -> dict:
    return fx.synthetic_state_inputs()


def _mk_instants(dates: list[str], start_index: int = 1) -> list[dict]:
    """Bookable instants over ``dates`` (V7 readable bar = previous
    session; TRUE 16:00-NY close instants via the P1 clock)."""
    return [
        {
            "decision_session": s,
            "decision_utc": ck.ny_close_utc(s).isoformat(),
            "readable_bar_date": dates[max(0, i - 1)],
            "session_index": start_index + i,
        }
        for i, s in enumerate(dates)
    ]


def _weekdays(start_iso: str, n: int) -> list[str]:
    out: list[str] = []
    d = dt.date.fromisoformat(start_iso)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


# ================================================================== #
# 1. Frozen-constant pins                                             #
# ================================================================== #

class TestFrozenConstantPins:
    def test_artifacts_unchanged_at_base(self):
        assert _sha256_file(FREEZE_PATH) == FREEZE_SHA256
        assert _sha256_file(CONTRACT_PATH) == CONTRACT_SHA256
        assert _sha256_file(CENSUS_PATH) == CENSUS_SHA256

    def test_leg_pair_and_tenor_bracket_law(self, freeze):
        leg_law = freeze["section_2_arm_configuration_plan"][
            "shared_arm_law"]["leg_pair_freeze"]
        assert rr.LEG_PAIR == {"front_leg": "SHY", "long_leg": "TLT"}
        assert rr.TENOR_BRACKET_MAPPING == {"2 Yr": "SHY", "30 Yr": "TLT"}
        assert leg_law["front_leg"] == "SHY"
        assert leg_law["long_leg"] == "TLT"
        # IEF/IEI are reserve legs: unmapped.
        assert "IEF" not in rr.TENOR_BRACKET_MAPPING
        assert "IEI" not in rr.TENOR_BRACKET_MAPPING

    def test_fold_windows_frozen_verbatim(self, freeze):
        r3 = [r for r in
              freeze["section_3_stage_a_rule_order_frozen"]["rules"]
              if r.startswith("R3")][0]
        assert rr.FOLD_WINDOWS == (
            ("2019-01-07", "2021-07-28"),
            ("2021-07-29", "2024-02-18"),
            ("2024-02-19", "2026-09-11"),
        )
        for lo, hi in rr.FOLD_WINDOWS:
            assert f"{lo}..{hi}" in r3
        # continuity: each fold starts the day after its predecessor.
        assert rr.FOLD_WINDOWS[1][0] == "2021-07-29"
        assert rr.FOLD_WINDOWS[2][0] == "2024-02-19"

    def test_holding_and_k_frozen(self, freeze):
        arm_cfg = freeze["section_2_arm_configuration_plan"]["arms"][0][
            "config"]
        assert arm_cfg["holding_trading_days"] == rr.HOLDING_TRADING_DAYS
        assert arm_cfg["orthogonalization"]["min_past_points"] == \
            rr.MIN_PAST_POINTS == 63
        k = freeze["section_6_control_battery_binding"][
            "k_misalign_sessions"]
        assert rr.K_MISALIGN_SESSIONS == bat.PLACEBO_K == k == 5

    def test_tiers_and_drag_cited_from_cost_contract(self, contract):
        for leg in ("SHY", "TLT"):
            pe = contract["per_etp"][leg]
            assert fx.SYNTHETIC_TIERS_BPS[leg] == pytest.approx(
                pe["spread_primary"]["cs_p90_bps"])
            drag = pe["expense_drag"]
            assert drag["drag_days_basis"] == "ACT/365F"
            assert fx.SYNTHETIC_ER_DAILY[leg] == pytest.approx(
                drag["drag_per_day_fraction"])
        assert contract["cost_ladder_tier"] == 2.0
        assert contract["cost_frequency"] == "once_per_fill"
        # the freeze cites the SAME tier constants (section 4).
        with open(FREEZE_PATH, "r", encoding="utf-8") as fh:
            freeze = json.load(fh)
        frozen_tiers = freeze["section_4_cost_contract_binding"][
            "per_leg_stress_tier_bps"]
        for leg in ("SHY", "TLT"):
            assert frozen_tiers[leg] == pytest.approx(
                fx.SYNTHETIC_TIERS_BPS[leg])

    def test_gate_rules_match_freeze_configs(self, freeze):
        arms = freeze["section_2_arm_configuration_plan"]["arms"]
        assert len(arms) == 3
        for arm in arms:
            assert arm["config"]["gate"]["state_rule"] in rr.GATE_RULES
            assert arm["role"] == "ANCHOR_VARIANT"
        state_rules = {a["config"]["gate"]["state_rule"] for a in arms}
        assert state_rules == set(rr.GATE_RULES)

    def test_frozen_rule_bounds_carry_over(self):
        assert rl.R1_EXPECTANCY_GT == 0.0
        assert (rl.R3_FOLDS_TOTAL, rl.R3_MIN_POSITIVE_FOLDS) == (3, 2)
        assert rl.R4_PF_MIN == 1.10
        assert rl.R6_MAX_SINGLE_INSTANT_GROSS_SHARE == 0.5
        assert rl.PBO_MIN_CELLS == 8
        assert len(rl.FROZEN_RULE_ORDER) == 6
        assert rl.FROZEN_RULE_ORDER[0].startswith("R1 EXPECTANCY")
        assert rl.FROZEN_RULE_ORDER[1].startswith("R2 CONTROL_KILL")

    def test_s1_sealed_untouched(self, freeze):
        assert freeze["s1"] == "SEALED_UNTOUCHED"


# ================================================================== #
# 2. Cell-config assembly (structural plumbing)                       #
# ================================================================== #

class TestCellConfigAssembly:
    def test_three_cells_digests_match_freeze(self, cells):
        assert len(cells) == 3
        for cell in cells:
            assert cell["arm_config_digest"] == \
                FROZEN_DIGESTS[cell["arm_id"]]
            assert cell["cell_id"] == \
                f"{rr.FAMILY_ID}:{cell['arm_id']}"

    def test_digests_pairwise_distinct(self, cells):
        digests = [c["arm_config_digest"] for c in cells]
        assert len(set(digests)) == 3

    def test_digest_law_recompute(self, cells):
        # Freeze law: sha256 of canonical JSON (sort_keys, compact).
        for cell in cells:
            blob = json.dumps(cell["config"], sort_keys=True,
                              separators=(",", ":")).encode("utf-8")
            assert hashlib.sha256(blob).hexdigest() == \
                cell["arm_config_digest"]

    def test_drift_refused(self, freeze):
        bad = copy.deepcopy(freeze)
        bad["section_2_arm_configuration_plan"]["arms"][0]["config"][
            "holding_trading_days"] = 4
        with pytest.raises(rr.RunnerLawError, match="digest drift"):
            rn.assemble_cell_configs(bad)

    def test_cell_citations(self, cells, freeze):
        binding = freeze["section_4_cost_contract_binding"]
        for cell in cells:
            cit = cell["cost_treatment_citation"]
            assert cit["contract_path"] == binding["contract"]["path"]
            assert cit["cost_ladder_tier"] == 2.0
            assert cit["cost_frequency"] == "once_per_fill"
            assert cit["both_legs_charged"] is True
            assert cell["k_misalign_sessions"] == 5


# ================================================================== #
# 3. State machinery                                                  #
# ================================================================== #

class TestStateMachinery:
    def test_curve_coordinates_hand(self):
        curve = {"2019-01-04": {"2 Yr": 2.0, "10 Yr": 3.0, "30 Yr": 4.5}}
        insts = [{"readable_bar_date": "2019-01-04"}]
        coords = rr.curve_coordinates(curve, insts)
        assert coords["slope"] == [4.5 - 2.0]      # 30 - 2
        assert coords["curvature"] == [2.0 - 6.0 + 4.5]  # 2 - 2*10 + 30
        assert coords["level"] == [3.0]            # 10 Yr

    def test_curve_coordinates_missing_tenor_all_none(self):
        curve = {"2019-01-04": {"2 Yr": 2.0, "10 Yr": 3.0}}  # 30 Yr gone
        coords = rr.curve_coordinates(
            curve, [{"readable_bar_date": "2019-01-04"}])
        assert coords == {"slope": [None], "curvature": [None],
                          "level": [None]}

    def test_decomposition_drift_refused(self):
        bad_cfg = {"decomposition": {"slope_tenors": ["2 Yr", "30 Yr"],
                                     "level_tenor": "10 Yr"}}
        with pytest.raises(rr.RunnerLawError, match="decomposition basis"):
            rr.curve_coordinates({}, [], bad_cfg)

    def test_ols_residual_hand(self):
        # y = 0.5 x exactly: every in-window residual is exactly 0.
        got = rr.ols_residual_on_level(
            [1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 6.0, 8.0, 10.0], 2)
        assert got == pytest.approx([None, None, 0.0, 0.0, 0.0])
        # hand case with an outlier: y=[1,3,2], x=[2,4,6]; the first
        # legal fit (pairs (2,1),(4,3)) gives beta=1, alpha=-1, so the
        # residual at the 3rd instant is 2 - (-1 + 1*6) = -3.
        got2 = rr.ols_residual_on_level([1.0, 3.0, 2.0],
                                        [2.0, 4.0, 6.0], 2)
        assert got2 == pytest.approx([None, None, -3.0])

    def test_ols_min_past_gating(self):
        got = rr.ols_residual_on_level(
            [1.0, 2.0, 3.0, 4.0, 5.0], [2.0, 4.0, 6.0, 8.0, 10.0], 4)
        # First legal fit only at the 4th strictly-past pair (i=4).
        assert got == pytest.approx([None, None, None, None, 0.0])

    def test_ols_zero_variance_design_none(self):
        got = rr.ols_residual_on_level([1.0, 2.0, 3.0],
                                       [5.0, 5.0, 5.0], 2)
        assert got == [None, None, None]

    def test_ols_length_mismatch_refused(self):
        with pytest.raises(rr.RunnerLawError, match="length mismatch"):
            rr.ols_residual_on_level([1.0], [1.0, 2.0], 1)

    def test_quantile_cut_linear_interpolation(self):
        assert rr.quantile_cut([3.0, 1.0, 5.0, 2.0, 4.0], 0.5) == 3.0
        assert rr.quantile_cut([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
        assert rr.quantile_cut([1.0, 2.0, 3.0, 4.0], 0.25) == 1.75
        assert rr.quantile_cut([1.0, 2.0, 3.0, 4.0], 0.75) == 3.25
        with pytest.raises(rr.RunnerLawError):
            rr.quantile_cut([], 0.5)

    def _coords4(self):
        return ([0.0, 1.0, 2.0, 3.0], [10.0, 30.0, 20.0, 40.0])

    def test_gate_and_rule_hand(self):
        a, b = self._coords4()
        got = rr.gate_state_series(a, b, {
            "state_rule": "both_above_plus1_both_below_minus1_else_zero",
            "upper_quantile": 0.5, "lower_quantile": 0.5})
        # cuts: a_med 1.5, b_med 25.0 -> [-1, 0, 0, +1].
        assert got == [-1.0, 0.0, 0.0, 1.0]

    def test_gate_or_rule_hand(self):
        a, b = self._coords4()
        got = rr.gate_state_series(a, b, {
            "state_rule":
                "either_above_plus1_either_below_minus1_else_zero",
            "upper_quantile": 0.5, "lower_quantile": 0.5})
        # OR gate: [-1 (both below), +1 (b hi), +1 (a hi), +1 (both hi)].
        assert got == [-1.0, 1.0, 1.0, 1.0]

    def test_gate_quartile_rule_hand(self):
        a, b = self._coords4()
        got = rr.gate_state_series(a, b, {
            "state_rule":
                "both_above_upper_q_plus1_both_below_lower_q_minus1_"
                "else_zero",
            "upper_quantile": 0.75, "lower_quantile": 0.25})
        # q75: a 2.25 / b 32.5; q25: a 1.75 / b 17.5 -> [-1, 0, 0, +1].
        assert got == [-1.0, 0.0, 0.0, 1.0]

    def test_gate_cut_is_strict(self):
        # A coordinate exactly AT its cut is neither above nor below.
        got = rr.gate_state_series([0.0, 1.0], [0.0, 1.0], {
            "state_rule": "both_above_plus1_both_below_minus1_else_zero",
            "upper_quantile": 0.5, "lower_quantile": 0.5})
        assert got == [-1.0, 1.0]  # cut 0.5: 0.0 below, 1.0 above

    def test_gate_unknown_rule_refused(self):
        with pytest.raises(rr.RunnerLawError, match="refused"):
            rr.gate_state_series([1.0], [1.0],
                                 {"state_rule": "TUNED_VARIANT"})

    def test_gate_undefined_coord_none(self):
        got = rr.gate_state_series([1.0, None], [2.0, 3.0], {
            "state_rule": "both_above_plus1_both_below_minus1_else_zero",
            "upper_quantile": 0.5, "lower_quantile": 0.5})
        assert got[1] is None  # Q-11: UNDEFINED, never inferred as zero

    def test_d2_parity_neutral_exact(self, cells, bundle):
        """The NEUTRAL arm IS the D2-screened state, instance for
        instance (frozen defaults verbatim)."""
        neutral = [c for c in cells
                   if c["arm_id"] == "RATESNG1-A5-P1-ARM-NEUTRAL"][0]
        got = rn.arm_state_series(neutral["config"],
                                  bundle["curve_by_date"],
                                  bundle["instants"])
        want = ds.proposal_state_a5_p1(bundle["grid"], bundle["instants"],
                                       bundle["curve_by_date"])
        assert got == want
        assert len(got) == len(bundle["instants"])
        non_vacuous = sum(1 for s in got if s not in (None, 0.0))
        assert non_vacuous > 0  # the screened state is non-vacuous

    def test_variant_inclusions(self, cells, bundle):
        """Rule form: CONSERVATIVE activations are a sign-preserving
        subset of NEUTRAL's, which are a subset of AGGRESSIVE's."""
        states = {}
        for name in ("NEUTRAL", "CONSERVATIVE", "AGGRESSIVE"):
            cfg = [c for c in cells
                   if c["arm_id"].endswith(name)][0]["config"]
            states[name] = rn.arm_state_series(cfg, bundle["curve_by_date"],
                                               bundle["instants"])
        for s_cons, s_neu in zip(states["CONSERVATIVE"],
                                 states["NEUTRAL"]):
            if s_cons not in (None, 0.0):
                assert s_cons == s_neu
        for s_neu, s_agg in zip(states["NEUTRAL"], states["AGGRESSIVE"]):
            if s_neu not in (None, 0.0):
                assert s_neu == s_agg


# ================================================================== #
# 4. Position law (hand-traced decision series)                       #
# ================================================================== #

class TestPositionLaw:
    def test_holding_exit_hand(self):
        dates = _weekdays("2021-07-20", 10)   # fold-1 last: 2021-07-28
        insts = _mk_instants(dates, start_index=900)
        states = [1.0] + [0.0] * 9            # entry idx 900, expiry 905
        _, rts, meta = rn.positions_from_states(
            states, insts, "T|RATESNG1-A5-P1-ARM-NEUTRAL")
        assert len(rts) == 1
        # 5 sessions after 2021-07-20 == 2021-07-27; expiry (905) is at
        # or before the fold cap (906) -> natural holding exit.
        assert (rts[0]["entry_session"], rts[0]["exit_session"],
                rts[0]["exit_reason"]) == \
            ("2021-07-20", "2021-07-27", "holding")
        assert meta["exit_reasons"]["holding"] == 1

    def test_last_write_wins_overwrite_hand(self):
        dates = _weekdays("2019-01-07", 8)   # instants idx 1..8
        insts = _mk_instants(dates)
        states = [1.0, None, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0]
        recs, rts, meta = rn.positions_from_states(
            states, insts, "T|RATESNG1-A5-P1-ARM-NEUTRAL")
        assert [(r["direction"], r["entry_session"], r["exit_session"],
                 r["exit_reason"]) for r in rts] == [
            (1, "2019-01-07", "2019-01-10", "overwritten"),
            (-1, "2019-01-10", "2019-01-16", "window_end")]
        # position_after hand series: -1 persists to the grid end.
        assert [r["position_after"] for r in recs] == \
            [1, 1, 1, -1, -1, -1, -1, 0]
        assert meta["exit_reasons"]["overwritten"] == 1
        assert meta["exit_reasons"]["window_end"] == 1
        assert meta["states_undefined"] == 1
        assert meta["state_events_nonzero"] == 2

    def test_undefined_state_is_no_event(self):
        dates = _weekdays("2019-01-07", 8)
        insts = _mk_instants(dates)
        states = [1.0] + [None] * 7
        recs, rts, meta = rn.positions_from_states(
            states, insts, "T|RATESNG1-A5-P1-ARM-NEUTRAL")
        # None is NOT an overwrite event: the +1 position persists
        # until its natural 5-session expiry (idx 6 = 2019-01-14).
        assert len(rts) == 1
        assert (rts[0]["exit_session"], rts[0]["exit_reason"]) == \
            ("2019-01-14", "holding")
        assert meta["states_undefined"] == 7
        assert meta["state_events_nonzero"] == 1
        assert [r["position_after"] for r in recs] == \
            [1, 1, 1, 1, 1, 0, 0, 0]

    def test_fold_end_mid_window_hand(self):
        dates = _weekdays("2021-07-20", 10)   # idx 900..909
        insts = _mk_instants(dates, start_index=900)
        states = [0.0] * 5 + [1.0] + [0.0] * 4  # entry idx 905 (07-27)
        _, rts, meta = rn.positions_from_states(
            states, insts, "T|RATESNG1-A5-P1-ARM-NEUTRAL")
        # expiry 910 runs past the fold-1 cap (idx 906 = 2021-07-28);
        # the grid continues (fold 2) -> force-flat at the fold end.
        assert (rts[0]["exit_session"], rts[0]["exit_reason"]) == \
            ("2021-07-28", "fold_end")
        assert meta["exit_reasons"]["fold_end"] == 1
        assert meta["fold_force_flat_same_day"] == 0

    def test_fold_end_same_day_counter(self):
        dates = _weekdays("2021-07-20", 10)
        insts = _mk_instants(dates, start_index=900)
        states = [0.0] * 6 + [1.0, 0.0, 0.0, 0.0]  # entry idx 906 = 07-28
        _, rts, meta = rn.positions_from_states(
            states, insts, "T|RATESNG1-A5-P1-ARM-NEUTRAL")
        # Entry ON the fold's last instant: the round trip closes the
        # same day (disclosed metric; unit adapted to decision instants).
        assert (rts[0]["entry_session"], rts[0]["exit_session"],
                rts[0]["exit_reason"]) == \
            ("2021-07-28", "2021-07-28", "fold_end")
        assert meta["fold_force_flat_same_day"] == 1

    def test_window_end_hand(self):
        dates = _weekdays("2021-07-20", 10)
        insts = _mk_instants(dates, start_index=900)
        states = [0.0] * 9 + [1.0]  # entry idx 909: fold cap == grid end
        _, rts, meta = rn.positions_from_states(
            states, insts, "T|RATESNG1-A5-P1-ARM-NEUTRAL")
        assert (rts[0]["entry_session"], rts[0]["exit_session"],
                rts[0]["exit_reason"]) == \
            ("2021-08-02", "2021-08-02", "window_end")
        assert meta["exit_reasons"]["window_end"] == 1

    def test_decision_records_structure(self, bundle, cells):
        neutral = [c for c in cells
                   if c["arm_id"] == "RATESNG1-A5-P1-ARM-NEUTRAL"][0]
        res = rn.run_arm(neutral["arm_id"], neutral["role"],
                         neutral["config"], bundle["instants"],
                         bundle["curve_by_date"], bundle["leg_closes"],
                         bundle["tiers_bps"], bundle["er_daily"])
        recs = res["decision_series"]
        assert len(recs) == len(bundle["instants"])
        ids = [r["decision_id"] for r in recs]
        assert len(set(ids)) == len(ids)
        assert all(r["family_id"] == "RATESNG1-A5-P1" for r in recs)
        # structural only: NO outcome field anywhere in a record.
        forbidden = {"pnl", "expectancy", "profit_factor", "equity",
                     "return", "sharpe", "win_rate", "drawdown"}
        for rec in recs:
            assert not (set(rec) & forbidden)
        # folds assigned 1..1 (synthetic window inside fold 1).
        assert {r["fold"] for r in recs} == {1}

    def test_fold_of_session_refused_outside(self):
        with pytest.raises(rr.RunnerLawError, match="refused"):
            rr.fold_of_session("2021-07-28T00:00:00")
        with pytest.raises(rr.RunnerLawError, match="refused"):
            rr.fold_of_session("2018-12-31")
        assert rr.fold_of_session("2019-01-07") == 1
        assert rr.fold_of_session("2021-07-29") == 2
        assert rr.fold_of_session("2024-02-19") == 3

    def test_law_refusals(self):
        dates = _weekdays("2019-01-07", 4)
        insts = _mk_instants(dates)
        with pytest.raises(rr.RunnerLawError, match="length mismatch"):
            rn.positions_from_states([1.0, 0.0], insts, "T|A")
        with pytest.raises(rr.RunnerLawError, match="holding"):
            rn.positions_from_states([1.0, 0.0, 0.0, 0.0], insts, "T|A",
                                     holding=0)
        with pytest.raises(rr.RunnerLawError, match="empty instant grid"):
            rn.positions_from_states([], [], "T|A")


# ================================================================== #
# 5. Kernel booking (P1 dual-book kernel, used verbatim)              #
# ================================================================== #

class TestKernelBooking:
    TIERS = {"SHY": fx.SYNTHETIC_TIERS_BPS["SHY"],
             "TLT": fx.SYNTHETIC_TIERS_BPS["TLT"]}
    ER = {"SHY": fx.SYNTHETIC_ER_DAILY["SHY"],
          "TLT": fx.SYNTHETIC_ER_DAILY["TLT"]}

    def _one_rt(self, direction: float):
        closes = {"SHY": {"2019-01-07": 81.0, "2019-01-14": 82.0},
                  "TLT": {"2019-01-07": 99.0, "2019-01-14": 98.0}}
        rts = [{"rt_id": "T|RATESNG1-A5-P1-ARM-NEUTRAL|RT00001",
                "arm_id": "RATESNG1-A5-P1-ARM-NEUTRAL",
                "family_id": "RATESNG1-A5-P1",
                "direction": int(direction),
                "entry_session_index": 1, "entry_session": "2019-01-07",
                "exit_session_index": 6, "exit_session": "2019-01-14",
                "exit_reason": "holding", "fold": 1}]
        books = rn.book_round_trips(
            "RATESNG1-A5-P1-ARM-NEUTRAL", rts, closes, self.TIERS,
            self.ER, notional_per_leg=rr.NOTIONAL_PER_LEG_USD)
        return books, rts

    def test_hand_computed_leg_booking(self):
        books, rts = self._one_rt(+1.0)
        shy = rts[0]["legs"]["SHY"]
        tlt = rts[0]["legs"]["TLT"]
        # Sign convention: state +1 => LONG SHY / SHORT TLT.
        assert shy["orientation"] == "LONG"
        assert tlt["orientation"] == "SHORT"
        # True quantities from RAW closes; tenor-bracket provenance.
        assert shy["qty"] == pytest.approx(
            rr.NOTIONAL_PER_LEG_USD / 81.0)
        assert tlt["qty"] == pytest.approx(
            rr.NOTIONAL_PER_LEG_USD / 99.0)
        assert shy["tenor_bracket"] == "2 Yr"
        assert tlt["tenor_bracket"] == "30 Yr"
        # Cost law: CS p90 tier ONCE per fill, BOTH legs (4 fills).
        tier_shy = fx.SYNTHETIC_TIERS_BPS["SHY"] / 1e4
        assert shy["spread_cost_entry"] == pytest.approx(
            tier_shy * 81.0 * shy["qty"])
        assert shy["spread_cost_exit"] == pytest.approx(
            tier_shy * 82.0 * shy["qty"])
        assert rts[0]["cost_event_count"] == 6  # 3 per leg x 2 legs

    def test_cost_once_per_fill_both_legs_and_drag(self):
        books, rts = self._one_rt(+1.0)
        led_shy = books.ledger("SHY", "LONG")
        led_tlt = books.ledger("TLT", "SHORT")
        for led, leg in ((led_shy, "SHY"), (led_tlt, "TLT")):
            assert len(led.fills) == 2     # entry + exit
            assert len(led.marks) == 2
            assert len(led.cost_events) == 1  # one typed drag event
            drag = led.cost_events[0]
            assert drag["kind"] == "expense_drag"
            assert drag["days"] == rr.HOLDING_CALENDAR_DAYS_CHARGED == 7
            assert drag["notional"] == pytest.approx(
                rr.NOTIONAL_PER_LEG_USD)
            # ACT/365F drag over the frozen 7-calendar-day convention.
            assert drag["amount"] == pytest.approx(
                rr.NOTIONAL_PER_LEG_USD * fx.SYNTHETIC_ER_DAILY[leg] * 7)
            fills_spread = [f["spread_cost"] for f in led.fills]
            assert all(c is not None and c > 0 for c in fills_spread)
            # exactly ONE spread cost per fill (charged once, not twice)
            assert len(fills_spread) == 2
        # replaying a fill id violates the cost-once law (kernel law).
        with pytest.raises(CostOnceViolation):
            led_shy.apply_fill(fill_id=f"{rts[0]['rt_id']}|SHY|ENTRY",
                               ts="t", ticker="SHY", side="BUY",
                               qty=1.0, price=81.0, spread_cost=0.0)

    def test_dual_book_equality_and_dst_timestamps(self):
        books, _ = self._one_rt(+1.0)
        view = books.structural_view()
        assert set(view) == {"RATESNG1-A5-P1-ARM-NEUTRAL|SHY|LONG",
                             "RATESNG1-A5-P1-ARM-NEUTRAL|TLT|SHORT"}
        assert all(v["dual_book_equality_ok"] for v in view.values())
        assert all(v["fills"] == 2 and v["marks"] == 2
                   and v["cost_events"] == 1 for v in view.values())
        # V7/P1 clock law: execution AT the 16:00 NY close (DST-true).
        led = books.ledger("SHY", "LONG")
        assert led.fills[0]["ts"] == \
            ck.ny_close_utc("2019-01-07").isoformat()
        assert ck.ny_close_utc("2019-01-07").isoformat().endswith(
            "21:00:00+00:00")           # EST
        assert ck.ny_close_utc("2019-07-01").isoformat().endswith(
            "20:00:00+00:00")           # EDT

    def test_short_mirror_sign_surface(self):
        # SHORT leg PnL is the NEGATIVE of the mirror long-form PnL.
        assert rn.round_trip_leg_signed_pnl("LONG", 12.5) == 12.5
        assert rn.round_trip_leg_signed_pnl("SHORT", 12.5) == -12.5
        with pytest.raises(rr.RunnerLawError, match="orientation"):
            rn.round_trip_leg_signed_pnl("FLAT", 1.0)

    def test_missing_or_nonpositive_price_refused(self):
        closes = {"SHY": {"2019-01-07": 81.0},        # exit price gone
                  "TLT": {"2019-01-07": 99.0, "2019-01-14": 98.0}}
        rts = [{"rt_id": "X|RT00001", "arm_id": "RATESNG1-A5-P1-ARM"
                "-NEUTRAL", "family_id": "RATESNG1-A5-P1",
                "direction": 1, "entry_session_index": 1,
                "entry_session": "2019-01-07", "exit_session_index": 6,
                "exit_session": "2019-01-14", "exit_reason": "holding",
                "fold": 1}]
        with pytest.raises(rr.RunnerLawError, match="fail-closed"):
            rn.book_round_trips("RATESNG1-A5-P1-ARM-NEUTRAL", rts,
                                closes, self.TIERS, self.ER)
        bad = {"SHY": {"2019-01-07": 81.0, "2019-01-14": 0.0},
               "TLT": {"2019-01-07": 99.0, "2019-01-14": 98.0}}
        with pytest.raises(rr.RunnerLawError, match="refused"):
            rn.book_round_trips("RATESNG1-A5-P1-ARM-NEUTRAL", rts,
                                bad, self.TIERS, self.ER)


# ================================================================== #
# 6. Control battery                                                  #
# ================================================================== #

class TestControlBattery:
    def test_killer_roles_frozen_order(self, freeze):
        battery_spec = freeze["section_6_control_battery_binding"]
        roles = [c["role"] for c in battery_spec["controls"]]
        assert roles == list(bat.KILLER_ROLES)
        assert bat.KILLER_ROLES[0] == \
            "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL"
        assert battery_spec["controls"][0]["status"] == \
            "DECLARED_EXECUTIONER"
        assert battery_spec["controls"][0]["mandatory"] is True

    def test_align_defined_pairs_q11_hand(self):
        al = bat.align_defined_pairs(
            [1.0, None, 3.0, 4.0], [2.0, 9.0, None, 8.0])
        assert al["n_instants"] == 4
        assert al["n_pairs_used"] == 2            # i0 and i3
        assert al["dropped_undefined_side_a"] == 1  # i1 (a None)
        assert al["dropped_undefined_side_b"] == 1  # i2 (b None)
        assert al["pairs_a"] == [1.0, 4.0]
        assert al["pairs_b"] == [2.0, 8.0]
        with pytest.raises(ValueError):
            bat.align_defined_pairs([1.0], [1.0, 2.0])

    def test_kill_semantics_hand(self):
        kill = bat.out_earning_kill([1.0, 2.0], [1.5, 2.5],
                                    "CLOCK_ONLY_SHADOW")
        assert kill["kill"] is True
        assert kill["margin_control_minus_anchor"] == pytest.approx(0.5)
        tie = bat.out_earning_kill([1.0, 2.0], [1.0, 2.0], "PLACEBO")
        assert tie["kill"] is False           # a tie is NOT a kill
        assert tie["margin_control_minus_anchor"] == 0.0
        lower = bat.out_earning_kill([1.0, 2.0], [0.5, 1.5],
                                     "LEVEL_VS_SHAPE_DECOMPOSITION"
                                     "_CONTROL")
        assert lower["kill"] is False

    def test_undefined_pairs_excluded_from_means(self):
        got = bat.out_earning_kill([1.0, None, 3.0], [2.0, 99.0, 3.0],
                                   "PLACEBO")
        # the 99 (undefined on the anchor side) never enters a mean.
        assert got["n_pairs_used"] == 2
        assert got["anchor_mean_edge"] == pytest.approx(2.0)
        assert got["control_mean_edge"] == pytest.approx(2.5)
        assert got["kill"] is True
        assert got["dropped_undefined_anchor"] == 1

    def test_unknown_role_refused(self):
        with pytest.raises(ValueError, match="killer control role"):
            bat.out_earning_kill([1.0], [2.0], "TUNED_SHADOW")

    def test_battery_verdict_family_kill(self):
        verdict = bat.battery_verdict(
            [0.10] * 10,
            {"LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL": [0.05] * 10,
             "CLOCK_ONLY_SHADOW": [0.20] * 10,
             "PLACEBO": [0.01] * 10})
        assert verdict["family_kill"] is True
        assert verdict["killed_by"] == ["CLOCK_ONLY_SHADOW"]
        assert len(verdict["comparisons"]) == 3
        assert verdict["k_misalign_sessions"] == 5
        assert "falsification_rule_citation" in verdict
        clean = bat.battery_verdict(
            [0.10] * 10,
            {"LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL": [0.05] * 10,
             "CLOCK_ONLY_SHADOW": [0.05] * 10,
             "PLACEBO": [0.05] * 10})
        assert clean["family_kill"] is False
        assert clean["killed_by"] == []

    def test_battery_missing_roles_fail_closed(self):
        with pytest.raises(ValueError, match="frozen killer roles"):
            bat.battery_verdict([0.1], {"BOGUS": [0.2]})
        with pytest.raises(ValueError):
            bat.battery_verdict(
                [0.1], {r: [0.0] for r in bat.KILLER_ROLES[:2]})

    def test_level_control_state_hand(self):
        got = rn.level_control_state([1.0, 2.0, 3.0, 4.0])
        # sample median 2.5 -> sign state [-1, -1, +1, +1].
        assert got == [-1.0, -1.0, 1.0, 1.0]
        # cut computed over the DEFINED values only: median(1,3,4)=3.
        # strict comparisons -> the value AT the cut is flat (0.0).
        assert rn.level_control_state([1.0, None, 3.0, 4.0]) == \
            [-1.0, None, 0.0, 1.0]
        assert rn.level_control_state([None, None]) == [None, None]

    def test_clock_only_state_hand(self):
        insts = [{"decision_session": d} for d in
                 ("2026-09-07", "2026-09-08", "2026-09-09",
                  "2026-09-12")]  # Mon, Tue, Wed, Sat
        got = rn.clock_only_state(insts)
        assert got == [0.0, 1.0, 0.0, 0.0]  # +1 ONLY on Tuesday sessions

    def test_placebo_k5_misalignment(self):
        state = [1.0, -1.0, 0.0, None, 1.0, -1.0, 0.0, 1.0]
        got = rn.misaligned_state(state)
        assert got[:5] == [None] * 5          # head is UNDEFINED
        assert got[5:] == state[:3]
        assert bat.placebo_state(state) == got
        with pytest.raises(rr.RunnerLawError, match="positive"):
            rn.misaligned_state(state, k=0)
        with pytest.raises(rr.RunnerLawError, match="positive"):
            rn.misaligned_state(state, k=-3)


# ================================================================== #
# 7. R1-R6 scaffolding + PBO law                                      #
# ================================================================== #

class TestRulesR1R6:
    @staticmethod
    def _battery(kill: bool = False, by: str =
                 "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL") -> dict:
        return {
            "family_kill": kill,
            "killed_by": [by] if kill else [],
            "comparisons": [{"control_role": r} for r in
                            bat.KILLER_ROLES],
        }

    def test_all_rules_pass_survivor(self):
        edges = [1.0, 1.0, 1.0, -0.2]
        folds = [1, 2, 3, 3]
        ev = rn.evaluate_r1_r6(edges, folds, self._battery(False),
                               [1.0] * 4)
        assert ev["survivor"] == "PROVISIONAL_STAGE_A_SURVIVOR"
        assert ev["failed_rules"] == []
        assert ev["rules"]["R1"]["mean_edge"] == pytest.approx(0.7)
        assert ev["rules"]["R1"]["margin"] == pytest.approx(0.7)
        assert ev["rules"]["R3"]["positive_folds"] == 3
        assert ev["rules"]["R3"]["per_fold_means"] == \
            {"1": 1.0, "2": 1.0, "3": pytest.approx(0.4)}
        pf = ev["rules"]["R4"]
        assert pf["gross_win"] == pytest.approx(3.0)
        assert pf["gross_loss"] == pytest.approx(0.2)
        assert pf["profit_factor"] == pytest.approx(15.0)
        assert pf["margin_recorded"] == pytest.approx(15.0 - 1.10)
        assert ev["rules"]["R5"]["pass"] is True
        assert "coincides" in ev["rules"]["R5"]["coincidence_note"]
        assert ev["rules"]["R6"]["drop_one_all_positive"] is True
        assert ev["rules"]["R6"]["concentration"]["status"] == "MEASURED"

    def test_r1_fail(self):
        ev = rn.evaluate_r1_r6([-1.0, -1.0], [1, 2],
                               self._battery(False), None)
        assert ev["rules"]["R1"]["pass"] is False
        assert ev["rules"]["R1"]["mean_edge"] == pytest.approx(-1.0)
        # R5 (single-tier coincidence) fails exactly with R1.
        assert ev["rules"]["R5"]["pass"] is False
        assert ev["rules"]["R5"]["mean_edge"] == \
            ev["rules"]["R1"]["mean_edge"]
        assert "R1" in ev["failed_rules"]
        assert ev["survivor"] == "NOT_A_SURVIVOR"

    def test_r2_control_kill(self):
        ev = rn.evaluate_r1_r6([1.0, 1.0, 1.0, -0.2], [1, 2, 3, 3],
                               self._battery(True), None)
        assert ev["rules"]["R2"]["pass"] is False
        assert ev["rules"]["R2"]["family_kill"] is True
        assert ev["rules"]["R2"]["killed_by"] == \
            ["LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL"]
        assert ev["failed_rules"] == ["R2"]
        assert ev["survivor"] == "NOT_A_SURVIVOR"

    def test_r2_not_run_never_passes(self):
        ev = rn.evaluate_r1_r6([1.0, 1.0], [1, 2], None, None)
        assert ev["rules"]["R2"]["status"] == "NOT_RUN_NO_BATTERY_INPUT"
        assert ev["rules"]["R2"]["pass"] is False
        assert ev["survivor"] == "NOT_A_SURVIVOR"

    def test_r3_requires_two_positive_folds(self):
        edges = [1.0, -0.5, -0.5]
        folds = [1, 2, 3]
        ev = rn.evaluate_r1_r6(edges, folds, self._battery(False), None)
        assert ev["rules"]["R3"]["positive_folds"] == 1
        assert ev["rules"]["R3"]["pass"] is False
        assert ev["rules"]["R3"]["fold_windows"] == \
            [list(w) for w in rr.FOLD_WINDOWS]
        # exactly two positive folds passes (2-of-3 law).
        ev2 = rn.evaluate_r1_r6([1.0, 1.0, -0.5], [1, 2, 3],
                                self._battery(False), None)
        assert ev2["rules"]["R3"]["pass"] is True

    def test_r4_profit_factor_bound(self):
        ev = rn.evaluate_r1_r6([2.0, -2.0], [1, 1],
                               self._battery(False), None)
        pf = ev["rules"]["R4"]
        assert pf["profit_factor"] == pytest.approx(1.0)
        assert pf["pass"] is False
        assert pf["margin_recorded"] == pytest.approx(-0.10)
        # no losing edge: PF UNDEFINED (recorded None, never infinite).
        ev2 = rn.evaluate_r1_r6([1.0, 2.0], [1, 1],
                                self._battery(False), None)
        pf2 = ev2["rules"]["R4"]
        assert pf2["profit_factor"] is None
        assert pf2["pass"] is False
        assert "undefined" in pf2["undefined_note"]

    def test_r6_drop_one_and_concentration(self):
        edges = [1.0, 1.0, -1.0, -1.0, 0.5, 0.5]
        folds = [1, 1, 2, 2, 3, 3]
        ev = rn.evaluate_r1_r6(edges, folds, self._battery(False), None)
        # drop-one-fold survival fails on fold 3 (mean 0.0, not > 0).
        assert ev["rules"]["R6"]["drop_one_fold"]["3"]["mean_excl_fold"] \
            == 0.0
        assert ev["rules"]["R6"]["drop_one_fold"]["3"]["positive"] is \
            False
        assert ev["rules"]["R6"]["pass"] is False
        # concentration leg: one instant carries > 50% of gross.
        ev2 = rn.evaluate_r1_r6(edges, folds, self._battery(False),
                                [1.0] * 5 + [100.0])
        conc = ev2["rules"]["R6"]["concentration"]
        assert conc["max_single_instant_share"] > 0.5
        assert conc["pass"] is False
        assert ev2["rules"]["R6"]["pass"] is False
        # NOT_RUN concentration leg never blocks the drop-one leg.
        ev3 = rn.evaluate_r1_r6([1.0, 1.0, 0.5], [1, 2, 3],
                                self._battery(False), None)
        assert ev3["rules"]["R6"]["concentration"]["status"] == \
            "NOT_RUN_NO_GROSS_INPUT"
        assert ev3["rules"]["R6"]["pass"] is True

    def test_law_refusals_and_unknown_roles(self):
        with pytest.raises(rr.RunnerLawError, match="length mismatch"):
            rn.evaluate_r1_r6([1.0], [1, 2], None, None)
        with pytest.raises(rr.RunnerLawError, match="killer roles"):
            rn.evaluate_r1_r6([1.0], [1], {"family_kill": False,
                                           "killed_by": [],
                                           "comparisons": [
                                               {"control_role": "X"}]},
                              None)

    def test_pbo_fail_closed_below_8_cells(self):
        rec = rn.pbo_record(3)
        assert rec["status"] == "NOT_RUN_FAIL_CLOSED_CELLS_LT_8"
        assert rec["n_cells"] == 3
        assert rec["pbo_min_cells"] == 8
        assert "never estimated, never imputed" in rec["reason"]
        paths = " ".join(str(c.get("path", "")) for c in rec["citations"])
        assert "PLAN_rates_ng1.md" in paths
        assert "PLAN_forex_ng1.md" in paths
        assert "PLAN_crypto_ng1.md" in paths
        assert "forex_ng1_run/selection_freeze.json" in paths
        commit = [c for c in rec["citations"]
                  if "commit_sha" in c][0]["commit_sha"]
        assert commit == "d0992d17df8e2dfde57c9a0806a5798f14021a4f"
        # >= 8 cells: still NOT_RUN at I, with a DISTINCT reason (Q-11).
        rec8 = rn.pbo_record(8)
        assert rec8["status"] == "NOT_RUN_I_NO_MEASUREMENT"
        assert rec8["status"] != rec["status"]


# ================================================================== #
# 8. Emission scanner + dry-run plumbing + i-gate                     #
# ================================================================== #

class TestEmissionScanner:
    def test_clean_payload(self):
        payload = {"arms": {"a": {"fills": 4, "marks": 2}},
                   "list": [{"counts": [1, 2]}]}
        scan = rn.scan_emission_for_outcome_tokens(payload)
        assert scan["clean"] is True
        assert scan["leaks"] == []

    def test_planted_leaks_caught_at_depth(self):
        base = {"arms": {"a": {"fills": 4}}}
        for planted in ({"x": [{"y": {"total_pnl": 1.0}}]},
                        {"WIN-RATE": 0.5},
                        {"nested": {"profitFactor": 1.2}},
                        {"deep": [[{"expectancy_per_decision": 0.1}]]},
                        {"sharpe_ratio": 1.1},
                        {"break_even_count": 3},
                        {"total_return": 0.1},
                        {"pf": 1.3},
                        {"drawdown_pct": 0.2}):
            bad = copy.deepcopy(base)
            bad.update(planted)
            scan = rn.scan_emission_for_outcome_tokens(bad)
            assert scan["clean"] is False, planted
            assert len(scan["leaks"]) == 1


class TestDryRunPlumbing:
    def test_structural_counts_synthetic_only(self):
        d = rn.dry_run_plumbing()
        assert d["mode"] == "DRY_RUN_PLUMBING_SYNTHETIC"
        assert d["synthetic"] is True and d["real_substrate"] is False
        assert d["scored"] is False
        assert len(d["cells"]) == 3
        digests = {c["arm_config_digest"] for c in d["cells"]}
        assert digests == set(FROZEN_DIGESTS.values())
        assert d["identity"]["cell_count"] == 3
        assert d["identity"]["arm_config_digests_pairwise_distinct"] \
            is True
        assert d["leak_scan"]["clean"] is True

    def test_arms_non_vacuous_books_consistent(self):
        d = rn.dry_run_plumbing()
        for arm_id, meta in d["arms"].items():
            assert meta["decisions_total"] > 0
            assert meta["state_events_nonzero"] > 0   # non-vacuous
            assert meta["decision_ids_pairwise_distinct"] is True
            assert meta["all_ledgers_dual_book_equality_ok"] is True
            # kernel row structure: 4 fills + 2 drag events per RT.
            assert meta["fills_total"] == 4 * meta["round_trips"]
            assert meta["cost_events_total"] == 2 * meta["round_trips"]
            # both leg orientations present across the arm's ledgers.
            assert len(meta["ledgers"]) == 4
            assert meta["holding_trading_days"] == 5

    def test_battery_section_frozen(self):
        d = rn.dry_run_plumbing()
        assert d["battery"]["killer_roles"] == list(bat.KILLER_ROLES)
        assert d["battery"]["k_misalign_sessions"] == 5
        assert d["battery"]["anchor_arm"] == \
            "RATESNG1-A5-P1-ARM-NEUTRAL"
        # Q-11 placebo alignment: the placebo head (k=5) plus the
        # anchor's UNDEFINED head (63) never enter any mean.
        pl = d["battery"]["q11_alignment_counts_synthetic"]["PLACEBO"]
        assert pl["n_instants"] == \
            d["arms"]["RATESNG1-A5-P1-ARM-NEUTRAL"]["decisions_total"]
        assert pl["dropped_undefined_side_a"] == \
            d["arms"]["RATESNG1-A5-P1-ARM-NEUTRAL"]["states_undefined"]
        assert pl["dropped_undefined_side_b"] == \
            pl["dropped_undefined_side_a"] + 5

    def test_rules_scaffold_pbo(self):
        d = rn.dry_run_plumbing()
        assert d["rules_scaffold"]["pbo"]["status"] == \
            "NOT_RUN_FAIL_CLOSED_CELLS_LT_8"
        assert d["rules_scaffold"]["fold_windows"] == \
            [list(w) for w in rr.FOLD_WINDOWS]
        assert len(d["rules_scaffold"]["frozen_rule_order"]) == 6

    def test_replay_byte_identical(self):
        a = json.dumps(rn.dry_run_plumbing(), sort_keys=True)
        b = json.dumps(rn.dry_run_plumbing(), sort_keys=True)
        assert a == b

    def test_i_gate_payload(self):
        row = {"command": "pytest tests/test_rates_ng1_i.py -q",
               "exit_code": 0, "verdict": "PASS"}
        gate = dryrun.build_i_gate_payload(BASE_SHA, tests_row=row)
        assert gate["schema"] == "rates_ng1_run/i_gate@1"
        assert gate["base_sha"] == BASE_SHA
        assert gate["branch"] == "orca/rates-ng1-integration"
        for item in ("1_family_runner", "2_control_battery",
                     "3_rules_r1_r6_pbo"):
            assert gate["items"][item]["verdict"] == "PASS"
        assert gate["items"]["4_tests"] == row
        assert gate["negative_scan"]["emission_leak_scan_clean"] is True
        assert gate["negative_scan"][
            "outcome_numbers_on_real_substrate"] == \
            "NONE_COMPUTED_IN_I"
        pins = gate["structural_values"]["committed_artifact_pins"]
        assert pins["selection_freeze_sha256"] == FREEZE_SHA256
        measured = pins["p2_grid_census_measured"]
        assert measured["p2_grid_census_sha256"] == CENSUS_SHA256
        assert measured["bookable_instants_len"] == 1918
        assert measured["grid_dates_len"] == 2170
        counts = pins["grid_counts_vs_freeze_cited"]
        assert counts["bookable_instants_match"] is True
        assert counts["grid_sessions_match"] is True
        assert gate["structural_values"]["s1"] == "SEALED_UNTOUCHED"


class TestLoadRepresentationSynthetic:
    def test_structural_assembly_on_stub_plane(self):
        """load_representation is structural plumbing: exercised here
        against a STUB plane with synthetic rows only (never real
        substrate in I)."""
        grid = fx.weekday_sessions("2019-01-07", 12)
        curve_rows = [{"date": d, "2 Yr": str(2.0 + i * 0.01),
                       "10 Yr": str(2.5 + i * 0.01),
                       "30 Yr": str(3.0 + i * 0.01)}
                      for i, d in enumerate(grid)]

        class FakePlane:
            def curve_rows_for_year(self, year: int) -> list[dict]:
                return [r for r in curve_rows if r["date"][:4] == str(
                    year)]

            def etp_rows(self, ticker: str) -> list[dict]:
                return [{"date": d, "close": 81.0 + i}
                        for i, d in enumerate(grid)]

        census = {"census": {
            "grid_dates": grid,
            "bookable_instants": [{"decision_session": d,
                                   "decision_utc": "u",
                                   "readable_bar_date": grid[max(0, i)],
                                   "session_index": i}
                                  for i, d in enumerate(grid)]}}
        rep = rn.load_representation(FakePlane(), census)
        assert rep["grid_dates"] == grid
        assert set(rep["curve_by_date"]) == set(grid)
        assert rep["curve_by_date"][grid[3]]["2 Yr"] == pytest.approx(
            2.03)
        assert set(rep["leg_closes"]) == {"SHY", "TLT"}
        assert len(rep["leg_closes"]["SHY"]) == len(grid)
        # instants pass through untouched (structural plumbing only).
        assert rep["instants"] == census["census"]["bookable_instants"]

    def test_real_census_shape_only(self):
        """Structural plumbing on the committed census: list LENGTHS
        and the instants' KEY SET only -- no series content, no PnL."""
        with open(CENSUS_PATH, "r", encoding="utf-8") as fh:
            census = json.load(fh)
        instants = census["census"]["bookable_instants"]
        assert len(instants) == 1918
        assert set(instants[0]) == {"decision_session", "decision_utc",
                                    "readable_bar_date",
                                    "session_index"}
        assert len(census["census"]["grid_dates"]) == 2170


# ================================================================== #
# standalone --dry-run-plumbing self-check                            #
# ================================================================== #

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="RATES-NG1 I-phase dry-run plumbing self-check "
                    "(SYNTHETIC data; structural counts only, no PnL)")
    ap.add_argument("--dry-run-plumbing", action="store_true",
                    help="run the self-check and print a verdict")
    args = ap.parse_args(argv)
    if not args.dry_run_plumbing:
        ap.print_help()
        return 1
    report = dryrun.dry_run_plumbing()
    replay = json.dumps(dryrun.dry_run_plumbing(), sort_keys=True) == \
        json.dumps(report, sort_keys=True)
    summary = {
        "verdict": "DRY_RUN_PLUMBING_CLEAN"
        if (report["leak_scan"]["clean"] and replay) else "DRY_RUN_DIRTY",
        "cells": len(report["cells"]),
        "arms": {a: {"decisions": m["decisions_total"],
                     "state_events": m["state_events_nonzero"],
                     "round_trips": m["round_trips"],
                     "fills": m["fills_total"],
                     "cost_events": m["cost_events_total"]}
                 for a, m in sorted(report["arms"].items())},
        "battery_killer_roles": report["battery"]["killer_roles"],
        "k_misalign_sessions": report["battery"]["k_misalign_sessions"],
        "pbo": report["rules_scaffold"]["pbo"]["status"],
        "leak_scan_clean": report["leak_scan"]["clean"],
        "replay_byte_identical": replay,
    }
    print(json.dumps(summary, indent=1))
    return 0 if summary["verdict"] == "DRY_RUN_PLUMBING_CLEAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
