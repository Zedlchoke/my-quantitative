"""Signal-event reducer golden + no-op law + cost-tier exactness."""

import pytest

from psv1_spy.events import labels_to_targets, reduce_events
from psv1_spy.phase_rule import UNKNOWN, UPTREND
from psv1_spy.costs import (
    PER_FILL_BPS,
    ROUND_TRIP_BPS,
    TIERS,
    fill_cost_bps,
    round_trip_cost_bps,
    tier_table,
)


def test_event_golden_entry_exit_holds():
    targets = [0, 0, 1, 1, 1, 0, 0, 1, 1, 0]
    r = reduce_events(targets)
    assert r["fills"] == [("ENTER", 2), ("EXIT", 5), ("ENTER", 7), ("EXIT", 9)]
    assert r["entry_events"] == 2 and r["exit_events"] == 2
    assert r["holds_sessions"] == [3, 2]
    assert r["long_sessions"] == 5
    assert r["no_op_fills"] == 0
    assert not r["still_open_at_stream_end"]


def test_no_op_law_same_direction_zero_fills():
    r = reduce_events([1, 1, 1, 1, 1])
    assert r["fills"] == [("ENTER", 0)]
    assert r["exit_events"] == 0
    assert r["no_op_opportunities"] == 4
    r0 = reduce_events([0, 0, 0])
    assert r0["fills"] == [] and r0["entry_events"] == 0


def test_enter_at_stream_start_and_open_end_flag():
    r = reduce_events([1, 1, 1])
    assert r["fills"] == [("ENTER", 0)]
    assert r["still_open_at_stream_end"] is True


def test_unknown_label_state_hysteresis_produces_no_fills():
    # UNKNOWN keeps the previous position (state hysteresis, not a holding-
    # duration law): a label wiggle through UNKNOWN fires ZERO fills.
    labels = [UPTREND, UNKNOWN, UNKNOWN, UPTREND, UNKNOWN]
    targets = labels_to_targets(labels, {UPTREND: 1}, unknown_keeps_previous=True)
    assert targets == [1, 1, 1, 1, 1]
    r = reduce_events(targets)
    assert r["entry_events"] == 1 and r["exit_events"] == 0


def test_cost_constants_and_tiers_exact():
    assert PER_FILL_BPS == 10.0 and ROUND_TRIP_BPS == 20.0
    assert TIERS == (1.0, 1.5, 2.0)
    # 1.0x
    assert fill_cost_bps(1, 1.0) == 10.0
    assert fill_cost_bps(2, 1.0) == 20.0
    assert round_trip_cost_bps(1, 1.0) == 20.0
    # equivalence: 2 fills == 1 round trip (never summed)
    assert fill_cost_bps(2, 1.0) == round_trip_cost_bps(1, 1.0)
    # 1.5x applies to the FULL stack
    assert fill_cost_bps(2, 1.5) == 30.0
    assert round_trip_cost_bps(1, 1.5) == 30.0
    # 2.0x
    assert fill_cost_bps(2, 2.0) == 40.0
    assert round_trip_cost_bps(1, 2.0) == 40.0
    # reference points used in feasibility/ceiling.json
    assert tier_table(8, 4)["tier_1.0x"]["fills_view_bps"] == 80.0
    assert tier_table(8, 4)["tier_1.5x"]["round_trips_view_bps"] == 120.0
    assert tier_table(8, 4)["tier_2.0x"]["fills_view_bps"] == 160.0
    with pytest.raises(ValueError):
        fill_cost_bps(1, 1.25)
    with pytest.raises(ValueError):
        round_trip_cost_bps(1, 3.0)
