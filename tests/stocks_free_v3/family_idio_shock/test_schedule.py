"""Hand-computed schedule goldens for the frozen state machine (A1/N1/C1).

Every expected fill date, weight, turnover and z below is derived by hand in
tests/stocks_free_v3/family_idio_shock/conftest.py (closed forms) and from
the frozen clocks: decision at close of session t -> fill at close of t+1 ->
exit fill at close of entry+hold (ADJ-1-EXEC-CLOCK).  SCHEDULE-ONLY: no PnL
is computed anywhere in this module.
"""

from __future__ import annotations

import pytest

from research.assets.common.contracts import canonical_json
from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v3.family_idio_shock.arms import ARM_A1, ARM_C1, ARM_N1
from research.stocks_free_v3.family_idio_shock.features import compute_features
from research.stocks_free_v3.family_idio_shock.schedule import (
    ScheduleError,
    build_arm_schedule,
    build_arm_schedule_from_features,
    entries_in_budget_window,
    schedule_feasibility,
)

from tests.stocks_free_v3.family_idio_shock.conftest import (
    Z_ONE_SHOCK,
    shock_fixture,
)


# --------------------------------------------------------------------------- #
# Anchor A1 golden: one -0.06 idio shock on AAA at session index 62.
# --------------------------------------------------------------------------- #
def test_a1_single_shock_hand_schedule(single_shock):
    sessions, returns = single_shock
    result = build_arm_schedule(ARM_A1, sessions, returns)
    assert result.n_triggers_observed == 1
    assert result.n_entries_committed == 1
    assert result.n_budget_rejections == 0
    assert result.n_concurrency_blocks == 0
    assert result.n_same_close_switches == 0
    # hand schedule: decision at close of index 62 (z = -60/sqrt(59) <= -3),
    # entry fill at close of index 63, exit fill at close of index 68.
    assert [r["kind"] for r in result.records] == ["ENTRY", "EXIT"]
    entry, exit_ = result.records
    assert entry["fill_date"] == sessions[63]
    assert entry["decision_date"] == sessions[62]
    assert entry["targets"] == {"XLK": 0.5, CASH_SYMBOL: 0.5}
    assert entry["cash_weight"] == 0.5
    assert entry["turnover_one_way"] == pytest.approx(0.5)  # from all-cash
    assert entry["symbol"] == "XLK"
    assert entry["z_at_decision"] == pytest.approx(Z_ONE_SHOCK, rel=1e-12)
    assert entry["episode"] == 1
    assert exit_["fill_date"] == sessions[68]  # 63 + hold(5), close-to-close
    assert exit_["targets"] == {CASH_SYMBOL: 1.0}
    assert exit_["cash_weight"] == 1.0
    assert exit_["turnover_one_way"] == pytest.approx(0.5)
    assert exit_["episode"] == 1
    # gross exposure is 0.5 on holding fills and 0.0 otherwise
    feas = schedule_feasibility(sessions, result, ARM_A1)
    assert feas.max_gross_observed == pytest.approx(0.5)
    assert feas.gross_within_limit is True
    # one episode in 80 sessions = 1 / (80/252) entries per year
    assert feas.entries_per_year == pytest.approx(1.0 / (80 / 252))
    # two-way turnover = 0.5 buy + 0.5 sell = 1.0 over 80 sessions
    assert feas.turnover_one_way_total == pytest.approx(1.0)
    assert feas.turnover_two_way_per_year == pytest.approx(1.0 / (80 / 252))
    assert feas.within_turnover_ceiling is True


def test_n1_single_shock_exits_ten_sessions_later(single_shock):
    sessions, returns = single_shock
    result = build_arm_schedule(ARM_N1, sessions, returns)
    assert [r["kind"] for r in result.records] == ["ENTRY", "EXIT"]
    entry, exit_ = result.records
    assert entry["fill_date"] == sessions[63]
    assert exit_["fill_date"] == sessions[73]  # 63 + hold(10)
    assert exit_["turnover_one_way"] == pytest.approx(0.5)


def test_c1_never_triggers_on_negative_shocks(single_shock):
    sessions, returns = single_shock
    result = build_arm_schedule(ARM_C1, sessions, returns)
    assert result.records == ()
    assert result.n_triggers_observed == 0
    feas = schedule_feasibility(sessions, result, ARM_C1)
    assert feas.n_entries_committed == 0
    assert feas.turnover_one_way_total == 0.0
    assert feas.max_gross_observed == 0.0


def test_c1_longs_a_positive_shock_with_matching_structure():
    """The control enters LONG on z >= +3 (mirror of the anchor).  Expected
    mechanism direction (static): non-positive alpha — a long book on a
    transitory POSITIVE idio overshoot buys what must revert."""
    sessions, returns = shock_fixture(80, {"XLF": {62: +0.08}})
    result = build_arm_schedule(ARM_C1, sessions, returns)
    assert [r["kind"] for r in result.records] == ["ENTRY", "EXIT"]
    entry, exit_ = result.records
    assert entry["fill_date"] == sessions[63]
    assert entry["targets"] == {"XLF": 0.5, CASH_SYMBOL: 0.5}
    assert entry["z_at_decision"] == pytest.approx(-Z_ONE_SHOCK, rel=1e-12)
    assert exit_["fill_date"] == sessions[68]


# --------------------------------------------------------------------------- #
# Selection rules.
# --------------------------------------------------------------------------- #
def test_tie_breaks_to_alphabetically_first_symbol():
    """Two symbols with BIT-IDENTICAL shock series: identical z -> the
    alphabetically first symbol is selected."""
    shock = {62: -0.06}
    sessions, returns = shock_fixture(80, {"XLE": dict(shock), "XLB": dict(shock)})
    result = build_arm_schedule(ARM_A1, sessions, returns)
    assert result.n_triggers_observed == 1
    assert result.records[0]["symbol"] == "XLB"


def test_smallest_z_wins_among_simultaneous_triggers():
    """P carries one shock in its window (z = -60/sqrt(59) = -7.814); Q
    carries TWO equal shocks (z = -30/sqrt(29) = -5.571).  Both breach -3;
    the more extreme z must be selected."""
    sessions, returns = shock_fixture(
        80, {"XLY": {62: -0.06}, "XLU": {50: -0.05, 62: -0.05}})
    result = build_arm_schedule(ARM_A1, sessions, returns)
    entry = result.records[0]
    assert entry["symbol"] == "XLY"
    assert entry["z_at_decision"] == pytest.approx(Z_ONE_SHOCK, rel=1e-12)
    assert result.n_triggers_observed == 1  # one decision, two candidates


def test_largest_z_wins_for_the_control():
    sessions, returns = shock_fixture(
        80, {"XLY": {62: +0.06}, "XLU": {50: +0.05, 62: +0.05}})
    result = build_arm_schedule(ARM_C1, sessions, returns)
    entry = result.records[0]
    assert entry["symbol"] == "XLY"  # largest z (least-shocked construction wins)


# --------------------------------------------------------------------------- #
# Clocks: same-close switch, concurrency 1, budget.
# --------------------------------------------------------------------------- #
def test_same_close_switch_a1_hand_schedule():
    """AAA shocked at 62 (decision 62 -> fill 63 -> exit 68); BBB shocked at
    67 (decision 67 -> fill 68 == exit session): a PIT-clean same-close
    switch.  Hand schedule: ENTRY XLK @63 (turnover 0.5), SWITCH BBB @68
    (both legs, turnover 1.0), EXIT @73 (0.5)."""
    sessions, returns = shock_fixture(
        80, {"XLK": {62: -0.06}, "XLE": {67: -0.06}})
    result = build_arm_schedule(ARM_A1, sessions, returns)
    assert result.n_same_close_switches == 1
    assert [(r["kind"], r["fill_date"]) for r in result.records] == [
        ("ENTRY", sessions[63]), ("SWITCH", sessions[68]),
        ("EXIT", sessions[73]),
    ]
    entry, switch, exit_ = result.records
    assert entry["targets"] == {"XLK": 0.5, CASH_SYMBOL: 0.5}
    assert switch["targets"] == {"XLE": 0.5, CASH_SYMBOL: 0.5}
    assert switch["turnover_one_way"] == pytest.approx(1.0)  # both legs
    assert switch["decision_date"] == sessions[67]
    assert switch["z_at_decision"] == pytest.approx(Z_ONE_SHOCK, rel=1e-12)
    assert switch["episode"] == 2
    assert exit_["targets"] == {CASH_SYMBOL: 1.0}
    assert exit_["episode"] == 2
    feas = schedule_feasibility(sessions, result, ARM_A1)
    assert feas.turnover_one_way_total == pytest.approx(2.0)
    assert feas.n_same_close_switches == 1


def test_concurrency_one_blocks_the_neighbour_at_hold_ten():
    """N1 (hold 10): the second shock's fill (68) lands while the first
    episode is open until 73 -> the trigger is ignored, no switch exists."""
    sessions, returns = shock_fixture(
        80, {"XLK": {62: -0.06}, "XLE": {67: -0.06}})
    result = build_arm_schedule(ARM_N1, sessions, returns)
    assert result.n_concurrency_blocks == 1
    assert [(r["kind"], r["fill_date"]) for r in result.records] == [
        ("ENTRY", sessions[63]), ("EXIT", sessions[73]),
    ]
    assert result.records[0]["symbol"] == "XLK"


def test_rolling_budget_suppresses_the_sixth_entry():
    """Shocks every 8 sessions from 62 (all on r_SPY=0 positions): entries at
    63,71,79,87,95 fill; the 6th (103) and 7th (111) candidates sit inside a
    252-session window that already holds 5 entries -> suppressed."""
    shocks = {"XLK": {k: -0.06 for k in (62, 70, 78, 86, 94, 102, 110)}}
    sessions, returns = shock_fixture(130, shocks)
    result = build_arm_schedule(ARM_A1, sessions, returns)
    assert result.n_entries_committed == 5
    assert result.n_budget_rejections == 2
    assert result.n_triggers_observed == 7
    entries = [r for r in result.records if r["kind"] == "ENTRY"]
    assert [r["fill_date"] for r in entries] == [
        sessions[i] for i in (63, 71, 79, 87, 95)]
    # every entry exits exactly 5 sessions later
    exits = [r for r in result.records if r["kind"] == "EXIT"]
    assert [r["fill_date"] for r in exits] == [
        sessions[i] for i in (68, 76, 84, 92, 100)]


def test_budget_gate_pure_helper_rolls_off():
    # 5 priors inside [1..5]; candidate 252 -> window [1,252] holds 5 priors -> full
    assert entries_in_budget_window(252, [1, 2, 3, 4, 5], 252, 5) is False
    # candidate 253 -> window [2,253] holds 4 priors -> one slot left
    assert entries_in_budget_window(253, [1, 2, 3, 4, 5], 252, 5) is True
    # the candidate itself is never counted as its own prior
    assert entries_in_budget_window(10, [10], 252, 5) is True
    assert entries_in_budget_window(6, [1, 2, 3, 4, 5], 252, 5) is False


def test_data_edge_entry_never_holding_becomes_force_flat():
    """A shock at the second-to-last session fills at the final close, where
    its hold cannot fit: the canonical record is the terminal FORCE_FLAT."""
    sessions, returns = shock_fixture(64, {"XLK": {62: -0.06}})
    assert 62 == len(sessions) - 2
    result = build_arm_schedule(ARM_A1, sessions, returns)
    assert result.n_entries_committed == 1
    assert len(result.records) == 1
    record = result.records[0]
    assert record["entry_type"] == "FORCE_FLAT"
    assert record["fill_date"] == sessions[63]
    assert record["targets"] == {CASH_SYMBOL: 1.0}
    assert record["turnover_one_way"] == pytest.approx(0.0)


def test_window_end_flat_closes_an_open_position():
    """Hold 10 (N1) with the list ending before the exit: the position is
    force-flattened at the last session."""
    sessions, returns = shock_fixture(70, {"XLK": {62: -0.06}})  # exit would be 73
    result = build_arm_schedule(ARM_N1, sessions, returns)
    assert [(r["kind"], r["fill_date"]) for r in result.records] == [
        ("ENTRY", sessions[63]), ("WINDOW_END_FLAT", sessions[69])]
    flat = result.records[1]
    assert flat["entry_type"] == "FORCE_FLAT"
    assert flat["turnover_one_way"] == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# Double-generation equality (byte-identical schedules via two code paths).
# --------------------------------------------------------------------------- #
def test_double_generation_byte_identical():
    fixture = {"XLK": {62: -0.06}, "XLE": {67: -0.06}}
    sessions, returns = shock_fixture(90, fixture)
    for arm in (ARM_A1, ARM_N1, ARM_C1):
        direct = build_arm_schedule(arm, sessions, returns)          # path 1
        cached = compute_features(sessions, returns, arm.universe, "SPY")
        from_cached = build_arm_schedule_from_features(arm, sessions, cached)
        regenerated = compute_features(sessions, returns, arm.universe, "SPY")
        from_regen = build_arm_schedule_from_features(arm, sessions, regenerated)
        assert direct.records == from_cached.records == from_regen.records
        assert direct.schedule_digest == from_cached.schedule_digest \
            == from_regen.schedule_digest
        # byte-identical canonical JSON of the full record lists
        assert canonical_json({"records": list(direct.records)}) == \
            canonical_json({"records": list(from_cached.records)}) == \
            canonical_json({"records": list(from_regen.records)})


def test_schedule_digest_is_stable_across_repeat_builds(single_shock):
    sessions, returns = single_shock
    first = build_arm_schedule(ARM_A1, sessions, returns)
    second = build_arm_schedule(ARM_A1, sessions, returns)
    assert first.schedule_digest == second.schedule_digest
    assert first.to_payload() == second.to_payload()


# --------------------------------------------------------------------------- #
# Invariant guard: schedules that breach frozen invariants fail closed.
# --------------------------------------------------------------------------- #
def test_invariant_guard_rejects_bad_records():
    from research.stocks_free_v3.family_idio_shock.schedule import (
        _assert_schedule_invariants,
    )
    bad = [{
        "entry_type": "FILL", "fill_date": "2020-01-06",
        "targets": {"AAA": 0.9, CASH_SYMBOL: 0.1}, "cash_weight": 0.1,
        "turnover_one_way": 0.9, "kind": "ENTRY",
    }]
    with pytest.raises(ScheduleError, match="non-frozen ETF weight"):
        _assert_schedule_invariants(ARM_A1, bad, [0])
    non_ascending = [
        {"entry_type": "FILL", "fill_date": "2020-01-07",
         "targets": {"AAA": 0.5, CASH_SYMBOL: 0.5}, "cash_weight": 0.5,
         "turnover_one_way": 0.5, "kind": "ENTRY"},
        {"entry_type": "FILL", "fill_date": "2020-01-06",
         "targets": {CASH_SYMBOL: 1.0}, "cash_weight": 1.0,
         "turnover_one_way": 0.5, "kind": "EXIT"},
    ]
    with pytest.raises(ScheduleError, match="ascending"):
        _assert_schedule_invariants(ARM_A1, non_ascending, [0, 1])
    over_budget = [
        {"entry_type": "FILL", "fill_date": str(i), "targets": {},
         "cash_weight": 1.0, "turnover_one_way": 0.0, "kind": "ENTRY"}
        for i in range(6)
    ]
    with pytest.raises(ScheduleError, match="episode budget breached"):
        _assert_schedule_invariants(ARM_A1, over_budget, list(range(6)))


def test_feasibility_rejects_empty_sessions():
    from research.stocks_free_v3.family_idio_shock.schedule import ScheduleResult
    empty = ScheduleResult(ARM_A1.arm_id, ARM_A1.config_digest, "d" * 64, (),
                           0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ScheduleError, match="non-empty session list"):
        schedule_feasibility([], empty, ARM_A1)
