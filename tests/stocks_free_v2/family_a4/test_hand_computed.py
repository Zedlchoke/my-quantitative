"""Hand-computed tiny fixture for the frozen A4 family (Z5 required test).

Five synthetic sectors x 300 frozen calendar sessions, crafted so every
frozen feature, every selection and every weight is hand-computable and
written here literally with its arithmetic.  Offline; no real data.

Fixture (see conftest.HAND_PLACEMENTS), decision at session index 272
(2019-01-31, the first session with the full 253-bar window):

  symbol   total growth c between t-252 (idx 20) and t-21 (idx 251)
           and number of equal log-jumps k inside that window
  AAA      c = 4.0, k = 4      -> mom = 4/1 - 1 = 3.0
  BBB      c = 3.0, k = 2      -> mom = 3/1 - 1 = 2.0
  CCC      c = 2.5, k = 2      -> mom = 2.5/1 - 1 = 1.5
  DDD      c = 2.0, k = 8      -> mom = 2/1 - 1 = 1.0
  EEE      c = 1.5, k = 4      -> mom = 1.5/1 - 1 = 0.5

  sigma_i = v_i * sqrt((231 - k_i) / (231 * k_i * 230)),  v_i = ln(c_i)
  (sample std, ddof=1, of k_i jumps of size v_i/k_i among 231 daily log
  returns; derived: mean = v/231, sum sq dev = v^2 (231-k)/(231 k)).

  mra_i = mom_i / sigma_i  ->  AAA 66.20 > DDD 62.99 > BBB 39.21
                               > EEE 37.72 > CCC 35.26
"""

from __future__ import annotations

import math
from statistics import stdev

import pytest

from research.stocks_free_v2.family_a4 import (
    ARM_ID_ANCHOR,
    ARM_ID_NEGCTRL,
    ARM_ID_NEIGHBOUR,
    build_arm_configs,
    compute_symbol_features,
    generate_target_book,
    normalize_capped,
    rank_select,
)
from tests.stocks_free_v2.family_a4._fixtures import (
    HAND_PLACEMENTS,
    HAND_SYMBOLS,
)

FORMATION = 252
SKIP = 21
SIGMA_OBS = FORMATION - SKIP  # 231 daily log returns in the formation window

DECISION_INDEX = 272  # 2019-01-31, first full 253-session window
FIRST_DECISION = "2019-01-31"
FIRST_FILL = "2019-02-01"


def expected_sigma(symbol: str) -> float:
    """Hand-computed sigma: stdev of the explicit 231-return multiset."""
    c, k, _ = HAND_PLACEMENTS[symbol]
    v = math.log(c)
    jump = v / k
    returns = [jump] * k + [0.0] * (SIGMA_OBS - k)
    return stdev(returns)


def hand_features(hand_inputs, symbol: str):
    tr = hand_inputs.tr[symbol]
    sessions = hand_inputs.sessions
    return compute_symbol_features(
        tr=tr,
        sessions=sessions,
        index=DECISION_INDEX,
        formation_sessions=FORMATION,
        skip_sessions=SKIP,
        symbol=symbol,
    )


class TestHandComputedFeatures:
    def test_mom_values_exact_by_construction(self, hand_inputs):
        for symbol, (c, _k, _idx) in HAND_PLACEMENTS.items():
            features = hand_features(hand_inputs, symbol)
            # mom = P(t-21)/P(t-252) - 1 = c/1 - 1 (all jumps inside window)
            assert features.mom == pytest.approx(c - 1.0, rel=1e-12)
            assert features.ready is True

    def test_sigma_values_hand_computed(self, hand_inputs):
        for symbol in HAND_SYMBOLS:
            features = hand_features(hand_inputs, symbol)
            assert features.sigma == pytest.approx(expected_sigma(symbol), rel=1e-9)
            # closed form cross-check: v * sqrt((231-k)/(231*k*230))
            c, k, _ = HAND_PLACEMENTS[symbol]
            closed = math.log(c) * math.sqrt(
                (SIGMA_OBS - k) / (SIGMA_OBS * k * (SIGMA_OBS - 1))
            )
            assert features.sigma == pytest.approx(closed, rel=1e-9)

    def test_mra_ranking_order_hand_computed(self, hand_inputs):
        mra = {s: hand_features(hand_inputs, s).mra for s in HAND_SYMBOLS}
        # AAA: 3.0/0.045315=66.20  DDD: 1.0/0.015876=62.99  BBB: 2.0/0.051002=39.21
        # EEE: 0.5/0.013255=37.72  CCC: 1.5/0.042540=35.26
        assert sorted(mra, key=lambda s: (-mra[s], s)) == [
            "AAA", "DDD", "BBB", "EEE", "CCC",
        ]
        assert mra["AAA"] > mra["DDD"] > mra["BBB"] > mra["EEE"] > mra["CCC"]


class TestHandComputedSelection:
    def test_anchor_top3(self, hand_inputs):
        anchor, _neighbour, _control = build_arm_configs(hand_inputs.spec)
        features = {s: hand_features(hand_inputs, s) for s in HAND_SYMBOLS}
        assert rank_select(features, anchor) == ("AAA", "BBB", "CCC")

    def test_neighbour_top3_differs_from_anchor(self, hand_inputs):
        _anchor, neighbour, _control = build_arm_configs(hand_inputs.spec)
        features = {s: hand_features(hand_inputs, s) for s in HAND_SYMBOLS}
        # risk normalization changes membership: DDD's low vol lifts its
        # mra above BBB and CCC
        assert rank_select(features, neighbour) == ("AAA", "DDD", "BBB")

    def test_control_bottom3_is_pure_sign_flip(self, hand_inputs):
        _anchor, _neighbour, control = build_arm_configs(hand_inputs.spec)
        features = {s: hand_features(hand_inputs, s) for s in HAND_SYMBOLS}
        # bottom-3 by mom, ties ascending symbol: EEE 0.5 < DDD 1.0 < CCC 1.5
        # (returned in rank order: the LOWEST momentum ranks first)
        assert rank_select(features, control) == ("EEE", "DDD", "CCC")


class TestHandComputedWeights:
    def test_anchor_equal_weight_literal(self, hand_inputs):
        anchor, _n, _c = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, anchor)
        first = next(
            e for e in stream.entries if e.decision_date == FIRST_DECISION
        )
        # equal weight: 1/3 each; gross 1.0; residual 0% to cash
        assert first.targets == {
            "AAA": pytest.approx(1 / 3),
            "BBB": pytest.approx(1 / 3),
            "CCC": pytest.approx(1 / 3),
        }
        assert first.gross == pytest.approx(1.0)
        assert first.cash_weight == pytest.approx(0.0)

    def test_neighbour_inverse_vol_with_cap_literal(self, hand_inputs):
        _a, neighbour, _c = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, neighbour)
        first = next(
            e for e in stream.entries if e.decision_date == FIRST_DECISION
        )
        sigma = {s: expected_sigma(s) for s in ("AAA", "DDD", "BBB")}
        inv = {s: 1.0 / sigma[s] for s in sigma}
        # raw normalized shares: AAA inv/sum, DDD inv/sum, BBB inv/sum
        total = sum(inv.values())
        raw_ddd = inv["DDD"] / total
        assert raw_ddd > 0.35  # DDD's low vol breaches the frozen cap
        # cap arithmetic: pin DDD at 0.35; redistribute 0.65 between the
        # uncapped AAA and BBB proportional to their 1/sigma
        exp_ddd = 0.35
        exp_aaa = 0.65 * inv["AAA"] / (inv["AAA"] + inv["BBB"])
        exp_bbb = 0.65 * inv["BBB"] / (inv["AAA"] + inv["BBB"])
        assert first.targets["DDD"] == pytest.approx(exp_ddd, abs=1e-9)
        assert first.targets["AAA"] == pytest.approx(exp_aaa, abs=1e-9)
        assert first.targets["BBB"] == pytest.approx(exp_bbb, abs=1e-9)
        assert first.targets["AAA"] < 0.35 and first.targets["BBB"] < 0.35
        assert first.gross == pytest.approx(1.0)

    def test_control_weights_equal_anchor_scheme(self, hand_inputs):
        _a, _n, control = build_arm_configs(hand_inputs.spec)
        stream = generate_target_book(hand_inputs, control)
        first = next(
            e for e in stream.entries if e.decision_date == FIRST_DECISION
        )
        # identical weighting scheme, identical 1/3 slots, different legs
        assert set(first.targets) == {"CCC", "DDD", "EEE"}
        for weight in first.targets.values():
            assert weight == pytest.approx(1 / 3)


class TestNormalizeCappedUnit:
    def test_binding_cap_hand_case(self):
        # raw inverse-vols (0.5, 1, 1) -> shares (0.2, 0.4, 0.4);
        # B and C breach 0.35 -> pin both, A takes the 0.30 residual
        out = normalize_capped({"A": 0.5, "B": 1.0, "C": 1.0}, 0.35)
        assert out["A"] == pytest.approx(0.30, abs=1e-12)
        assert out["B"] == pytest.approx(0.35, abs=1e-12)
        assert out["C"] == pytest.approx(0.35, abs=1e-12)

    def test_single_breach_hand_case(self):
        # raw inverse-vols (2, 1, 1) -> shares (0.5, 0.25, 0.25);
        # A breaches 0.35 -> pin A, redistribute 0.65 between B and C (1:1)
        out = normalize_capped({"A": 2.0, "B": 1.0, "C": 1.0}, 0.35)
        assert out["A"] == pytest.approx(0.35, abs=1e-12)
        assert out["B"] == pytest.approx(0.325, abs=1e-12)
        assert out["C"] == pytest.approx(0.325, abs=1e-12)

    def test_exact_cap_edge_no_redistribution(self):
        # raw (7, 7, 6) -> shares (7/20, 7/20, 6/20) = (0.35, 0.35, 0.30):
        # the two 0.35 names sit exactly AT the frozen cap (<= cap), so no
        # redistribution fires
        out = normalize_capped({"A": 7.0, "B": 7.0, "C": 6.0}, 0.35)
        assert out["A"] == pytest.approx(0.35, abs=1e-12)
        assert out["B"] == pytest.approx(0.35, abs=1e-12)
        assert out["C"] == pytest.approx(0.30, abs=1e-12)

    def test_cap_redistributes_proportionally(self):
        # raw (6, 6, 7) -> shares (6/19, 6/19, 7/19): C breaches 0.35 ->
        # pin C, A and B split the 0.65 evenly (equal raw)
        out = normalize_capped({"A": 6.0, "B": 6.0, "C": 7.0}, 0.35)
        assert out["A"] == pytest.approx(0.325, abs=1e-12)
        assert out["B"] == pytest.approx(0.325, abs=1e-12)
        assert out["C"] == pytest.approx(0.35, abs=1e-12)

    def test_uniform_case(self):
        out = normalize_capped({"A": 1.0, "B": 1.0, "C": 1.0}, 0.35)
        for value in out.values():
            assert value == pytest.approx(1 / 3)

    def test_fails_closed_on_non_positive_raw(self):
        import pytest as _pytest

        with _pytest.raises(ValueError):
            normalize_capped({"A": 0.0, "B": 1.0}, 0.35)


class TestExpectedSignFixture:
    """Spec: 'at every decision the selected legs' prior 12-1 TR must exceed
    the unselected legs' for the anchor and invert for the control'."""

    def test_anchor_beats_unselected_and_control_inverts(self, hand_inputs):
        anchor, _n, control = build_arm_configs(hand_inputs.spec)
        sessions = hand_inputs.sessions
        for stream, config, inverted in (
            (generate_target_book(hand_inputs, anchor), anchor, False),
            (generate_target_book(hand_inputs, control), control, True),
        ):
            decisions = [e for e in stream.entries if e.entry_type == "decision_fill"]
            assert decisions, config.arm_id
            for entry in decisions:
                index = sessions.index(entry.decision_date)
                mom = {
                    s: compute_symbol_features(
                        tr=hand_inputs.tr[s],
                        sessions=sessions,
                        index=index,
                        formation_sessions=FORMATION,
                        skip_sessions=SKIP,
                        symbol=s,
                    ).mom
                    for s in HAND_SYMBOLS
                }
                selected, unselected = set(entry.targets), set()
                for s in HAND_SYMBOLS:
                    (selected if s in entry.targets else unselected).add(s)
                sel_scores = [mom[s] for s in selected]
                unsel_scores = [mom[s] for s in unselected]
                if inverted:
                    assert max(sel_scores) < min(unsel_scores)
                else:
                    assert min(sel_scores) > max(unsel_scores)
