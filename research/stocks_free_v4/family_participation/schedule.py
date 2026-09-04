"""Anchored 63-session decision schedules for SFV4-A5-H1 (A8).

Owner: lane A8, STOCKS-FREE-V4 family 1 (SFV4-A5-H1-PARTICIPATION-SHIFT).
Implements the frozen schedule rules from
``research/control/stocks_free_v4_run/selection_freeze.json`` (byte-exact
clock condition) and ``research/control/stocks_free_v4_run/proposals/a5_h1.json``
("universe_and_schedule", "holding_period", "fill_clock", "sample_size_floor")
on top of :mod:`research.stocks_free_v4.family_participation.config`.

This module is SCHEDULE ONLY: deterministic calendar arithmetic over a
caller-supplied master session calendar.  No data access, no disk writes, no
network, and NO PnL and NO feature values — on real data the emitted payloads
carry dates and counts only.

Frozen mechanics
----------------
* Master calendar: the SPY session list from the staged snapshot (the
  proposal's "derived deterministically from the snapshot calendar"); must be
  sorted ascending and unique.
* Decision clock (selection-freeze byte-exact pin): decisions at master
  indexes ``anchor_index + 63*k`` for ``k = 0, 1, 2, ...`` where the anchor is
  the S0 start session 2018-04-04, until the last fold end.  A tick whose
  session falls inside a fold is that fold's decision slot; a tick inside a
  fold gap (the purge gap between folds) would be VOIDED and is recorded —
  per the proposal's sample-size floor a voided slot is never re-timed.  On
  the real snapshot there are zero voided ticks (verified by test).
* Fill clock: the decision at session ``t`` fills at the NEXT allowed
  session (``master[t + 1]``) — never the same session.  Fail-closed when no
  next session exists.
* Holding: weights are fixed between decision slots (63-session clock); the
  final decision book of each fold is truncated at the fold boundary by a
  FORCE_FLAT fill AT the fold end session, so no position carries across a
  fold boundary (baseline invariants force-flat rule).
* Fold spans on the real snapshot are exactly 609 sessions each, so the
  anchored clock yields exactly 10 decision slots per fold and 30 overall —
  the proposal's expected sample, meeting the frozen floors (>=5 per fold,
  >=30 total) with zero slack.

Two independent generation paths are provided and must agree BYTE-IDENTICALLY
(canonical JSON of the schedule payloads), pinned by tests:

* :func:`build_arm_schedule_walk` — sequential clock walk appending decision
  slots, then fold force-flats;
* :func:`build_arm_schedule_blockwise` — fold blocks first (decision slots
  grouped per fold), then events merged by kind in frozen order.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.assets.common.contracts import canonical_json
from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v4.family_participation.config import (
    ANCHOR_SESSION,
    CLOCK_PERIOD_SESSIONS,
    DECISION_LAG_SESSIONS,
    FAMILY_ID,
    FAMILY_SCHEMA,
    FOLDS,
    WARMUP_SESSIONS,
    ArmConfig,
    Fold,
)
from research.stocks_free_v4.family_participation.features import eligibility


class ScheduleError(ValueError):
    """Raised when a schedule cannot be built from the declared sessions."""


# --------------------------------------------------------------------------- #
# master calendar helpers
# --------------------------------------------------------------------------- #
def validate_master_dates(dates: Sequence[str]) -> tuple[str, ...]:
    """Fail-closed calendar validation; returns the tuple form."""
    if not dates:
        raise ScheduleError("master calendar must be non-empty")
    if list(dates) != sorted(set(dates)):
        raise ScheduleError("master calendar must be sorted ascending and unique")
    if any(not isinstance(d, str) or len(d) != 10 or d[4] != "-" or d[7] != "-"
           for d in dates):
        raise ScheduleError(f"non-ISO session strings: {dates[:5]!r}")
    return tuple(dates)


def anchor_index(dates: Sequence[str],
                 anchor_session: str = ANCHOR_SESSION) -> int:
    """Index of the frozen clock anchor session (fail-closed if absent)."""
    try:
        return list(dates).index(anchor_session)
    except ValueError as exc:
        raise ScheduleError(
            f"clock anchor session {anchor_session!r} not on the master calendar"
        ) from exc


@dataclass(frozen=True)
class DecisionSlot:
    """One anchored-clock decision slot with its fold assignment and fill."""

    k: int                    # clock tick number (anchor tick is k=0)
    session: str              # decision session (PIT close)
    index: int                # index in the master calendar
    fold_id: str | None       # containing fold (None = voided, in a fold gap)
    fill_session: str | None  # next allowed session (None only when voided)

    def to_payload(self) -> dict[str, Any]:
        return {
            "k": self.k,
            "session": self.session,
            "index": self.index,
            "fold_id": self.fold_id,
            "fill_session": self.fill_session,
        }


@dataclass(frozen=True)
class ForceFlat:
    """One fold-boundary force-flat fill (at the fold end session)."""

    fold_id: str
    session: str

    def to_payload(self) -> dict[str, Any]:
        return {"fold_id": self.fold_id, "session": self.session}


@dataclass(frozen=True)
class ArmSchedule:
    """One arm's deterministic anchored-clock schedule (dates + counts only)."""

    arm_id: str
    arm_key: str
    role: str
    config_digest: str
    decisions: tuple[DecisionSlot, ...]
    voided: tuple[DecisionSlot, ...]
    force_flats: tuple[ForceFlat, ...]
    master_sessions_total: int
    master_first: str
    master_last: str
    anchor_index_value: int

    @property
    def decided(self) -> tuple[DecisionSlot, ...]:
        """Decision slots actually inside folds (never voided)."""
        return tuple(d for d in self.decisions if d.fold_id is not None)

    def decisions_in_fold(self, fold_id: str) -> tuple[DecisionSlot, ...]:
        return tuple(d for d in self.decided if d.fold_id == fold_id)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "role": self.role,
            "config_digest": self.config_digest,
            "clock": {
                "anchor_session": ANCHOR_SESSION,
                "period_sessions": CLOCK_PERIOD_SESSIONS,
                "anchor_index": self.anchor_index_value,
                "decision_lag_sessions": DECISION_LAG_SESSIONS,
                "master_sessions_total": self.master_sessions_total,
                "master_first": self.master_first,
                "master_last": self.master_last,
            },
            "decisions": [d.to_payload() for d in self.decisions],
            "voided_ticks": [v.to_payload() for v in self.voided],
            "force_flats": [f.to_payload() for f in self.force_flats],
            "counts": {
                "decisions": len(self.decided),
                "voided": len(self.voided),
                "force_flats": len(self.force_flats),
            },
        }

    def canonical_json(self) -> str:
        """Byte-stable canonical JSON of the whole schedule."""
        return canonical_json(self.to_payload())

    @property
    def schedule_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _fold_of(session: str, folds: Sequence[Fold] = FOLDS) -> str | None:
    """The fold containing ``session`` (ISO strings compare chronologically)."""
    for fold in folds:
        if fold.start <= session <= fold.end:
            return fold.fold_id
    return None


def clock_slots(dates: Sequence[str],
                anchor_session: str = ANCHOR_SESSION,
                period: int = CLOCK_PERIOD_SESSIONS,
                folds: Sequence[Fold] = FOLDS) -> tuple[DecisionSlot, ...]:
    """All anchored-clock ticks through the last fold end (filled or voided).

    Tick ``k`` sits at master index ``anchor_index + period*k``.  A tick whose
    session has no next master session cannot fill and is refused (fail-closed)
    rather than silently re-timed.
    """
    dates_t = validate_master_dates(dates)
    a = anchor_index(dates_t, anchor_session)
    last_fold_end = folds[-1].end
    slots: list[DecisionSlot] = []
    k = 0
    while True:
        i = a + period * k
        if i >= len(dates_t) or dates_t[i] > last_fold_end:
            break
        session = dates_t[i]
        fill = dates_t[i + 1] if i + 1 < len(dates_t) else None
        if fill is None:
            raise ScheduleError(
                f"clock tick k={k} at {session!r} has no next allowed session "
                "on the master calendar; refusing to re-time"
            )
        slots.append(DecisionSlot(k=k, session=session, index=i,
                                  fold_id=_fold_of(session, folds),
                                  fill_session=fill))
        k += 1
    if not slots:
        raise ScheduleError("no clock ticks before the last fold end")
    return tuple(slots)


def _force_flats(dates: Sequence[str],
                 folds: Sequence[Fold] = FOLDS) -> tuple[ForceFlat, ...]:
    """Force-flat fill at every fold end session (fail-closed if absent)."""
    dates_t = validate_master_dates(dates)
    out = []
    for fold in folds:
        if fold.end not in dates_t:
            raise ScheduleError(
                f"fold {fold.fold_id} end {fold.end!r} is not a master session; "
                "the force-flat boundary cannot be placed"
            )
        out.append(ForceFlat(fold.fold_id, fold.end))
    return tuple(out)


def _assemble(arm: ArmConfig, dates: Sequence[str],
              slots: Sequence[DecisionSlot],
              flats: Sequence[ForceFlat],
              folds: Sequence[Fold] = FOLDS) -> ArmSchedule:
    """Shared validation + payload assembly for both generation paths."""
    dates_t = validate_master_dates(dates)
    decided = tuple(s for s in slots if s.fold_id is not None)
    voided = tuple(s for s in slots if s.fold_id is None)
    # every decided slot: fill strictly inside the same fold, never the same
    # session, and never colliding with a fold-end force-flat
    flat_sessions = {f.session for f in flats}
    fold_spans = {f.fold_id: (f.start, f.end) for f in folds}
    for s in decided:
        start, end = fold_spans[s.fold_id]
        if not (start <= s.session <= end):
            raise ScheduleError(
                f"decision {s.session!r} assigned to {s.fold_id} outside its span"
            )
        if not (start <= s.fill_session <= end):
            raise ScheduleError(
                f"decision {s.session!r} fill {s.fill_session!r} escapes fold "
                f"{s.fold_id} span [{start}, {end}]"
            )
        if s.fill_session == s.session:
            raise ScheduleError(f"same-session fill at {s.session!r}")
        if s.fill_session in flat_sessions:
            raise ScheduleError(
                f"decision fill {s.fill_session!r} collides with a fold-end "
                "force-flat"
            )
    # force-flat must sit strictly after every fill session of its fold
    for flat in flats:
        fold_fills = [s.fill_session for s in decided if s.fold_id == flat.fold_id]
        if any(f >= flat.session for f in fold_fills):
            raise ScheduleError(
                f"force-flat {flat.session!r} not after all {flat.fold_id} fills"
            )
    return ArmSchedule(
        arm_id=arm.arm_id,
        arm_key=arm.arm_key,
        role=arm.role,
        config_digest=arm.digest,
        decisions=tuple(slots),
        voided=voided,
        force_flats=tuple(flats),
        master_sessions_total=len(dates_t),
        master_first=dates_t[0],
        master_last=dates_t[-1],
        anchor_index_value=anchor_index(dates_t),
    )


def build_arm_schedule_walk(arm: ArmConfig, dates: Sequence[str],
                            folds: Sequence[Fold] = FOLDS) -> ArmSchedule:
    """Path 1 — sequential clock walk (see module docstring)."""
    validate_master_dates(dates)
    slots = clock_slots(dates, folds=folds)
    flats = _force_flats(dates, folds)
    return _assemble(arm, dates, slots, flats, folds)


def build_arm_schedule_blockwise(arm: ArmConfig, dates: Sequence[str],
                                 folds: Sequence[Fold] = FOLDS) -> ArmSchedule:
    """Path 2 — fold blocks first, then merge (see module docstring).

    Groups the anchored ticks per fold in frozen FOLDS order, computes the
    fold force-flats, and concatenates the per-fold slot blocks.  MUST agree
    byte-identically with :func:`build_arm_schedule_walk` (pinned by tests).
    """
    validate_master_dates(dates)
    slots = clock_slots(dates, folds=folds)
    flats = _force_flats(dates, folds)
    by_fold: dict[str, list[DecisionSlot]] = {f.fold_id: [] for f in folds}
    ordered: list[DecisionSlot] = []
    voided: list[DecisionSlot] = []
    for s in slots:
        if s.fold_id is None:
            voided.append(s)
        else:
            by_fold[s.fold_id].append(s)
    for fold in folds:  # frozen fold order == k order on the anchored clock
        ordered.extend(by_fold[fold.fold_id])
    return _assemble(arm, dates, ordered + voided, flats, folds)


def schedules_equal(a: ArmSchedule, b: ArmSchedule) -> bool:
    """Byte-level equality of two schedules' canonical JSON payloads."""
    return a.canonical_json() == b.canonical_json()


# --------------------------------------------------------------------------- #
# schedule-only feasibility (dates/counts/universe — no PnL, no feature values)
# --------------------------------------------------------------------------- #
def schedule_feasibility(arm: ArmConfig, schedule: ArmSchedule,
                         dates: Sequence[str],
                         presence: Mapping[str, Any],
                         warmup: int = WARMUP_SESSIONS,
                         folds: Sequence[Fold] = FOLDS) -> dict[str, Any]:
    """Schedule-only feasibility of one arm on the real snapshot.

    Checks dates/counts/universe ONLY: per-fold decision counts and dates,
    next-allowed-session fills, fold-span containment, force-flat placement,
    voided ticks, and the eligible rank-set size at every decision (presence
    of data — never feature values, never returns, never PnL).
    """
    dates_t = validate_master_dates(dates)
    decided = schedule.decided
    per_fold: dict[str, Any] = {}
    for fold in folds:
        slots = schedule.decisions_in_fold(fold.fold_id)
        per_fold[fold.fold_id] = {
            "span": [fold.start, fold.end],
            "decision_count": len(slots),
            "decision_sessions": [s.session for s in slots],
            "fill_sessions": [s.fill_session for s in slots],
            "eligible_rank_set_sizes": [
                len(eligibility(dates_t, s.index, presence, warmup))
                for s in slots
            ],
        }
    flat_sessions = {f.session for f in schedule.force_flats}
    checks = {
        "all_decision_sessions_on_master_calendar": all(
            s.session in set(dates_t) for s in decided),
        "all_fills_next_allowed_session": all(
            dates_t[s.index + 1] == s.fill_session for s in decided),
        "no_same_session_fill": all(
            s.fill_session != s.session for s in decided),
        "all_decisions_inside_fold_spans": all(
            s.fold_id is not None for s in schedule.decisions),
        "force_flat_at_every_fold_end": all(
            ForceFlat(f.fold_id, f.end) in schedule.force_flats for f in folds),
        "no_fill_collides_with_force_flat": all(
            s.fill_session not in flat_sessions for s in decided),
        "zero_voided_ticks": len(schedule.voided) == 0,
        "meets_fold_floor_ge_5": all(
            len(schedule.decisions_in_fold(f.fold_id)) >= 5 for f in folds),
        "meets_total_floor_ge_30": len(decided) >= 30,
        "rank_set_never_below_minimum": all(
            n >= arm.min_rank_set
            for fold_id in per_fold
            for n in per_fold[fold_id]["eligible_rank_set_sizes"]),
        "double_generation_byte_identical": schedules_equal(
            build_arm_schedule_walk(arm, dates_t, folds),
            build_arm_schedule_blockwise(arm, dates_t, folds)),
        "cash_never_a_symbol": CASH_SYMBOL not in arm.symbols,
    }
    return {
        "schema": FAMILY_SCHEMA,
        "feasibility": "SCHEDULE_ONLY_NO_PNL_NO_REAL_FEATURE_VALUES",
        "family_id": FAMILY_ID,
        "arm_id": arm.arm_id,
        "arm_key": arm.arm_key,
        "config_digest": arm.digest,
        "schedule_digest": schedule.schedule_digest,
        "master_calendar": {
            "sessions_total": schedule.master_sessions_total,
            "first": schedule.master_first,
            "last": schedule.master_last,
            "anchor_session": ANCHOR_SESSION,
            "anchor_index": schedule.anchor_index_value,
        },
        "decisions_total": len(decided),
        "folds": per_fold,
        "force_flats": [f.to_payload() for f in schedule.force_flats],
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


__all__ = [
    "ArmSchedule",
    "DecisionSlot",
    "ForceFlat",
    "ScheduleError",
    "anchor_index",
    "build_arm_schedule_blockwise",
    "build_arm_schedule_walk",
    "clock_slots",
    "schedule_feasibility",
    "schedules_equal",
    "validate_master_dates",
]
