"""Hand-computed goldens for FX rollover carry (FX4 gate).

Schedule values are SYNTHETIC_TEST_ONLY (provenance is a required field).
Reference week (all dates 2026, America/New_York; January = EST = UTC-5,
so the 17:00 NY rollover is 22:00Z):

  Mon 05  Tue 06  Wed 07  Thu 08  Fri 09 | Sat 10  Sun 11 | Mon 12 ...

Value-date rule implemented by rollover.py (documented in the module):
nights charged at the rollover on day D = calendar nights between spot(D)
(T+2 business days, weekend+holidays skipped) and the next business day,
weekend nights counted, nights ending on an explicit holiday uncharged.
A regular week charges 1+1+3+1+1 = 7 nights; Wednesday is the triple-roll
(spot jumps Fri -> Mon: nights Fri->Sat, Sat->Sun, Sun->Mon).

Pip value of 10,000 EURUSD at pip 0.0001 = 0.0001 * 10,000 = 1.00 USD/pip,
so a +0.5 swap-point long pays +0.50 USD/night and a -0.7 short pays
-0.70 USD/night (long/short asymmetry is in the schedule itself).
"""

from __future__ import annotations

from datetime import date

import pytest

from research.assets.common.carrying_cost import CarryingCostModel
from research.assets.common.carrying_cost import FxRolloverCarry as FxRolloverCarryCommon

from research.assets.forex.conversion import DEFAULT_PIP_SIZE
from research.assets.forex.rollover import (
    RATE_PER_NIGHT,
    ROLLOVER_KIND,
    ROLLOVER_NOTE,
    RolloverLeg,
    RolloverSchedule,
    RolloverScheduleUnavailable,
    SWAP_POINTS,
    SYNTHETIC_TEST_ONLY,
    FxRolloverCarry,
    nights_charged,
)

QTY = 10_000
PIP = DEFAULT_PIP_SIZE  # 0.0001

# intervals as UTC ISO strings (EST = UTC-5)
WED_15_ET = "2026-01-07T20:00:00+00:00"
WED_18_ET = "2026-01-07T23:00:00+00:00"
THU_16_ET = "2026-01-08T21:00:00+00:00"
FRI_16_ET = "2026-01-09T21:00:00+00:00"
THU_18_ET = "2026-01-08T23:00:00+00:00"
WED_17_ET_UTC = "2026-01-07T22:00:00+00:00"


def make_schedule():
    return RolloverSchedule(
        entries={
            ("EURUSD", "LONG"): RolloverLeg(value=0.5, units=SWAP_POINTS, quote_currency="USD"),
            ("EURUSD", "SHORT"): RolloverLeg(value=-0.7, units=SWAP_POINTS, quote_currency="USD"),
            ("USDJPY", "LONG"): RolloverLeg(value=0.3, units=SWAP_POINTS, quote_currency="JPY"),
        },
        provenance=SYNTHETIC_TEST_ONLY,
    )


def make_carry():
    return FxRolloverCarry(schedule=make_schedule())


# --- golden: one night long / short (asymmetric) -------------------------------- #
def test_one_night_long():
    carry = make_carry()
    # window Thu 16:00 ET -> Fri 16:00 ET contains exactly the Thu 17:00 ET roll;
    # nights(Thu) = 1 (spot Mon -> Tue)
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=THU_16_ET,
        interval_end_utc=FRI_16_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    assert len(lines) == 1
    line = lines[0]
    # amount = +0.5 swap points * pip 0.0001 * 10,000 = +0.5 * 1.00 USD = +0.50
    assert line.amount == pytest.approx(0.50, abs=1e-12)
    assert line.currency == "USD"
    assert line.instrument_symbol == "EURUSD"
    # 17:00 EST == 22:00 UTC in January (EST, UTC-5)
    assert line.timestamp_utc == "2026-01-08T22:00:00+00:00"


def test_one_night_short_asymmetry():
    carry = make_carry()
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=-QTY,
        interval_start_utc=THU_16_ET,
        interval_end_utc=FRI_16_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    assert len(lines) == 1
    # amount = -0.7 * 0.0001 * 10,000 = -0.70 (short pays 0.70, not 0.50 mirrored)
    assert lines[0].amount == pytest.approx(-0.70, abs=1e-12)
    assert lines[0].is_paid is True


def test_long_short_asymmetry_not_mirrored():
    carry = make_carry()
    long_lines = carry.cashflows(
        instrument_symbol="EURUSD", position_qty=QTY,
        interval_start_utc=THU_16_ET, interval_end_utc=FRI_16_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    short_lines = carry.cashflows(
        instrument_symbol="EURUSD", position_qty=-QTY,
        interval_start_utc=THU_16_ET, interval_end_utc=FRI_16_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    assert long_lines[0].amount == pytest.approx(0.50)
    assert short_lines[0].amount == pytest.approx(-0.70)
    assert long_lines[0].amount != pytest.approx(-short_lines[0].amount)


# --- golden: triple-roll across Wednesday 17:00 NY ------------------------------- #
def test_triple_roll_wednesday():
    carry = make_carry()
    # open Wed 15:00 ET, still open Wed 18:00 ET: crosses the Wed 17:00 ET roll.
    # spot(Wed) = Fri 09 -> next business day Mon 12: 3 calendar nights
    # (Fri->Sat, Sat->Sun, Sun->Mon) -> 3 * 0.5 * 1.00 = +1.50 USD in one line.
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=WED_15_ET,
        interval_end_utc=WED_18_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    assert len(lines) == 1
    assert lines[0].timestamp_utc == WED_17_ET_UTC
    assert lines[0].amount == pytest.approx(1.50, abs=1e-12)


def test_two_rollover_events_in_window():
    carry = make_carry()
    # Wed 15:00 ET -> Thu 18:00 ET crosses Wed (3 nights) and Thu (1 night) rolls:
    # amounts 3*0.50 = 1.50 and 1*0.50 = 0.50, total 2.00.
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=WED_15_ET,
        interval_end_utc=THU_18_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    assert [round(line.amount, 12) for line in lines] == [1.50, 0.50]
    assert lines[0].timestamp_utc < lines[1].timestamp_utc


def test_event_boundary_is_strictly_after_start():
    carry = make_carry()
    # a position opened exactly AT the Wed 17:00 roll does not pay it; the next
    # event in the window (Thu 17:00 ET, 1 night) is included.
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=WED_17_ET_UTC,
        interval_end_utc=THU_18_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    assert len(lines) == 1
    assert lines[0].timestamp_utc == "2026-01-08T22:00:00+00:00"
    assert lines[0].amount == pytest.approx(0.50, abs=1e-12)


# --- golden: explicit holiday set shifts the weekday count ----------------------- #
def test_holiday_friday_reduces_triple_roll_to_one():
    carry = make_carry()
    # Friday 2026-01-09 is a settlement holiday: spot(Wed) slides Fri -> Mon,
    # so the Wednesday roll spans Mon -> Tue = 1 night -> +0.50 (was +1.50).
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=WED_15_ET,
        interval_end_utc=WED_18_ET,
        context={"holidays": {date(2026, 1, 9)}, "pip_size": PIP},
    )
    assert len(lines) == 1
    assert lines[0].amount == pytest.approx(0.50, abs=1e-12)


def test_holiday_monday_removes_one_of_four_weekend_span_nights():
    carry = make_carry()
    # Monday 2026-01-12 is a holiday: spot(Wed)=Fri 09, next business day after
    # Fri is Tue 13 -> 4 calendar nights minus the night ending on the holiday
    # (Sun->Mon) = 3 charged nights -> still +1.50.
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=WED_15_ET,
        interval_end_utc=WED_18_ET,
        context={"holidays": {date(2026, 1, 12)}, "pip_size": PIP},
    )
    assert len(lines) == 1
    assert lines[0].amount == pytest.approx(1.50, abs=1e-12)


def test_nights_charged_conserves_seven_per_week():
    holidays = frozenset[date]()
    # Mon 05 .. Fri 09 January 2026
    week = [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8), date(2026, 1, 9)]
    charged = [nights_charged(day, holidays) for day in week]
    # Mon Tue Wed Thu Fri -> 1 + 1 + 3 + 1 + 1 = 7 calendar nights per week
    assert charged == [1, 1, 3, 1, 1]
    assert sum(charged) == 7


# --- cashflow contract: kind is the common ROLLOVER kind, never FUNDING ---------- #
def test_cashflow_kind_is_rollover_never_funding():
    carry = make_carry()
    lines = carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=QTY,
        interval_start_utc=THU_16_ET,
        interval_end_utc=FRI_16_ET,
        context={"holidays": set(), "pip_size": PIP},
    )
    # common CASHFLOW_KINDS = ("FUNDING", "BORROW", "DIVIDEND", "ROLLOVER");
    # the literal "fx_rollover" is not a legal kind there, so the lane encodes
    # kind="ROLLOVER" (NEVER "FUNDING") with note="fx_rollover".
    assert lines[0].kind == ROLLOVER_KIND == "ROLLOVER"
    assert lines[0].kind != "FUNDING"
    assert lines[0].note == ROLLOVER_NOTE == "fx_rollover"


def test_implements_common_carry_interface():
    carry = make_carry()
    assert isinstance(carry, FxRolloverCarryCommon)
    assert isinstance(carry, CarryingCostModel)
    assert carry.model_id == "FX_ROLLOVER_V1"


# --- rate-per-night units ---------------------------------------------------------- #
def test_rate_per_night_units_without_pip_size():
    schedule = RolloverSchedule(
        entries={
            ("AUDUSD", "LONG"): RolloverLeg(value=0.00002, units=RATE_PER_NIGHT, quote_currency="AUD"),
        },
        provenance=SYNTHETIC_TEST_ONLY,
    )
    carry = FxRolloverCarry(schedule=schedule)
    lines = carry.cashflows(
        instrument_symbol="AUDUSD",
        position_qty=10_000,
        interval_start_utc=THU_16_ET,
        interval_end_utc=FRI_16_ET,
        context={"holidays": set()},  # no pip_size needed for RATE_PER_NIGHT
    )
    # amount = 0.00002 * 10,000 = 0.20 AUD for the single Thu night
    assert len(lines) == 1
    assert lines[0].amount == pytest.approx(0.20, abs=1e-12)
    assert lines[0].currency == "AUD"


# --- fail-closed paths -------------------------------------------------------------- #
def test_missing_schedule_pair_raises():
    carry = make_carry()  # schedule has no AUDUSD entries at all
    with pytest.raises(RolloverScheduleUnavailable) as excinfo:
        carry.cashflows(
            instrument_symbol="AUDUSD",
            position_qty=QTY,
            interval_start_utc=THU_16_ET,
            interval_end_utc=FRI_16_ET,
            context={"holidays": set(), "pip_size": PIP},
        )
    assert excinfo.value.reason == "MISSING_SCHEDULE_ENTRY"


def test_missing_schedule_side_raises():
    carry = make_carry()  # USDJPY has only a LONG leg
    with pytest.raises(RolloverScheduleUnavailable) as excinfo:
        carry.cashflows(
            instrument_symbol="USDJPY",
            position_qty=-QTY,
            interval_start_utc=THU_16_ET,
            interval_end_utc=FRI_16_ET,
            context={"holidays": set(), "pip_size": 0.01},
        )
    assert excinfo.value.reason == "MISSING_SCHEDULE_ENTRY"


def test_missing_holidays_context_fails_closed():
    carry = make_carry()
    with pytest.raises(RolloverScheduleUnavailable) as excinfo:
        carry.cashflows(
            instrument_symbol="EURUSD",
            position_qty=QTY,
            interval_start_utc=THU_16_ET,
            interval_end_utc=FRI_16_ET,
            context={"pip_size": PIP},  # holidays deliberately absent
        )
    assert excinfo.value.reason == "MISSING_CONTEXT"


def test_missing_pip_size_fails_closed_for_swap_points():
    carry = make_carry()
    with pytest.raises(RolloverScheduleUnavailable) as excinfo:
        carry.cashflows(
            instrument_symbol="EURUSD",
            position_qty=QTY,
            interval_start_utc=THU_16_ET,
            interval_end_utc=FRI_16_ET,
            context={"holidays": set()},  # pip_size deliberately absent
        )
    assert excinfo.value.reason == "MISSING_CONTEXT"


def test_zero_quantity_has_no_carry():
    carry = make_carry()
    assert carry.cashflows(
        instrument_symbol="EURUSD",
        position_qty=0,
        interval_start_utc=THU_16_ET,
        interval_end_utc=FRI_16_ET,
        context={"holidays": set(), "pip_size": PIP},
    ) == ()


def test_invalid_interval_raises():
    carry = make_carry()
    with pytest.raises(RolloverScheduleUnavailable) as excinfo:
        carry.cashflows(
            instrument_symbol="EURUSD",
            position_qty=QTY,
            interval_start_utc=FRI_16_ET,
            interval_end_utc=THU_16_ET,  # end before start
            context={"holidays": set(), "pip_size": PIP},
        )
    assert excinfo.value.reason == "INVALID_INTERVAL"


def test_schedule_requires_provenance():
    with pytest.raises(ValueError):
        RolloverSchedule(entries={}, provenance="")
