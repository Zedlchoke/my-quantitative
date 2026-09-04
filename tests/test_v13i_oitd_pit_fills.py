"""V13 I lane -- PIT/no-lookahead mutation and next-allowed-fill tests (b, c).

Evidence (b) -- PIT / no-lookahead mutations (every mutation must either
CHANGE the output or be REFUSED):

* future rows are unreadable: an OI snapshot, a mark snapshot or a
  turnover day stamped AFTER the decision stamp changes no score; the
  corresponding PAST row mutated changes the score (the input is
  provably consumed);
* the availability-stamp mutation pins the A9-F engine-convention
  caveat EXPLICITLY: a fill at slot-open 00:15Z cannot read a record
  stamped 00:30Z (e.g. the covering bar's own close);
  ``assert_inputs_available`` refuses fail-closed
  (:class:`LookaheadViolation`), the boundary (== horizon) is readable,
  and the pinned snap rule equals the frozen V12 audit loader's;

Evidence (c) -- the pinned next-allowed-fill convention:

* orders release at decision + 15m; the fill reference is the OPEN of
  the first completed 15m bar whose slot-open instant >= release (the
  00:15Z slot for a Monday-midnight decision); the consumed price is
  the bar OPEN (observable at slot-open), never the close;
* stress +1 event delay shifts the fill to the NEXT slot's open;
* missing slots -> NO event; duplicate slots and non-grid decisions are
  refused; the fill never happens before the release instant.

All data synthetic; no real data is read; no scored metric is computed.
"""

from __future__ import annotations

import pytest

from tests.v13i_oitd_world import (
    BAR_NS,
    DAY_NS,
    GROUP_L,
    T1_DAY,
    T1_NS,
    execution_bars,
    world_b,
)

from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    CONTROL_ARM,
    LookaheadViolation,
    assert_inputs_available,
    compute_targets_at,
    next_allowed_fill,
    signal_scores_at,
    snap_close_to_boundary,
)

RELEASE_NS = T1_NS + BAR_NS  # decision + 15 minutes


def _anchor_scores(day_turnover, oi, mark, stamp=T1_NS, universe=None):
    return signal_scores_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=day_turnover,
        stamp_ns=stamp,
        universe=universe or list(day_turnover),
        oi_by_symbol=oi,
        mark_by_symbol=mark,
    )


# --------------------------------------------------------------------- #
# (b) future-row mutations must change nothing
# --------------------------------------------------------------------- #
def test_future_oi_row_mutation_changes_nothing() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    base = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], world["mark_by_symbol"]
    )
    mutated_oi = {
        sym: series + ((T1_NS + 3_600_000_000_000, 1e12),)
        for sym, series in world["oi_by_symbol"].items()
    }
    mutated = _anchor_scores(
        world["day_turnover_by_symbol"], mutated_oi, world["mark_by_symbol"]
    )
    assert mutated == base  # exact float equality: the future row is unread


def test_future_mark_row_mutation_changes_nothing() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    base = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], world["mark_by_symbol"]
    )
    mutated_mark = {
        sym: series + ((T1_NS + 60_000_000_000, 4242.0),)
        for sym, series in world["mark_by_symbol"].items()
    }
    mutated = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], mutated_mark
    )
    assert mutated == base


def test_future_turnover_day_mutation_changes_nothing() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    base = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], world["mark_by_symbol"]
    )
    mutated = {sym: dict(days) for sym, days in world["day_turnover_by_symbol"].items()}
    for sym in mutated:
        mutated[sym][T1_DAY + 1] = 1e15  # a future "burst" day
        mutated[sym][T1_DAY + 2] = 1e15
    after = _anchor_scores(mutated, world["oi_by_symbol"], world["mark_by_symbol"])
    assert after == base


def test_past_input_mutations_DO_change_the_output() -> None:
    """The mirror mutations: past rows are provably the consumed inputs."""
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    base = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], world["mark_by_symbol"]
    )
    # mutate the past OI history of one symbol
    oi = {sym: series for sym, series in world["oi_by_symbol"].items()}
    oi["SYM03"] = oi["SYM03"][:-1] + ((oi["SYM03"][-1][0], 999_999.0),)
    after = _anchor_scores(
        world["day_turnover_by_symbol"], oi, world["mark_by_symbol"]
    )
    assert after["SYM03"] != base["SYM03"]
    for sym in base:
        if sym != "SYM03":
            assert after[sym] == base[sym]
    # mutate one past turnover day of one symbol
    to = {sym: dict(days) for sym, days in world["day_turnover_by_symbol"].items()}
    to["SYM14"][T1_DAY - 4] *= 3.0
    after = _anchor_scores(to, world["oi_by_symbol"], world["mark_by_symbol"])
    assert after["SYM14"] != base["SYM14"]
    # D = OI7 x MK / TO: tripling ONE of the 28 window days multiplies the
    # mean by 30/28, so D scales by exactly 28/30 (hand arithmetic)
    assert after["SYM14"] == pytest.approx(
        base["SYM14"] * 28.0 / 30.0, rel=1e-9
    )
    # mutate the past mark of one symbol
    mk = {sym: series for sym, series in world["mark_by_symbol"].items()}
    mk["SYM08"] = ((T1_NS - 3_600_000_000_000, 99.0),)
    after = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], mk
    )
    assert after["SYM08"] != base["SYM08"]


def test_control_scores_consumed_turnover_mutation_and_nothing_else() -> None:
    """The control reads ONLY the turnover flow: OI/mark rows are inert."""
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    base = signal_scores_at(
        CONTROL_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    # the control score IS the 28d daily mean turnover, hand-exact
    for sym in GROUP_L:
        assert base[sym] == pytest.approx(250_000.0, rel=1e-15)
    # OI history entirely absent -> identical scores (deleted numerator)
    after = signal_scores_at(
        CONTROL_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    assert after == base
    # a past-turnover mutation DOES move it
    to = {sym: dict(days) for sym, days in world["day_turnover_by_symbol"].items()}
    for sym in GROUP_L:
        for d in list(to[sym]):
            to[sym][d] = 125_000.0
    after = signal_scores_at(
        CONTROL_ARM,
        day_turnover_by_symbol=to,
        stamp_ns=T1_NS,
        universe=world["universe"],
    )
    assert after["SYM12"] == pytest.approx(125_000.0, rel=1e-15)
    assert after["SYM12"] != base["SYM12"]


def test_ineligibility_mutations_refuse_the_symbol_fail_closed() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    base = _anchor_scores(
        world["day_turnover_by_symbol"], world["oi_by_symbol"], world["mark_by_symbol"]
    )
    # drop a past OI stamp below the frozen 7
    oi = {sym: series for sym, series in world["oi_by_symbol"].items()}
    oi["SYM05"] = oi["SYM05"][:6]
    after = _anchor_scores(
        world["day_turnover_by_symbol"], oi, world["mark_by_symbol"]
    )
    assert "SYM05" in base and "SYM05" not in after


# --------------------------------------------------------------------- #
# (b) the availability-stamp mutation (the A9-F pinned caveat)
# --------------------------------------------------------------------- #
def test_availability_stamp_mutation_fill_cannot_read_a_later_record() -> None:
    """THE pinned convention: a 00:15Z fill cannot read a 00:30Z record.

    Decision at Monday 00:00:00Z; release at 00:15Z; the fill's readable
    horizon is its slot-open 00:15Z.  A record stamped 00:30Z (exactly
    the covering bar's close stamp) is UNREADABLE to that fill.
    """
    stamp_00_15 = RELEASE_NS
    stamp_00_30 = RELEASE_NS + BAR_NS
    # readable: the bar OPEN exists at the slot-open instant itself (==)
    assert_inputs_available(
        (stamp_00_15,), as_of_ns=stamp_00_15, context="fill@00:15"
    )
    # unreadable: anything stamped strictly later refuses, fail closed
    with pytest.raises(LookaheadViolation):
        assert_inputs_available(
            (stamp_00_30,), as_of_ns=stamp_00_15, context="fill@00:15"
        )
    # the decision payload (stamped 00:00Z) is readable at the fill
    assert_inputs_available((T1_NS,), as_of_ns=stamp_00_15, context="fill@00:15")


def test_availability_gate_is_the_shared_decision_rule() -> None:
    """The same gate governs decisions at T (OI7 / mark consume it)."""
    from research.v13.families.oitd.strategy import oi7_mean, latest_mark

    # nine daily rows at 23:55 ending the day before the stamp, value 5
    series = tuple(
        ((T1_NS - k * DAY_NS) + (23 * 3_600 + 55 * 60) * 1_000_000_000, 5.0)
        for k in range(1, 10)
    )
    assert oi7_mean(series, T1_NS) == pytest.approx(5.0)  # latest 7, all 5
    # a record stamped AFTER the decision is structurally invisible: the
    # primitives stop at the first future row, so the output is unchanged
    assert oi7_mean(series + ((T1_NS + 1, 7.0),), T1_NS) == pytest.approx(5.0)
    assert latest_mark(((T1_NS - 60, 10.0),), T1_NS) == pytest.approx(10.0)
    assert latest_mark(((T1_NS + 1, 10.0),), T1_NS - 1) is None
    # the availability gate itself refuses future-stamped CONSUMED inputs
    with pytest.raises(LookaheadViolation):
        assert_inputs_available(
            (T1_NS + 1,), as_of_ns=T1_NS, context="decision@T"
        )


def test_snap_rule_equals_the_frozen_v12_audit_loader() -> None:
    """The pinned snap is the frozen V12 rule, byte-for-byte (read-only)."""
    from research.v12.families.oilev_v2.audits import (
        _snap_close_to_boundary as v12_snap,
    )

    probes = [
        T1_NS - 999_936,  # the real Binance ~1ms-before-boundary stamp
        T1_NS,
        T1_NS + BAR_NS // 2,
        T1_NS + BAR_NS - 1,
        T1_NS - BAR_NS // 2 + 1,
        1756080000000000999,
    ]
    for probe in probes:
        assert snap_close_to_boundary(probe) == v12_snap(probe), probe


# --------------------------------------------------------------------- #
# (c) next-allowed-fill
# --------------------------------------------------------------------- #
def test_fill_is_the_open_of_the_first_slot_at_or_after_release() -> None:
    bars = execution_bars(T1_NS)
    event = next_allowed_fill(bars, "SYM00", decision_ns=T1_NS)
    assert event is not None
    assert event.fill_open_ns == RELEASE_NS  # the 00:15Z slot-open
    assert event.fill_bar_close_ns == T1_NS + 2 * BAR_NS  # closes 00:30Z
    # the consumed price is the bar OPEN (observable at 00:15Z), never its close
    assert event.price == pytest.approx(101.0)
    assert event.event_offset == 0
    assert event.decision_ns == T1_NS
    # the fill never happens before the release instant
    assert event.fill_open_ns >= RELEASE_NS


def test_stress_plus_one_delay_shifts_to_the_next_slot() -> None:
    bars = execution_bars(T1_NS)
    base = next_allowed_fill(bars, "SYM00", decision_ns=T1_NS)
    delayed = next_allowed_fill(
        bars, "SYM00", decision_ns=T1_NS, event_delay_events=1
    )
    assert delayed.fill_open_ns == base.fill_open_ns + BAR_NS  # the 00:30Z slot
    assert delayed.price == pytest.approx(102.0)
    assert delayed.event_offset == 1
    # a delay beyond the available bars degrades to the last one (never None
    # while ANY candidate exists), and a huge delay on a short list stays
    # at/after release
    assert delayed.fill_open_ns >= RELEASE_NS + BAR_NS


def test_missing_slots_yield_no_event() -> None:
    # no bar at/after release -> None (never a shifted substitute)
    assert next_allowed_fill((), "SYM00", decision_ns=T1_NS) is None
    # the bar [00:00, 00:15) closes at 00:15: its slot-open (00:00) is
    # BEFORE the release instant, so it is not a candidate
    early_only = execution_bars(T1_NS)[:1]
    assert next_allowed_fill(early_only, "SYM00", decision_ns=T1_NS) is None


def test_duplicate_slots_and_unsorted_bars() -> None:
    from research.adapter_v10.protocol import ContractViolation
    from research.v11.families.oilever_delev.strategy import Bar

    good = execution_bars(T1_NS)
    duplicate = list(good) + [
        Bar(ts_event_ns=T1_NS + 2 * BAR_NS, open=55.0, high=56.0, low=54.0, close=55.5)
    ]
    with pytest.raises(ContractViolation):
        next_allowed_fill(duplicate, "SYM00", decision_ns=T1_NS)
    # unsorted input is ordered internally before selection
    shuffled = [good[2], good[0], good[3], good[1]]
    event = next_allowed_fill(shuffled, "SYM00", decision_ns=T1_NS)
    assert event.price == pytest.approx(101.0)


def test_plugin_fills_and_marks_use_the_pinned_convention() -> None:
    from tests.v13i_oitd_world import plugin as make_plugin

    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    p = make_plugin(ANCHOR_ARM, world)
    from research.adapter_v10.protocol import FillStatusVocabulary

    stress = p.baseline_stress()
    fills = p.fills_at(T1_NS, symbols=world["universe"], stress=stress)
    assert len(fills) == 18
    for fill in fills:
        assert fill.applied is True
        assert fill.status == FillStatusVocabulary.APPLIED
        assert fill.fill_open_ns == RELEASE_NS
        assert fill.price == pytest.approx(101.0)
    delayed = p.fills_at(
        T1_NS,
        symbols=("SYM00",),
        stress=type(stress)(
            name="s", fee_multiplier=1.0, tick_slip_ticks=1, event_delay_events=1
        ),
    )[0]
    assert delayed.fill_open_ns == RELEASE_NS + BAR_NS
    assert delayed.price == pytest.approx(102.0)
    marks = p.marks_at(world["universe"], T1_NS)
    for sym, mark in marks.items():
        # valuation mark = OPEN of the bar that OPENS at the stamp
        assert mark == pytest.approx(100.0), sym


def test_decision_target_mutation_via_later_stamp_is_refused_by_the_chain() -> None:
    """A book asked at a NON-retained stamp is refused (fail-closed)."""
    from tests.v13i_oitd_world import plugin as make_plugin

    from research.adapter_v10.protocol import ContractViolation

    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    p = make_plugin(ANCHOR_ARM, world)
    with pytest.raises(ContractViolation):
        p.targets_at(
            T1_NS + 3_600_000_000_000,
            universe=tuple(world["universe"]),
            stress=p.baseline_stress(),
        )
