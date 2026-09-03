"""Deterministic TOM-SETTLE schedules: month ordinals, windows, target books.

Owner: lane A9, STOCKS-FREE-V3 family 2 (SFV3-A6-TOM-SETTLE).  Implements the
frozen contract in ``research/control/stocks_free_v3_run/selection_freeze.json``
(families[1]) from the mechanism source
``research/proposals/stocks_free_v3/a6_family_SFV3-A6-TOM-SETTLE.md``
(sections 4-6, 8).  This module is SCHEDULE ONLY: deterministic calendar
arithmetic and target-book emission — no data access, no disk writes, no
network, and NO PnL of any kind.

Frozen mechanics (proposal sections 4-5):

* Month ordinals are counted on the REGULAR-SESSION calendar (a sorted list of
  ISO session strings, e.g. the ``US_EQUITY_REGULAR_V1`` sessions), never on
  calendar dates: holiday-thinned months are handled with no special cases.
* Window membership per arm — see :mod:`...family_tom_settle.config`.
* Decision clock: at the close of completed session T the target book for the
  fill at the close of T+1 is fully determined — TOM book if T+1 is a window
  session, BASE book otherwise.  Fills happen ONLY where the book changes
  (24 transitions/yr on full years) plus the initial establishment fill at the
  first coverage session; legs drift between scheduled transitions and are
  never traded (no intra-window re-equalization).
* Books: TOM = 11 cohort ETFs at ``TOM_GROSS/11`` each (gross 0.50); BASE =
  11 at ``BASE_GROSS/11`` each (gross 0.30); CASH is the explicit residual
  leg, never a tradable leg and never in turnover.
* Windows straddling fold/purge boundaries simply lose those scored sessions;
  the schedule itself spans the declared coverage sessions and makes no
  compensation trades.

Two independent generation paths are provided and must agree BYTE-IDENTICALLY
(canonical JSON of the fill payloads), pinned by tests:

* :func:`build_schedule` — session walk: desired book per session from window
  membership, emit a fill whenever the book changes;
* :func:`build_schedule_from_windows` — window blocks first: one entry fill at
  the first session of each maximal window run and one exit fill at the first
  session after it, plus the establishment fill at the coverage start.

Schedule-only feasibility (:func:`schedule_feasibility`) reports transitions
and one-way turnover sums WITHOUT computing any PnL: the frozen expectation is
24 transitions and 4.80 two-way per complete calendar year (12 windows x
[entry + exit], each |delta gross| = 0.20), inside the 6.0x ceiling, and a
gross envelope of [0.30, 0.50].
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.assets.common.contracts import canonical_json
from research.assets.stocks.factory import CASH_SYMBOL, etf_leg_turnover
from research.stocks_free_v3.family_tom_settle.config import (
    BOOK_BASE,
    BOOK_TOM,
    BASE_GROSS,
    FAMILY_SCHEMA,
    MIN_MONTH_SESSIONS,
    MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT,
    TOM_GROSS,
    EXPECTED_TRANSITIONS_PER_YEAR,
    TURNOVER_CEILING_TWO_WAY_PER_YEAR,
    ArmConfig,
    ArmConfigError,
    WindowRule,
    build_arm_configs,
)

#: The gross envelope the books must stay inside (the arm's designed range).
cfg_gross_min = BASE_GROSS
cfg_gross_max = TOM_GROSS

_ISO_SESSION = re.compile(r"^\d{4}-\d{2}-\d{2}$")

#: The implicit book held before the first coverage session is all-CASH; the
#: establishment fill moves the gross from 0.0 to the desired book's gross.
INITIAL_WEIGHTS: Mapping[str, float] = {CASH_SYMBOL: 1.0}


class ScheduleError(ValueError):
    """Raised when a schedule cannot be built from the declared sessions."""


# --------------------------------------------------------------------------- #
# month ordinals on a session calendar
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SessionOrdinal:
    """One regular session with its regular-session month coordinates."""

    session: str            # ISO date of the regular session
    month: str              # "YYYY-MM" calendar month key
    ordinal: int            # 1-based regular-session ordinal inside the month
    month_length: int       # number of regular sessions in the month

    def to_payload(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "month": self.month,
            "ordinal": self.ordinal,
            "month_length": self.month_length,
        }


def month_ordinals(sessions: Sequence[str]) -> tuple[SessionOrdinal, ...]:
    """Regular-session month ordinals over a sorted session calendar.

    Groups the declared sessions by calendar month in order and numbers them
    1..n within each month.  Fail-closed on: empty input, unsorted or
    duplicated sessions, non-ISO session strings, and any month with fewer
    than ``MIN_MONTH_SESSIONS`` regular sessions (real US equity months have
    19-23; the floor only rejects synthetic misuse that could make the
    mid-month control window empty).
    """
    if not sessions:
        raise ScheduleError("sessions must be a non-empty ascending ISO list")
    unknown = [s for s in sessions if not isinstance(s, str) or not _ISO_SESSION.match(s)]
    if unknown:
        raise ScheduleError(f"non-ISO session strings: {unknown[:5]!r}")
    if list(sessions) != sorted(set(sessions)):
        raise ScheduleError("sessions must be sorted ascending and unique")

    by_month: dict[str, list[str]] = {}
    for s in sessions:
        by_month.setdefault(s[:7], []).append(s)
    short = {m: len(v) for m, v in by_month.items() if len(v) < MIN_MONTH_SESSIONS}
    if short:
        raise ScheduleError(
            f"months with fewer than {MIN_MONTH_SESSIONS} regular sessions "
            f"(real US months have 19-23; refusing to guess): {short}"
        )
    out: list[SessionOrdinal] = []
    for month in sorted(by_month):
        month_sessions = by_month[month]
        for i, s in enumerate(month_sessions, start=1):
            out.append(SessionOrdinal(s, month, i, len(month_sessions)))
    return tuple(out)


def sessions_by_month(sessions: Sequence[str]) -> dict[str, tuple[str, ...]]:
    """Ordered ``{month_key: sessions}`` view (single pass over month ordinals)."""
    out: dict[str, list[str]] = {}
    for rec in month_ordinals(sessions):
        out.setdefault(rec.month, []).append(rec.session)
    return {m: tuple(v) for m, v in sorted(out.items())}


def window_ordinals(rule: WindowRule, month_length: int) -> tuple[int, ...]:
    """Window ordinals of one arm's rule for one month length."""
    return rule.window_ordinals(month_length)


def is_window_session(rule: WindowRule, rec: SessionOrdinal) -> bool:
    """True when ``rec`` is one of the arm's window sessions in its month."""
    return rec.ordinal in rule.window_ordinals(rec.month_length)


def desired_book(cfg: ArmConfig, rec: SessionOrdinal) -> str:
    """The book the arm must hold at session ``rec``: TOM inside the window, BASE outside."""
    return BOOK_TOM if is_window_session(cfg.window, rec) else BOOK_BASE


def anchor_control_disjoint(month_length: int) -> bool:
    """True iff the anchor and control windows cannot share a session.

    Anchor ordinals are ``{1, 2} | {n-2, n-1, n}``; control ordinals are
    ``{8..12}``.  They are disjoint for every ``month_length >= 15`` (12 <
    n - 2); every real US equity month has 19-23 regular sessions.  Months
    below the frozen minimum raise (fail-closed) in
    :func:`month_ordinals` already.
    """
    rule_a = build_arm_configs()["A"].window
    rule_c = build_arm_configs()["C"].window
    a = set(rule_a.window_ordinals(month_length))
    c = set(rule_c.window_ordinals(month_length))
    return not a & c


def assert_anchor_control_disjoint(sessions: Sequence[str]) -> dict[str, Any]:
    """Fail closed unless A and C windows are disjoint on every qualifying month.

    A month qualifies when it has at least
    ``MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT`` (15) regular sessions — the
    provenance of the frozen disjointness claim ("ordinals 8-12 are disjoint
    from the anchor window for all month lengths"); every real US equity month
    (19-23 sessions) qualifies, so on real calendars the guarantee is
    absolute.  Shorter months can only exist in synthetic partial-coverage
    slices; there the mathematical predicate is below the threshold and the
    month is reported as skipped instead of guessed about.  Returns the
    ``{"months_checked", "months_skipped"}`` evidence.
    """
    cfgs = build_arm_configs()
    ords = month_ordinals(sessions)
    a_sessions = {r.session for r in ords if is_window_session(cfgs["A"].window, r)}
    c_sessions = {r.session for r in ords if is_window_session(cfgs["C"].window, r)}
    overlap = sorted(a_sessions & c_sessions)
    lengths = {r.month: r.month_length for r in ords}
    qualifying = {m for m, n in lengths.items() if n >= MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT}
    overlap_qualifying = sorted(s for s in overlap if s[:7] in qualifying)
    if overlap_qualifying:
        raise ScheduleError(
            f"anchor and control windows overlap on {overlap_qualifying[:5]!r} in "
            f"month(s) with >= {MIN_MONTH_SESSIONS_ANCHOR_CONTROL_DISJOINT} "
            "sessions; the frozen disjointness claim is violated"
        )
    return {
        "months_checked": len(qualifying),
        "months_skipped": len(lengths) - len(qualifying),
        "min_month_length": min(lengths.values()),
        "max_month_length": max(lengths.values()),
    }


# --------------------------------------------------------------------------- #
# frozen target books (explicit CASH residual leg)
# --------------------------------------------------------------------------- #
def tom_targets(cfg: ArmConfig) -> dict[str, float]:
    """TOM book: 11 cohort legs at gross/11 each plus the explicit CASH residual."""
    w = cfg.leg_weight(BOOK_TOM)
    legs = {s: w for s in cfg.symbols}
    legs[CASH_SYMBOL] = 1.0 - cfg.tom_gross
    return legs


def base_targets(cfg: ArmConfig) -> dict[str, float]:
    """BASE book: 11 cohort legs at gross/11 each plus the explicit CASH residual."""
    w = cfg.leg_weight(BOOK_BASE)
    legs = {s: w for s in cfg.symbols}
    legs[CASH_SYMBOL] = 1.0 - cfg.base_gross
    return legs


def targets_for_book(cfg: ArmConfig, book: str) -> dict[str, float]:
    if book == BOOK_TOM:
        return tom_targets(cfg)
    if book == BOOK_BASE:
        return base_targets(cfg)
    raise ArmConfigError(f"unknown book {book!r}")


# --------------------------------------------------------------------------- #
# scheduled fills and the arm schedule
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ScheduledFill:
    """One scheduled close-fill event of an arm.

    ``decision_session`` is the completed session T whose close determined the
    book (``fill_session`` = T+1 by the canonical close-fill clock);
    ``None`` only for the establishment fill at the first coverage session.
    ``turnover_one_way`` is the schedule-only one-way turnover of the pure
    target books (drift-adjusted realized turnover is a scoring-time quantity
    and is deliberately NOT computed here).
    """

    fill_session: str
    decision_session: str | None
    book: str
    establishment: bool
    targets: Mapping[str, float]
    turnover_one_way: float

    def to_payload(self) -> dict[str, Any]:
        return {
            "fill_session": self.fill_session,
            "decision_session": self.decision_session,
            "book": self.book,
            "establishment": self.establishment,
            "targets": {s: self.targets[s] for s in sorted(self.targets)},
            "turnover_one_way": self.turnover_one_way,
        }


@dataclass(frozen=True)
class ArmSchedule:
    """One arm's deterministic schedule over the declared coverage sessions."""

    arm_id: str
    arm_key: str
    config_digest: str
    sessions: tuple[str, ...]
    window_sessions: tuple[str, ...]
    fills: tuple[ScheduledFill, ...]

    @property
    def transitions(self) -> tuple[ScheduledFill, ...]:
        """Scheduled fills excluding the initial establishment fill."""
        return tuple(f for f in self.fills if not f.establishment)

    @property
    def establishment_fill(self) -> ScheduledFill:
        est = [f for f in self.fills if f.establishment]
        if len(est) != 1:
            raise ScheduleError(
                f"expected exactly one establishment fill, found {len(est)}"
            )
        return est[0]

    def fills_between(self, start: str, end: str) -> tuple[ScheduledFill, ...]:
        """Fills with ``start <= fill_session <= end`` (ISO string compare)."""
        return tuple(f for f in self.fills if start <= f.fill_session <= end)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "config_digest": self.config_digest,
            "sessions": list(self.sessions),
            "window_sessions": list(self.window_sessions),
            "fills": [f.to_payload() for f in self.fills],
        }

    def canonical_json(self) -> str:
        """Byte-stable canonical JSON of the whole schedule."""
        return canonical_json(self.to_payload())

    @property
    def schedule_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _validate_config_sessions(cfg: ArmConfig, sessions: Sequence[str]) -> tuple[SessionOrdinal, ...]:
    if cfg.arm_key not in ("A", "N", "C"):
        raise ArmConfigError(f"unknown arm key {cfg.arm_key!r}")
    return month_ordinals(sessions)


def _establishment_fill(cfg: ArmConfig, first: str, book: str) -> ScheduledFill:
    targets = targets_for_book(cfg, book)
    turnover = etf_leg_turnover(INITIAL_WEIGHTS, targets)
    return ScheduledFill(
        fill_session=first,
        decision_session=None,
        book=book,
        establishment=True,
        targets=targets,
        turnover_one_way=turnover,
    )


def _transition_fill(cfg: ArmConfig, rec: SessionOrdinal, prev_rec: SessionOrdinal,
                     book: str, previous_book: str) -> ScheduledFill:
    targets = targets_for_book(cfg, book)
    previous = targets_for_book(cfg, previous_book)
    return ScheduledFill(
        fill_session=rec.session,
        decision_session=prev_rec.session,
        book=book,
        establishment=False,
        targets=targets,
        turnover_one_way=etf_leg_turnover(previous, targets),
    )


def build_schedule(cfg: ArmConfig, sessions: Sequence[str]) -> ArmSchedule:
    """Path 1 — session walk.

    The desired book of each session is a pure function of its window
    membership; a scheduled fill is emitted at the first coverage session
    (establishment) and at every session whose desired book differs from the
    previous session's desired book.  The decision session of a transition is
    the immediately preceding session (T -> T+1 close-fill clock).
    """
    ords = _validate_config_sessions(cfg, sessions)
    fills: list[ScheduledFill] = []
    fills.append(_establishment_fill(cfg, ords[0].session, desired_book(cfg, ords[0])))
    for prev, cur in zip(ords, ords[1:]):
        book = desired_book(cfg, cur)
        if book != desired_book(cfg, prev):
            fills.append(_transition_fill(cfg, cur, prev, book, desired_book(cfg, prev)))
    window_sessions = tuple(r.session for r in ords if is_window_session(cfg.window, r))
    return ArmSchedule(
        arm_id=cfg.arm_id,
        arm_key=cfg.arm_key,
        config_digest=cfg.digest,
        sessions=tuple(sessions),
        window_sessions=window_sessions,
        fills=tuple(fills),
    )


def build_schedule_from_windows(cfg: ArmConfig, sessions: Sequence[str]) -> ArmSchedule:
    """Path 2 — window blocks first.

    Computes the maximal contiguous runs of window sessions, emits one entry
    fill (TOM) at the first session of each run and one exit fill (BASE) at
    the first session after the run (omitted when the run ends at the last
    coverage session — the schedule never trades beyond coverage), then adds
    the establishment fill at the first coverage session.  MUST agree
    byte-identically with :func:`build_schedule` (pinned by tests).
    """
    ords = _validate_config_sessions(cfg, sessions)
    in_window = [is_window_session(cfg.window, r) for r in ords]
    blocks: list[tuple[int, int]] = []   # inclusive [start_idx, end_idx] runs of window
    i = 0
    while i < len(ords):
        if in_window[i]:
            j = i
            while j + 1 < len(ords) and in_window[j + 1]:
                j += 1
            blocks.append((i, j))
            i = j + 1
        else:
            i += 1

    events: dict[str, ScheduledFill] = {}
    if in_window[0]:
        events[ords[0].session] = _establishment_fill(cfg, ords[0].session, BOOK_TOM)
    else:
        events[ords[0].session] = _establishment_fill(cfg, ords[0].session, BOOK_BASE)
    for start_idx, end_idx in blocks:
        entry_session = ords[start_idx].session
        if entry_session not in events:  # establishment may already occupy it
            prev_rec = ords[start_idx - 1]
            events[entry_session] = _transition_fill(
                cfg, ords[start_idx], prev_rec, BOOK_TOM, BOOK_BASE
            )
        if end_idx + 1 < len(ords):
            exit_rec = ords[end_idx + 1]
            prev_rec = ords[end_idx]
            events[exit_rec.session] = _transition_fill(
                cfg, exit_rec, prev_rec, BOOK_BASE, BOOK_TOM
            )
    fills = tuple(events[s] for s in sorted(events))
    window_sessions = tuple(r.session for r in ords if is_window_session(cfg.window, r))
    return ArmSchedule(
        arm_id=cfg.arm_id,
        arm_key=cfg.arm_key,
        config_digest=cfg.digest,
        sessions=tuple(sessions),
        window_sessions=window_sessions,
        fills=fills,
    )


def schedules_equal(a: ArmSchedule, b: ArmSchedule) -> bool:
    """Byte-level equality of two schedules' canonical JSON payloads."""
    return a.canonical_json() == b.canonical_json()


# --------------------------------------------------------------------------- #
# schedule-only feasibility (no PnL anywhere in this section)
# --------------------------------------------------------------------------- #
def complete_calendar_years(sessions: Sequence[str]) -> tuple[int, ...]:
    """Calendar years fully interior to the coverage span.

    A year Y is complete when the coverage starts strictly before Y-01-01 (so
    the establishment fill and every January boundary decision lie outside Y)
    and covers Y-12-31 itself (so every in-year fill, including the December
    window's entry, is observable).  The December window's exit lands in
    January of Y+1 and is deliberately NOT counted inside Y; with these bounds
    every complete year shows exactly 24 transitions and 4.80 one-way turnover
    sum for each arm.
    """
    if not sessions:
        raise ScheduleError("sessions must be non-empty")
    first_year = int(sessions[0][:4])
    last_year = int(sessions[-1][:4])
    return tuple(y for y in range(first_year, last_year + 1)
                 if sessions[0] < f"{y}-01-01" and sessions[-1] >= f"{y}-12-31")


def year_turnover(schedule: ArmSchedule, year: int) -> dict[str, Any]:
    """Transitions and one-way turnover sum inside one calendar year.

    The establishment fill is excluded everywhere (it is bookkeeping at the
    coverage boundary, not a monthly transition).
    """
    transitions = schedule.fills_between(f"{year}-01-01", f"{year}-12-31")
    transitions = tuple(f for f in transitions if not f.establishment)
    return {
        "year": year,
        "transitions": len(transitions),
        "one_way_turnover_sum": sum(f.turnover_one_way for f in transitions),
        "entries": sum(1 for f in transitions if f.book == BOOK_TOM),
        "exits": sum(1 for f in transitions if f.book == BOOK_BASE),
    }


def schedule_feasibility(schedules: Mapping[str, ArmSchedule]) -> dict[str, Any]:
    """Schedule-only feasibility across the family's arms — NO PnL is computed.

    Reports, per arm and per complete calendar year: transitions (frozen
    expectation 24), one-way turnover sum (frozen expectation 4.80, the
    proposal's "two-way per year" arithmetic), window-session counts, the
    gross envelope, the turnover-ceiling verdict, and the family-level
    anchor/control window disjointness over the shared calendar.
    """
    per_arm: dict[str, Any] = {}
    shared_sessions: tuple[str, ...] = ()
    disjointness: dict[str, Any] = {}
    for key in sorted(schedules):
        sched = schedules[key]
        shared_sessions = sched.sessions
        years = [year_turnover(sched, y) for y in complete_calendar_years(sched.sessions)]
        gross_per_fill = [
            math.fsum(w for s, w in f.targets.items() if s != CASH_SYMBOL)
            for f in sched.fills
        ]
        per_arm[key] = {
            "arm_id": sched.arm_id,
            "config_digest": sched.config_digest,
            "schedule_digest": sched.schedule_digest,
            "coverage_sessions": len(sched.sessions),
            "window_sessions": len(sched.window_sessions),
            "n_fills": len(sched.fills),
            "n_transitions": len(sched.transitions),
            "windows": len(sched.transitions) // 2,
            "gross_min": min(gross_per_fill) if gross_per_fill else None,
            "gross_max": max(gross_per_fill) if gross_per_fill else None,
            "gross_envelope_ok": bool(gross_per_fill)
            and min(gross_per_fill) >= cfg_gross_min - 1e-9
            and max(gross_per_fill) <= cfg_gross_max + 1e-9,
            "complete_years": [
                {
                    **y,
                    "transitions_ok": y["transitions"] == EXPECTED_TRANSITIONS_PER_YEAR,
                    "turnover_two_way_per_year": y["one_way_turnover_sum"],
                    "turnover_ok": (
                        abs(y["one_way_turnover_sum"] - 4.80) < 1e-9
                    ),
                }
                for y in years
            ],
        }
    if shared_sessions:
        disjointness = assert_anchor_control_disjoint(shared_sessions)
    all_ok = all(
        arm["gross_envelope_ok"]
        and all(y["transitions_ok"] and y["turnover_ok"] for y in arm["complete_years"])
        and arm["complete_years"]
        for arm in per_arm.values()
    )
    return {
        "schema": FAMILY_SCHEMA,
        "feasibility": "SCHEDULE_ONLY_NO_PNL",
        "turnover_ceiling_two_way_per_year": TURNOVER_CEILING_TWO_WAY_PER_YEAR,
        "expected_transitions_per_year": EXPECTED_TRANSITIONS_PER_YEAR,
        "anchor_control_disjoint": True,
        "anchor_control_disjoint_evidence": disjointness,
        "all_arms_within_gate": all_ok,
        "arms": per_arm,
    }


__all__ = [
    "EXPECTED_TRANSITIONS_PER_YEAR",
    "INITIAL_WEIGHTS",
    "ArmSchedule",
    "ScheduleError",
    "ScheduledFill",
    "SessionOrdinal",
    "anchor_control_disjoint",
    "assert_anchor_control_disjoint",
    "base_targets",
    "build_schedule",
    "build_schedule_from_windows",
    "complete_calendar_years",
    "desired_book",
    "is_window_session",
    "month_ordinals",
    "schedule_feasibility",
    "schedules_equal",
    "sessions_by_month",
    "targets_for_book",
    "tom_targets",
    "window_ordinals",
    "year_turnover",
]
