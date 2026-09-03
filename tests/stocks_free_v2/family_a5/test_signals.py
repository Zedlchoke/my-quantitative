"""Hand-computed feature/gate tests for family_a5.signals (frozen definitions)."""

import math
from datetime import date

import pytest


def test_frozen_signal_constants(a5):
    """Spec-pinned estimator constants; nothing here was chosen at Z5 time."""
    s = a5.signals
    assert s.TSMOM_LOOKBACK_SESSIONS == 252  # arm1/arm3 feature lookback
    assert s.SMA_WINDOW_SESSIONS == 200  # arm2 feature window
    assert s.VOL_WINDOW_SESSIONS == 63  # realized-vol window (all arms)
    assert s.VOL_DDOF == 1  # ddof=1 per spec
    assert s.ANNUALIZATION_SESSIONS == 252.0  # sqrt(252) annualization


class TestTsmomGate:
    def test_hand_computed_momentum_and_sign(self, a5):
        # TR chain S = [100, 102, 101, 105, 110, 120] on sessions d0..d5.
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 6)
        tr = {"S": {d: v for d, v in zip(sessions, [100.0, 102.0, 101.0, 105.0, 110.0, 120.0])}}
        d5 = sessions[5]
        # lookback=4 at d5: TR(t-4) is d1=102, so m = 120/102 - 1 = 0.1764705882 > 0
        m4 = s.tsmom_momentum(tr["S"], sessions, "S", d5, lookback_sessions=4)
        assert m4 == pytest.approx(120.0 / 102.0 - 1.0)
        assert s.tsmom_eligible(tr["S"], sessions, "S", d5, lookback_sessions=4) is True
        # inverted control: m < 0 required -> +0.176 is NOT eligible
        assert (
            s.tsmom_eligible(tr["S"], sessions, "S", d5, lookback_sessions=4, inverted_sign=True)
            is False
        )
        # lookback=4 needs exactly 5 points through t; at d4 the anchor is d0:
        # m = 110/100 - 1 = 0.1
        d4 = sessions[4]
        assert s.tsmom_momentum(tr["S"], sessions, "S", d4, lookback_sessions=4) == pytest.approx(0.1)
        # falling chain: TR = [100, 90] -> m = -0.1 < 0: anchor OUT, control IN
        tr_dn = {"F": {sessions[0]: 100.0, sessions[1]: 90.0}}
        assert s.tsmom_eligible(tr_dn["F"], sessions[:2], "F", sessions[1], lookback_sessions=1) is False
        assert (
            s.tsmom_eligible(
                tr_dn["F"], sessions[:2], "F", sessions[1], lookback_sessions=1, inverted_sign=True
            )
            is True
        )

    def test_insufficient_history_fails_closed(self, a5):
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 4)
        tr = {d: 100.0 + i for i, d in enumerate(sessions)}
        # lookback=4 needs 5 completed points; d3 has only 4 -> ValueError (never guesses)
        with pytest.raises(ValueError):
            s.tsmom_momentum(tr, sessions, "S", sessions[3], lookback_sessions=4)

    def test_exact_zero_momentum_ineligible_under_both_signs(self, a5):
        # m = 100/100 - 1 = 0 exactly -> INELIGIBLE for anchor AND control (tie-break).
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 2)
        tr = {sessions[0]: 100.0, sessions[1]: 100.0}
        assert s.tsmom_momentum(tr, sessions, "E", sessions[1], lookback_sessions=1) == 0.0
        assert s.tsmom_eligible(tr, sessions, "E", sessions[1], lookback_sessions=1) is False
        assert (
            s.tsmom_eligible(tr, sessions, "E", sessions[1], lookback_sessions=1, inverted_sign=True)
            is False
        )

    def test_no_lookahead_decision_uses_only_sessions_through_t(self, a5):
        # A shock strictly after the decision date cannot move the feature...
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 6)
        base = [100.0, 102.0, 101.0, 105.0, 110.0, 120.0]
        tr_a = {d: v for d, v in zip(sessions, base)}
        mutated = list(base)
        mutated[5] = 1000.0  # shock on d5
        tr_b = {d: v for d, v in zip(sessions, mutated)}
        d4 = sessions[4]
        assert s.tsmom_momentum(tr_a, sessions, "S", d4, lookback_sessions=4) == s.tsmom_momentum(
            tr_b, sessions, "S", d4, lookback_sessions=4
        )
        # ...and mutating an input the feature DOES read (the t-4 anchor) moves it.
        mutated_past = list(base)
        mutated_past[0] = 200.0  # d0 is the t-4 anchor for the d4 decision
        tr_c = {d: v for d, v in zip(sessions, mutated_past)}
        assert s.tsmom_momentum(tr_c, sessions, "S", d4, lookback_sessions=4) != s.tsmom_momentum(
            tr_a, sessions, "S", d4, lookback_sessions=4
        )


class TestSmaGate:
    def test_hand_computed_sma_and_tie(self, a5):
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 6)
        tr = {d: v for d, v in zip(sessions, [100.0, 102.0, 101.0, 105.0, 110.0, 120.0])}
        d5 = sessions[5]
        # window=3: sma = (105+110+120)/3 = 111.666666...; TR(t)=120 > sma -> ELIGIBLE
        assert s.sma_value(tr, sessions, "S", d5, window_sessions=3) == pytest.approx(111.66666666666667)
        assert s.sma_eligible(tr, sessions, "S", d5, window_sessions=3) is True
        # window=5 at d4: sma = (100+102+101+105+110)/5 = 518/5 = 103.6; 110 > 103.6
        d4 = sessions[4]
        assert s.sma_value(tr, sessions, "S", d4, window_sessions=5) == pytest.approx(103.6)
        assert s.sma_eligible(tr, sessions, "S", d4, window_sessions=5) is True
        # exact tie: TR == sma -> INELIGIBLE (price-above-only threshold)
        flat = {sessions[0]: 100.0, sessions[1]: 100.0}
        assert s.sma_eligible(flat, sessions[:2], "T", sessions[1], window_sessions=2) is False
        # below the mean: falling tail (90 after 100) -> mean(100, 90) = 95 > 90
        dn = {sessions[0]: 100.0, sessions[1]: 90.0}
        assert s.sma_eligible(dn, sessions[:2], "D", sessions[1], window_sessions=2) is False

    def test_insufficient_history_fails_closed(self, a5):
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 3)
        tr = {d: 100.0 + i for i, d in enumerate(sessions)}
        with pytest.raises(ValueError):
            s.sma_value(tr, sessions, "S", sessions[2], window_sessions=5)

    def test_no_lookahead_future_value_cannot_move_sma(self, a5):
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 6)
        base = [100.0, 102.0, 101.0, 105.0, 110.0, 120.0]
        d4 = sessions[4]
        tr_a = {d: v for d, v in zip(sessions, base)}
        tr_b = {d: v for d, v in zip(sessions, [100.0, 102.0, 101.0, 105.0, 110.0, 999.0])}
        assert s.sma_value(tr_a, sessions, "S", d4, window_sessions=5) == s.sma_value(
            tr_b, sessions, "S", d4, window_sessions=5
        )


class TestRealizedVol:
    def test_zero_vol_constant_returns(self, a5):
        # 100 * 1.01**i has simple returns 0.01 up to float rounding
        # (~1e-16), so std(ddof=1) vanishes to float dust, not exactly 0.
        s = a5.signals
        values = [100.0 * 1.01 ** i for i in range(80)]
        assert s.realized_vol_annualized(values, window_sessions=63) == pytest.approx(0.0, abs=1e-12)

    def test_hand_computed_sigma(self, a5):
        # Returns [+0.01, -0.01, +0.01, -0.01] from TR [100, 101, 99.99, 100.9899, 99.980001].
        # mean = 0; var(ddof=1) = 4*0.0001/3 = 0.0004/3;
        # sigma_ann = sqrt(0.0004/3) * sqrt(252) = sqrt(0.0004 * 252 / 3) = sqrt(0.0336)
        #           = 0.18330302552021538...
        s = a5.signals
        values = [100.0, 101.0, 99.99, 100.9899, 99.980001]
        sigma = s.realized_vol_annualized(values, window_sessions=4)
        assert sigma == pytest.approx(math.sqrt(0.0336))
        assert sigma == pytest.approx(0.18330302552021538)

    def test_needs_window_returns_not_points(self, a5):
        s = a5.signals
        with pytest.raises(ValueError):
            s.realized_vol_annualized([100.0] * 64, window_sessions=63 + 1)

    def test_per_symbol_vol_ignores_future_sessions(self, a5):
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 10)
        tr = {d: 100.0 * 1.01 ** i for i, d in enumerate(sessions)}
        d8 = sessions[8]
        shocked = dict(tr)
        shocked[sessions[9]] = tr[sessions[9]] * 3.0  # shock AFTER the decision date
        assert s.realized_vol_for_symbol(tr, sessions, "X", d8, window_sessions=4) == (
            s.realized_vol_for_symbol(shocked, sessions, "X", d8, window_sessions=4)
        )


class TestArenaVol:
    def test_hand_computed_arena(self, a5):
        # sigma_arena = sqrt(mean(sigma_i^2)) = sqrt((0.04 + 0.09)/2) = sqrt(0.065)
        s = a5.signals
        assert s.arena_volatility({"A": 0.20, "B": 0.30}) == pytest.approx(math.sqrt(0.065))
        assert s.arena_volatility({}) == 0.0  # empty eligible set -> 0.0 (declared)


class TestRampRequirement:
    def test_feature_requirements(self, a5):
        # TSMOM needs TR(t-252) to exist -> 253 points through t (frozen formula
        # m = TR(t)/TR(t-252) - 1 is the binding authority); SMA needs 200.
        s = a5.signals
        assert s.feature_requirement_sessions("TSMOM_SIGN", 252) == 253
        assert s.feature_requirement_sessions("SMA_ABOVE", 200) == 200
        with pytest.raises(ValueError):
            s.feature_requirement_sessions("UNKNOWN", 10)

    def test_completed_session_count_skips_missing_points(self, a5):
        s = a5.signals
        sessions = a5.make_sessions(date(2018, 1, 1), 5)
        tr = {d: 100.0 + i for i, d in enumerate(sessions) if i != 2}  # gap on d2
        # gaps are returns, never fabricated: only present points count
        assert s.completed_session_count(tr, sessions, sessions[4]) == 4
