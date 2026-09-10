"""FX overnight rollover / swap carry (A5 lane, PLAN_forex.md section 7).

Contracts implemented here (fail closed, always):

* the ONLY input is an explicit swap/rollover schedule supplied by the
  caller (per pair, per side LONG/SHORT, in swap points or per-night rate).
  A missing schedule or a missing (pair, side) entry raises
  :class:`RolloverScheduleUnavailable` — there is no default carry and no
  implicit zero-cost assumption;
* long/short asymmetry is honored structurally: the schedule carries a
  separate signed value for each side and the position side selects it;
* triple-roll: a position open across the Wednesday 17:00 America/New_York
  rollover pays/receives 3 nightly amounts, because the spot value date
  jumps Friday -> Monday.  This is derived, not hard-coded: the nights
  charged at the rollover on day ``D`` are the calendar nights between
  ``spot(D)`` (two business days after ``D``) and the next business day
  after that, with weekend nights counted (they are exactly what makes the
  Wednesday roll a triple) and nights ending on an explicit holiday
  uncharged.  The rule conserves nights: 7 charged nights per regular week
  (1+1+3+1+1).  Rollover events exist Monday-Friday at 17:00 NY; Saturday
  and Sunday have no event.
* results are common :class:`~research.assets.common.carrying_cost.CashflowLine`
  entries.  The common contract restricts ``kind`` to
  ``("FUNDING", "BORROW", "DIVIDEND", "ROLLOVER")`` — the literal
  ``"fx_rollover"`` is not a legal ``kind`` there, so this lane encodes the
  rollover tag as ``kind="ROLLOVER"`` (NEVER ``"FUNDING"``) with
  ``note="fx_rollover"`` for lane-level identification.

All schedules used in tests are SYNTHETIC_TEST_ONLY; no broker schedule is
fabricated anywhere in this module.  Crypto funding assumptions must never
be substituted for FX rollover.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Mapping
from zoneinfo import ZoneInfo

from research.assets.common.carrying_cost import CashflowLine
from research.assets.common.carrying_cost import (
    FxRolloverCarry as FxRolloverCarryBase,
)

from research.assets.forex.conversion import parse_utc_timestamp

__all__ = [
    "ROLLOVER_KIND",
    "ROLLOVER_NOTE",
    "ROLLOVER_TIMEZONE",
    "ROLLOVER_HOUR",
    "SWAP_POINTS",
    "RATE_PER_NIGHT",
    "SYNTHETIC_TEST_ONLY",
    "RolloverLeg",
    "RolloverSchedule",
    "RolloverScheduleUnavailable",
    "FxRolloverCarry",
]

# kind is constrained by common CASHFLOW_KINDS; "fx_rollover" travels in note.
ROLLOVER_KIND = "ROLLOVER"
ROLLOVER_NOTE = "fx_rollover"

ROLLOVER_TIMEZONE = "America/New_York"
ROLLOVER_HOUR = 17  # NY 17:00 rollover boundary

SWAP_POINTS = "SWAP_POINTS"
RATE_PER_NIGHT = "RATE_PER_NIGHT"
_UNITS = (SWAP_POINTS, RATE_PER_NIGHT)

_SIDES = ("LONG", "SHORT")

# Explicit provenance marker required on every schedule built in this lane.
SYNTHETIC_TEST_ONLY = "SYNTHETIC_TEST_ONLY"


class RolloverScheduleUnavailable(Exception):
    """Rollover cannot be computed; carries a machine-readable reason.

    Reasons: ``MISSING_SCHEDULE``, ``MISSING_SCHEDULE_ENTRY``,
    ``MISSING_CONTEXT``, ``INVALID_INTERVAL``.
    """

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


@dataclass(frozen=True)
class RolloverLeg:
    """One side of one pair on the schedule.

    ``value`` is signed from the position holder's perspective (positive =
    received).  ``units`` is ``SWAP_POINTS`` (pips of the pair; needs an
    explicit ``pip_size`` at evaluation time) or ``RATE_PER_NIGHT`` (a pure
    fraction of base notional per night).
    """

    value: float
    units: str
    quote_currency: str

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError(f"RolloverLeg.value must be a number, got {self.value!r}")
        if not math.isfinite(float(self.value)):
            raise ValueError(f"RolloverLeg.value must be finite, got {self.value!r}")
        if self.units not in _UNITS:
            raise ValueError(f"RolloverLeg.units must be one of {_UNITS}, got {self.units!r}")
        if not isinstance(self.quote_currency, str) or len(self.quote_currency) != 3 or not self.quote_currency.isupper():
            raise ValueError(
                f"RolloverLeg.quote_currency must be a 3-letter uppercase code, got {self.quote_currency!r}"
            )


@dataclass(frozen=True)
class RolloverSchedule:
    """Explicit swap schedule: (pair, side) -> :class:`RolloverLeg`.

    ``provenance`` is required and non-empty; tests pass
    ``SYNTHETIC_TEST_ONLY`` so synthetic inputs can never masquerade as
    provider data.
    """

    entries: Mapping[tuple[str, str], RolloverLeg] = field(default_factory=dict)
    provenance: str = SYNTHETIC_TEST_ONLY

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, str) or not self.provenance.strip():
            raise ValueError("RolloverSchedule.provenance must be a non-empty string")
        if not isinstance(self.entries, Mapping):
            raise ValueError(
                f"RolloverSchedule.entries must be a mapping of (pair, side) -> RolloverLeg, "
                f"got {type(self.entries).__name__}"
            )
        for key, leg in self.entries.items():
            if not isinstance(key, tuple) or len(key) != 2:
                raise ValueError(f"schedule key must be (pair, side), got {key!r}")
            pair, side = key
            if not isinstance(pair, str) or len(pair) != 6 or not pair.isupper() or not pair.isalpha():
                raise ValueError(f"schedule pair must be a 6-letter symbol, got {pair!r}")
            if side not in _SIDES:
                raise ValueError(f"schedule side must be one of {_SIDES}, got {side!r}")
            if not isinstance(leg, RolloverLeg):
                raise ValueError(f"schedule value must be a RolloverLeg, got {type(leg).__name__}")

    def leg_for(self, pair: str, side: str) -> RolloverLeg | None:
        return self.entries.get((pair, side))


def _as_holiday_set(holidays: object) -> frozenset[date]:
    """Normalize an explicit holiday set (dates or ISO strings) to dates."""
    if isinstance(holidays, (str, bytes)) or not isinstance(holidays, (set, frozenset, list, tuple)):
        raise RolloverScheduleUnavailable(
            "MISSING_CONTEXT",
            "context['holidays'] must be an explicit set of dates or ISO date strings "
            "(fail closed: holiday adjustment is never implicit)",
        )
    normalized: set[date] = set()
    for item in holidays:
        if isinstance(item, datetime):
            normalized.add(item.date())
        elif isinstance(item, date):
            normalized.add(item)
        elif isinstance(item, str):
            try:
                normalized.add(date.fromisoformat(item))
            except ValueError as exc:
                raise RolloverScheduleUnavailable(
                    "MISSING_CONTEXT",
                    f"holiday {item!r} is not an ISO date string",
                ) from exc
        else:
            raise RolloverScheduleUnavailable(
                "MISSING_CONTEXT",
                f"holiday must be a date or ISO string, got {type(item).__name__}",
            )
    return frozenset(normalized)


def _spot_value_date(day: date, holidays: frozenset[date]) -> date:
    """T+2 spot value date: the second business day strictly after ``day``."""
    current = day
    found = 0
    while found < 2:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in holidays:
            found += 1
    return current


def _next_business_day_after(day: date, holidays: frozenset[date]) -> date:
    current = day
    while True:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in holidays:
            return current


def nights_charged(day: date, holidays: frozenset[date]) -> int:
    """Nights charged at the 17:00 NY rollover on ``day``.

    Calendar nights between ``spot(day)`` and the next business day after
    it, weekend nights included, minus nights ending on a holiday.  A normal
    week charges 1+1+3+1+1 = 7 nights (Wednesday = triple-roll).
    """
    value_date = _spot_value_date(day, holidays)
    next_value_date = _next_business_day_after(value_date, holidays)
    nights = (next_value_date - value_date).days
    if nights <= 0:
        raise ValueError(
            f"value-date ladder collapsed at {day}: {value_date} -> {next_value_date}"
        )
    holiday_nights = sum(
        1
        for offset in range(1, nights + 1)
        if (value_date + timedelta(days=offset)) in holidays
    )
    charged = nights - holiday_nights
    if charged < 0:
        raise ValueError(f"negative charged nights at {day} (inconsistent holiday set)")
    return charged


class FxRolloverCarry(FxRolloverCarryBase):
    """Implements the common :class:`FxRolloverCarry` stub for spot FX.

    The schedule is injected at construction; ``context`` must carry the
    explicit ``holidays`` set (possibly empty) and, when the schedule is in
    swap points, the explicit ``pip_size`` for the pair.
    """

    def __init__(
        self,
        *,
        schedule: RolloverSchedule,
        model_id: str = "FX_ROLLOVER_V1",
        rollover_tz: str = ROLLOVER_TIMEZONE,
        rollover_hour: int = ROLLOVER_HOUR,
    ) -> None:
        if not isinstance(schedule, RolloverSchedule):
            raise ValueError(
                f"schedule must be a RolloverSchedule, got {type(schedule).__name__}"
            )
        if not isinstance(model_id, str) or not model_id.strip():
            raise ValueError("model_id must be a non-empty string")
        try:
            self._tz = ZoneInfo(rollover_tz)
        except Exception as exc:  # noqa: BLE001 - unknown tz must fail closed
            raise ValueError(f"rollover_tz is not a known timezone: {rollover_tz!r}") from exc
        if not isinstance(rollover_hour, int) or not 0 <= rollover_hour <= 23:
            raise ValueError(f"rollover_hour must be an int in [0, 23], got {rollover_hour!r}")
        self._schedule = schedule
        self._model_id = model_id
        self._rollover_hour = rollover_hour

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def schedule(self) -> RolloverSchedule:
        return self._schedule

    # --- event enumeration ---------------------------------------------------- #
    def _events_between(
        self, start_utc: datetime, end_utc: datetime, holidays: frozenset[date]
    ) -> list[tuple[datetime, int]]:
        """Rollover events (UTC, nights charged) with start < event <= end."""
        zone = self._tz
        first_ny = start_utc.astimezone(zone).date() - timedelta(days=1)
        last_ny = end_utc.astimezone(zone).date() + timedelta(days=1)
        events: list[tuple[datetime, int]] = []
        day = first_ny
        while day <= last_ny:
            if day.weekday() < 5:  # Mon-Fri only: no Saturday/Sunday event
                event_ny = datetime(day.year, day.month, day.day, self._rollover_hour, tzinfo=zone)
                event_utc = event_ny.astimezone(start_utc.tzinfo)
                if start_utc < event_utc <= end_utc:
                    events.append((event_utc, nights_charged(day, holidays)))
            day += timedelta(days=1)
        events.sort(key=lambda item: item[0])
        return events

    # --- CarryingCostModel interface ------------------------------------------ #
    def cashflows(
        self,
        *,
        instrument_symbol: str,
        position_qty: float,
        interval_start_utc: str,
        interval_end_utc: str,
        context: Mapping[str, object] | None = None,
    ) -> tuple[CashflowLine, ...]:
        if not isinstance(instrument_symbol, str) or len(instrument_symbol) != 6 or not instrument_symbol.isupper():
            raise RolloverScheduleUnavailable(
                "INVALID_ARGUMENT",
                f"instrument_symbol must be a 6-letter pair, got {instrument_symbol!r}",
            )
        if isinstance(position_qty, bool) or not isinstance(position_qty, (int, float)):
            raise RolloverScheduleUnavailable(
                "INVALID_ARGUMENT", f"position_qty must be a number, got {position_qty!r}"
            )
        if not math.isfinite(float(position_qty)):
            raise RolloverScheduleUnavailable(
                "INVALID_ARGUMENT", f"position_qty must be finite, got {position_qty!r}"
            )
        try:
            start = parse_utc_timestamp(interval_start_utc, field="interval_start_utc")
            end = parse_utc_timestamp(interval_end_utc, field="interval_end_utc")
        except ValueError as exc:
            raise RolloverScheduleUnavailable("INVALID_INTERVAL", str(exc)) from exc
        if start > end:
            raise RolloverScheduleUnavailable(
                "INVALID_INTERVAL",
                f"interval_start_utc {interval_start_utc!r} is after interval_end_utc {interval_end_utc!r}",
            )
        if float(position_qty) == 0.0:
            return ()
        side = "LONG" if float(position_qty) > 0 else "SHORT"

        leg = self._schedule.leg_for(instrument_symbol, side)
        if leg is None:
            raise RolloverScheduleUnavailable(
                "MISSING_SCHEDULE_ENTRY",
                f"schedule has no {side} entry for {instrument_symbol} "
                f"(provenance={self._schedule.provenance!r}); fail closed, no default carry",
            )

        ctx = context or {}
        if "holidays" not in ctx:
            raise RolloverScheduleUnavailable(
                "MISSING_CONTEXT",
                "context['holidays'] is required (pass an explicit, possibly empty, set)",
            )
        holidays = _as_holiday_set(ctx["holidays"])

        notional = abs(float(position_qty))
        if leg.units == SWAP_POINTS:
            if "pip_size" not in ctx:
                raise RolloverScheduleUnavailable(
                    "MISSING_CONTEXT",
                    "context['pip_size'] is required for SWAP_POINTS schedules "
                    "(pair conventions live in the caller)",
                )
            pip_size = ctx["pip_size"]
            if isinstance(pip_size, bool) or not isinstance(pip_size, (int, float)) or not math.isfinite(float(pip_size)) or float(pip_size) <= 0:
                raise RolloverScheduleUnavailable(
                    "INVALID_ARGUMENT", f"pip_size must be a positive number, got {pip_size!r}"
                )
            amount_per_night = float(leg.value) * float(pip_size) * notional
        else:  # RATE_PER_NIGHT
            amount_per_night = float(leg.value) * notional

        lines: list[CashflowLine] = []
        for event_utc, multiplier in self._events_between(start, end, holidays):
            lines.append(
                CashflowLine(
                    timestamp_utc=event_utc.isoformat(),
                    amount=amount_per_night * multiplier,
                    currency=leg.quote_currency,
                    kind=ROLLOVER_KIND,
                    instrument_symbol=instrument_symbol,
                    note=ROLLOVER_NOTE,
                )
            )
        return tuple(lines)
