"""V13 I lane (i-family-2) -- PIT/no-lookahead mutation tests and the
next-allowed-fill contract for A13-V13-A5-LIQEPIS (plan section 9 evidence
items b and c).

Fusion availability semantics (binding): a decision at T never reads a row
whose availability stamp is > T; a completed 15m bar is available at its
close boundary.  The formation window at T is the trailing N completed
slots in ``(T - N*15m, T]``; EVERY slot must be present AND available --
one missing or unavailable slot refuses the symbol (fail closed).

Evidence (b):
* an IN-WINDOW mutation (volume of the engineered burst bar of the middle
  symbol) must CHANGE the decision book;
* a FUTURE-row mutation (the close of the 00:15Z / 00:30Z fill bars,
  strictly after the decision stamp) must NEVER change the decision book
  while it DOES change the fill prices (the mutated rows are read only by
  execution, never by the decision);
* an AVAILABILITY mutation (a formation row made available only after T)
  must REFUSE the symbol at T (fail closed) -- with 13 names that refuses
  the stamp outright; with 14 names the book changes because the symbol is
  dropped from the ranking.

Evidence (c): fills execute at the CLOSE of the first completed 15m bar
STRICTLY after the decision stamp (Monday 00:15:00Z); the +1-delay stress
fills at the 00:30:00Z close; the decision stamp's own bar is never a
fill; a genuinely missing slot advances to the next completed bar (a real
execution event, never a shifted substitute); a fill bar that is not yet
readable at its own close refuses.

All data synthetic; no scored metric exists.
"""

from __future__ import annotations

import pytest

from research.v13.families.liqepis.plugin import LiqepisPlugin
from research.v13.families.liqepis.strategy import (
    ANCHOR_ARM,
    BAR_INTERVAL_NS,
    CONTROL_ARM,
    EligibilityShortfall,
    episodicity_at,
    compute_targets_at,
    next_allowed_close_fill,
    series_from_rows,
    signal_scores_at,
)

from tests.test_v13i_liqepis_goldens import build_world, load_fixture


def test_mutation_inside_the_formation_window_changes_the_book() -> None:
    """Mutating an in-window row (SYM06's burst) must change the decision."""
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    base = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    burst = int(fixture["burst_boundary_ns"])
    # blow SYM06 (the middle name) into the extreme bursty tail
    mutated, _stamp, _universe = build_world(
        fixture, volume_override={"SYM06": {burst: 500.0}}
    )
    after = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=mutated, stamp_ns=stamp, universe=universe
    )
    assert [s for s, _ in after["shorts"]] != [s for s, _ in base["shorts"]]
    assert "SYM06" in [s for s, _ in after["shorts"]]
    assert "SYM07" not in [s for s, _ in after["shorts"]]  # pushed to the middle


def test_future_row_mutation_never_changes_the_decision_but_changes_fills() -> None:
    """No-lookahead: strictly-after-T rows cannot enter the decision at T."""
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    base = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    base_scores = signal_scores_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    fill_bar = int(fixture["mutation_slots"]["fill_bar_boundary_ns"])
    stress_fill_bar = int(fixture["mutation_slots"]["stress_fill_bar_boundary_ns"])
    mutated, _stamp, _universe = build_world(
        fixture,
        close_override={"SYM06": {fill_bar: 999.0, stress_fill_bar: 777.0}},
    )
    after = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=mutated, stamp_ns=stamp, universe=universe
    )
    after_scores = signal_scores_at(
        ANCHOR_ARM, bars_by_symbol=mutated, stamp_ns=stamp, universe=universe
    )
    assert after_scores == base_scores  # decisions are bit-identical
    assert after["weights"] == base["weights"]
    # ...while the same mutation moves the FILL prices (execution reads it)
    base_fill = next_allowed_close_fill(world["SYM06"], "SYM06", decision_ns=stamp)
    mutated_fill = next_allowed_close_fill(
        mutated["SYM06"], "SYM06", decision_ns=stamp
    )
    assert base_fill.fill_ns == fill_bar
    assert mutated_fill.price == 999.0 and base_fill.price != mutated_fill.price
    delayed = next_allowed_close_fill(
        mutated["SYM06"], "SYM06", decision_ns=stamp, event_delay_events=1
    )
    assert delayed.fill_ns == stress_fill_bar and delayed.price == 777.0


def test_decision_is_invariant_to_whether_future_rows_exist_at_all() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    full = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    # truncate every series at the decision stamp: no post-T row exists
    truncated = {}
    for sym, series in world.items():
        rows = []
        for idx in range(series.close.shape[0]):
            boundary = int(series.origin_ns) + idx * BAR_INTERVAL_NS
            if boundary > stamp:
                break
            if series.close[idx] != series.close[idx]:  # NaN gap slot
                continue
            rows.append(
                (boundary, int(series.available_ns[idx]), float(series.close[idx]),
                 float(series.volume[idx]))
            )
        truncated[sym] = series_from_rows(rows)
    cut = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=truncated, stamp_ns=stamp, universe=universe
    )
    assert cut["weights"] == full["weights"]


def test_availability_mutation_refuses_the_symbol_fail_closed() -> None:
    """A formation row available only AFTER T is unreadable at T."""
    fixture = load_fixture()
    burst = int(fixture["burst_boundary_ns"])
    late = int(fixture["stamp_ns"]) + 1  # available one nanosecond after T
    world, stamp, universe = build_world(
        fixture, late_available={"SYM06": {burst: late}}
    )
    value, reason = episodicity_at(
        world["SYM06"], stamp, formation_bars=2688
    )
    assert value is None and reason == "UNAVAILABLE_ROW"
    scores = signal_scores_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    assert "SYM06" not in scores
    # 13-name universe minus one refused name = 12 < min_eligible 13: refuse
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
        )
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            CONTROL_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=universe
        )


def test_availability_mutation_on_a_deeper_universe_changes_the_book() -> None:
    """With 14 names one refusal still yields a book -- but a different one."""
    fixture = load_fixture()
    burst = int(fixture["burst_boundary_ns"])
    late = int(fixture["stamp_ns"]) + 1
    deep_fixture = dict(fixture)
    deep_fixture["symbols"] = fixture["symbols"] + ["SYM13"]
    deep_fixture["burst_multiplier_by_symbol"] = dict(
        fixture["burst_multiplier_by_symbol"], SYM13=14
    )
    world, stamp, universe = build_world(
        deep_fixture, late_available={"SYM08": {burst: late}}
    )
    base_world, _stamp, _universe = build_world(deep_fixture)
    base = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=base_world, stamp_ns=stamp, universe=list(universe)
    )
    after = compute_targets_at(
        ANCHOR_ARM, bars_by_symbol=world, stamp_ns=stamp, universe=list(universe)
    )
    # base 14-name book: shorts are the six burstiest SYM08..SYM13
    assert [s for s, _ in base["shorts"]] == [
        "SYM08", "SYM09", "SYM10", "SYM11", "SYM12", "SYM13",
    ]
    assert after["diagnostics"]["refused"].get("SYM08") == "UNAVAILABLE_ROW"
    assert "SYM08" not in [s for s, _ in after["shorts"]]
    assert "SYM07" in [s for s, _ in after["shorts"]]  # the leg shifted in


# --------------------------------------------------------------------------- #
# Evidence (c): next-allowed-fill (close of the first completed 15m bar
# strictly after the decision stamp)
# --------------------------------------------------------------------------- #
def test_fill_at_the_00_15z_close_and_stress_delay_at_00_30z() -> None:
    fixture = load_fixture()
    world, stamp, _universe = build_world(fixture)
    series = world["SYM00"]
    base = next_allowed_close_fill(series, "SYM00", decision_ns=stamp)
    assert base is not None
    assert base.fill_ns == stamp + BAR_INTERVAL_NS  # Monday 00:15:00Z
    assert base.price == 1.0  # the fill bar's CLOSE
    assert base.event_offset == 0
    delayed = next_allowed_close_fill(
        series, "SYM00", decision_ns=stamp, event_delay_events=1
    )
    assert delayed is not None
    assert delayed.fill_ns == stamp + 2 * BAR_INTERVAL_NS  # Monday 00:30:00Z
    assert delayed.event_offset == 1
    # the decision stamp's own (completed) bar is NEVER a fill candidate:
    # no event carries fill_ns == stamp
    for event in (base, delayed):
        assert event.fill_ns > stamp


def test_fill_walks_a_genuinely_missing_slot_and_refuses_when_none() -> None:
    fixture = load_fixture()
    world, stamp, _universe = build_world(fixture)
    fill_bar = int(fixture["mutation_slots"]["fill_bar_boundary_ns"])
    holed, _stamp, _universe = build_world(
        fixture, drop_boundaries={"SYM00": {fill_bar}}
    )
    event = next_allowed_close_fill(holed["SYM00"], "SYM00", decision_ns=stamp)
    # the 00:15Z slot is missing, so the first completed bar after T IS the
    # 00:30Z bar: a real execution event, not an invented substitute
    assert event.fill_ns == stamp + 2 * BAR_INTERVAL_NS
    assert event.event_offset == 0
    # a series that ends at the decision stamp has NO event at all
    short = series_from_rows(
        [
            (int(world["SYM00"].origin_ns) + k * BAR_INTERVAL_NS,
             int(world["SYM00"].origin_ns) + k * BAR_INTERVAL_NS, 1.0, 1.0)
            for k in range(5)
            if int(world["SYM00"].origin_ns) + k * BAR_INTERVAL_NS <= stamp
        ]
    )
    assert next_allowed_close_fill(short, "SYM00", decision_ns=stamp) is None
    with pytest.raises(Exception):
        next_allowed_close_fill(world["SYM00"], "SYM00", decision_ns=stamp,
                                event_delay_events=-1)


def test_fill_bar_not_readable_at_its_own_close_refuses() -> None:
    fixture = load_fixture()
    burst = int(fixture["burst_boundary_ns"])
    fill_bar = int(fixture["mutation_slots"]["fill_bar_boundary_ns"])
    late = fill_bar + 1
    world, stamp, _universe = build_world(
        fixture, late_available={"SYM00": {burst: late, fill_bar: late}}
    )
    event = next_allowed_close_fill(world["SYM00"], "SYM00", decision_ns=stamp)
    assert event is None  # cannot transact on a row that is not yet readable


def test_plugin_fills_carry_the_declared_close_fill_convention() -> None:
    fixture = load_fixture()
    world, stamp, universe = build_world(fixture)
    bars = dict(world)
    bars["BTCUSDT"] = world["SYM00"]  # benchmark context bars (never traded)
    plugin = LiqepisPlugin(
        arm_id=ANCHOR_ARM,
        bars_by_symbol=bars,
        tick_sizes={sym: 0.01 for sym in universe},
    )
    fills = plugin.fills_at(
        stamp, symbols=["SYM00", "SYM01"], stress=plugin.baseline_stress()
    )
    assert all(f.applied for f in fills)
    assert all(f.fill_bar_close_ns == stamp + BAR_INTERVAL_NS for f in fills)
    assert plugin.declared_execution_lag() == (
        "fill at the close of the first completed 15m bar strictly after the "
        "decision stamp (Monday 00:15:00Z close); stress event delays walk "
        "strictly later completed bars (00:30:00Z close at +1 delay)"
    )
    from research.adapter_v10.protocol import StressSpec

    stressed = plugin.fills_at(
        stamp,
        symbols=["SYM00"],
        stress=StressSpec(name="probe", event_delay_events=1),
    )
    assert stressed[0].fill_bar_close_ns == stamp + 2 * BAR_INTERVAL_NS
    # valuation marks never look past the instant (the mark at T is the
    # decision stamp's own completed-bar close, not the future fill bar)
    marks = plugin.marks_at(["SYM00"], stamp)
    assert marks["SYM00"] == 1.0
