"""Monthly decision schedule and target-book generation for family A4.

SCHEDULE-ONLY.  Builds the frozen monthly decision clock on the frozen
``US_EQUITY_REGULAR_V1`` calendar (imported read-only from
``research/assets/stocks/calendar.py``) and emits deterministic target books
per arm.  No returns, PnL, PF or any scored metric is computed here.

Frozen clock (spec ``clock``):

- ``"evaluate on the completed daily bar of the LAST regular session (US_
  EQUITY_REGULAR_V1 calendar) of each calendar month M"``;
- ``"orders fill at the immediately following regular session (first session
  of month M+1), one-event delay, raw executable price"``;
- readiness ramp: ``"a decision at t is VALID for ETF i only if the full
  253-session TR window [t-252, t] exists"`` — decisions before the first
  full window exists are suppressed (no position change, unscored);
  ``"No truncated-lookback fallback is permitted."``
- force-flat: scored ends + S0 terminal (``warmup_folds_terminal``); ``"a
  decision whose natural holding would cross a force-flat event is closed
  early at that event"``; ``"no S1 date enters any decision, hold, feature
  or evaluation schedule"``.
"""

from __future__ import annotations

import calendar as _cal_mod
import datetime as _dt
import re
from dataclasses import dataclass
from typing import Mapping

from research.assets.stocks.calendar import (
    US_EQUITY_REGULAR_V1,
    USEquityRegularCalendar,
)

from .portfolio import (
    BookEntry,
    TargetBookStream,
    turnover_one_way,
    weight_book,
)
from .signals import (
    FAMILY_ID,
    ArmConfig,
    SymbolFeatures,
    arm_config_digest,
    compute_symbol_features,
    parse_force_flat_dates,
    parse_spec_constants,
    rank_select,
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _to_date(iso_date: str) -> _dt.date:
    return _dt.date.fromisoformat(iso_date)


@dataclass(frozen=True)
class PartitionSpec:
    """Injected frozen partition dates (from the frozen partition.json)."""

    warmup_start: str
    warmup_end: str
    s0_start: str
    s0_end: str
    s1_start: str
    s1_end: str

    def __post_init__(self) -> None:
        for name in (
            "warmup_start", "warmup_end", "s0_start", "s0_end", "s1_start", "s1_end"
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not _DATE_RE.match(value):
                raise ValueError(f"partition {name} must be an ISO date string")


@dataclass(frozen=True)
class FamilyInputs:
    """All injected inputs (NO file IO to market data, no network).

    ``sessions`` is the injected data coverage (a sorted sequence of frozen
    calendar sessions); ``tr`` carries the issuer-reconstructed total-return
    series (raw closes x issuer split factors + distributions, amended FD2,
    built upstream); ``raw_close`` carries the raw executable closes used
    ONLY for fill reference prices, never for features.
    """

    sessions: tuple[str, ...]
    tr: Mapping[str, Mapping[str, float]]
    raw_close: Mapping[str, Mapping[str, float]]
    spec: Mapping[str, object]
    partition: PartitionSpec
    calendar: USEquityRegularCalendar | None = None

    def __post_init__(self) -> None:
        calendar = self.calendar or US_EQUITY_REGULAR_V1
        object.__setattr__(self, "calendar", calendar)
        sessions = self.sessions
        if len(set(sessions)) != len(sessions) or list(sessions) != sorted(sessions):
            raise ValueError("sessions must be sorted and unique")
        for day in sessions:
            if not calendar.is_session_day(_to_date(day)):
                raise ValueError(f"session {day} is not a US_EQUITY_REGULAR_V1 session")
        consts = parse_spec_constants(self.spec)
        for symbol in consts.rankable:
            if symbol not in self.tr or symbol not in self.raw_close:
                raise ValueError(f"missing injected series for rankable symbol {symbol}")


@dataclass(frozen=True)
class DecisionSlot:
    """One monthly decision slot on the frozen clock."""

    decision_date: str
    fill_date: str
    month: str                                      # YYYY-MM
    fold_id: str
    decision_index: int                             # index into sessions
    suppressed: bool
    suppressed_reason: str | None = None


def fold_id_for_date(spec: Mapping[str, object], iso_date: str) -> str | None:
    """Fold whose [start, end] window contains the date, else None."""
    day = _to_date(iso_date)
    for fold in spec["warmup_folds_terminal"]["s0_folds"]:
        if _to_date(fold["start"]) <= day <= _to_date(fold["end"]):
            return str(fold["fold_id"])
    return None


def last_session_of_month(
    calendar: USEquityRegularCalendar, year: int, month: int
) -> str | None:
    """ISO date of the LAST regular session of the month (frozen calendar)."""
    last_day = _cal_mod.monthrange(year, month)[1]
    sessions = calendar.sessions_in_range(_dt.date(year, month, 1), _dt.date(year, month, last_day))
    if not sessions:
        return None
    return sessions[-1].start_utc.date().isoformat()


def build_decision_slots(inputs: FamilyInputs) -> tuple[DecisionSlot, ...]:
    """Enumerate the frozen monthly decision slots (chronological).

    A slot exists for each calendar month whose last regular session lies in
    S0 and whose fill session (the immediately following regular session) is
    still <= s0_end — enforcing the S1 seal.  Slots before the first full
    253-session window are marked suppressed (ramp rule, unscored).
    """
    calendar: USEquityRegularCalendar = inputs.calendar  # type: ignore[assignment]
    assert calendar is not None
    session_index = {day: i for i, day in enumerate(inputs.sessions)}
    consts = parse_spec_constants(inputs.spec)
    start = _to_date(inputs.partition.s0_start)
    end = _to_date(inputs.partition.s0_end)
    slots: list[DecisionSlot] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        decision_date = last_session_of_month(calendar, year, month)
        month_label = f"{year:04d}-{month:02d}"
        month += 1
        if month > 12:
            year, month = year + 1, 1
        if decision_date is None:
            continue
        if decision_date < inputs.partition.s0_start or decision_date > inputs.partition.s0_end:
            continue
        if decision_date not in session_index:
            # Decision session exists on the frozen calendar but outside the
            # injected coverage: fail closed (never fabricate bars).
            raise ValueError(
                f"decision session {decision_date} is outside injected coverage"
            )
        fill_date = calendar.next_session(_to_date(decision_date)).start_utc.date().isoformat()
        if fill_date > inputs.partition.s0_end:
            continue  # the fill would land in sealed S1: no such decision
        index = session_index[decision_date]
        suppressed = index + 1 < consts.readiness_sessions
        slots.append(
            DecisionSlot(
                decision_date=decision_date,
                fill_date=fill_date,
                month=month_label,
                fold_id=fold_id_for_date(inputs.spec, decision_date) or "OUTSIDE_FOLDS",
                decision_index=index,
                suppressed=suppressed,
                suppressed_reason="INSUFFICIENT_LOOKBACK" if suppressed else None,
            )
        )
    return tuple(slots)


def force_flat_events(inputs: FamilyInputs) -> tuple[str, ...]:
    """Frozen force-flat dates (fold scored ends + S0 terminal), ascending."""
    dates = parse_force_flat_dates(inputs.spec)
    for day in dates:
        if day > inputs.partition.s0_end:
            raise ValueError(f"force-flat event {day} lies beyond S0; fail closed")
    return dates


def generate_target_book(
    inputs: FamilyInputs, config: ArmConfig
) -> TargetBookStream:
    """Deterministic target-book stream for one arm (double-generation equal).

    Walks the frozen decision slots chronologically, carries the previous
    book, emits one ``decision_fill`` entry per valid decision (fill at the
    NEXT session on raw executable closes) and one ``force_flat`` entry per
    force-flat event that actually flattens a non-empty book (costed exit
    in schedule terms; the flat is an event book with empty targets).
    Suppressed decisions produce no entry and no position change.
    """
    consts = parse_spec_constants(inputs.spec)
    rankable = list(consts.rankable)
    slots = build_decision_slots(inputs)
    events = force_flat_events(inputs)

    entries: list[BookEntry] = []
    suppressed_dates: list[str] = []
    per_fold_valid: dict[str, int] = {}
    prev_book: dict[str, float] = {}
    event_pos = 0

    def emit_force_flats(up_to_date: str) -> None:
        """Fire every force-flat event with date <= up_to_date, in order.

        Events on a fill date fire AFTER that fill (the fill happens at the
        session, the force-flat at that session's close).
        """
        nonlocal prev_book, event_pos
        while event_pos < len(events) and events[event_pos] <= up_to_date:
            event_date = events[event_pos]
            event_pos += 1
            if not prev_book:
                continue  # book already flat: nothing to flatten
            fold = fold_id_for_date(inputs.spec, event_date) or "S0_TERMINAL"
            entries.append(
                BookEntry(
                    entry_type="force_flat",
                    fill_date=event_date,
                    fold_id=fold,
                    targets={},
                    cash_weight=1.0,
                    gross=0.0,
                    turnover_one_way=turnover_one_way(prev_book, {}),
                    fill_ref_prices={},
                )
            )
            prev_book = {}

    for slot in slots:
        emit_force_flats(_prev_date(slot.fill_date))
        if slot.suppressed:
            suppressed_dates.append(slot.decision_date)
            continue  # ramp rule: no position change, unscored
        features: dict[str, SymbolFeatures] = {}
        for symbol in rankable:
            features[symbol] = compute_symbol_features(
                tr=inputs.tr[symbol],
                sessions=inputs.sessions,
                index=slot.decision_index,
                formation_sessions=consts.formation_sessions,
                skip_sessions=consts.skip_sessions,
                symbol=symbol,
            )
        selected = rank_select(features, config)
        sigma_by_symbol = {
            s: features[s].sigma for s in selected if features[s].sigma is not None
        }
        weights = weight_book(selected, config, sigma_by_symbol)
        gross = sum(weights.values())
        cash = 1.0 - gross
        ref_prices: dict[str, float] = {}
        for symbol in sorted(weights):
            raw_value = inputs.raw_close[symbol].get(slot.fill_date)
            if raw_value is None:
                raise ValueError(
                    f"no raw close for {symbol} on fill date {slot.fill_date}; "
                    "fail closed (no synthetic fill)"
                )
            ref_prices[symbol] = float(raw_value)
        entries.append(
            BookEntry(
                entry_type="decision_fill",
                decision_date=slot.decision_date,
                fill_date=slot.fill_date,
                fold_id=slot.fold_id,
                targets=dict(weights),
                cash_weight=cash,
                gross=gross,
                turnover_one_way=turnover_one_way(prev_book, weights),
                fill_ref_prices=ref_prices,
            )
        )
        per_fold_valid[slot.fold_id] = per_fold_valid.get(slot.fold_id, 0) + 1
        prev_book = dict(weights)

    emit_force_flats(inputs.partition.s0_end)

    # --- schedule summary (decision counts and weight turnover only) ------ #
    turnover_per_year: dict[str, float] = {}
    for entry in entries:
        year_label = entry.fill_date[:4]
        turnover_per_year[year_label] = (
            turnover_per_year.get(year_label, 0.0) + entry.turnover_one_way
        )
    spec_slots = inputs.spec["evidence_count"]["expected_calendar_slots_s0"]
    summary: dict[str, object] = {
        "decision_frequency": "MONTHLY_LAST_REGULAR_SESSION",
        "fill_rule": "NEXT_SESSION_RAW_CLOSE_ONE_EVENT_DELAY",
        "valid_decision_count": sum(per_fold_valid.values()),
        "decisions_per_fold": dict(sorted(per_fold_valid.items())),
        "suppressed_warmup_extension_count": len(suppressed_dates),
        "suppressed_warmup_extension_dates": list(suppressed_dates),
        "force_flat_dates": list(events),
        "turnover_per_year_one_way": {
            year_label: round(total, 10)
            for year_label, total in sorted(turnover_per_year.items())
        },
        "total_turnover_one_way": round(
            sum(entry.turnover_one_way for entry in entries), 10
        ),
        "spec_recorded_calendar_slots_s0": {
            "fold1": spec_slots["fold1"],
            "fold2": spec_slots["fold2"],
            "fold3": spec_slots["fold3"],
            "total": spec_slots["total"],
        },
        "turnover_convention": "SUM_ABS_DELTA_WEIGHTS_ETF_ONLY_ONE_WAY",
    }
    return TargetBookStream(
        family_id=FAMILY_ID,
        arm_id=config.arm_id,
        arm_config_digest=arm_config_digest(inputs.spec),
        calendar_id=inputs.calendar.calendar_id,  # type: ignore[union-attr]
        entries=tuple(entries),
        summary=summary,
    )


def _prev_date(iso_date: str) -> str:
    return (_to_date(iso_date) - _dt.timedelta(days=1)).isoformat()
