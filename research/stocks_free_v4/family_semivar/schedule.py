"""Deterministic schedules for family SFV4-A4-H1-SEMIVARIANCE-SHARE (A9).

Owner: lane A9, STOCKS-FREE-V4 family 2.  Implements the frozen schedule
surface from ``research/control/stocks_free_v4_run/selection_freeze.json``
(families[1] conditions), ``research/control/stocks_free_v4_run/proposals/
a4_h1.json`` (universe_and_schedule) and
``research/control/stocks_free_v4_run/baseline_invariants.json``.  This
module is SCHEDULE ONLY on real data: deterministic calendar arithmetic and
target-book emission from ALREADY-COMPUTED signals — it never computes a
return, a feature, or any PnL from real prices.  Signals enter only through
caller-supplied rank lists (synthetic tests) or not at all (the real-data
feasibility path carries dates and counts ONLY).

Frozen schedule mechanics:

* Decision clock (byte-exact pin): a GLOBAL session-count clock anchored to
  the S0 start ``2018-04-04`` — a session at global SPY-calendar index ``i``
  is a decision session iff ``(i - anchor_index) % 21 == 0``.  No calendar
  (month/day) dependence.  Decisions inside a fold are the global clock
  ticks that fall inside that fold's window; the automaton RE-SEEDS with the
  seed rule at the first tick of each fold and the book is FORCE-FLAT at
  every fold boundary (boundary sessions carry no cross-fold carry; the gap
  sessions between folds are not scored and the book stays flat across
  them).

* PIT fill clock: the signal is computed on the decision session's
  COMPLETED data; the fill happens at the NEXT allowed session (the next
  session of the shared calendar) — never a same-session fill.  A fill is
  emitted ONLY when the target book differs from the current book (static
  weights between decisions; hysteresis keeps most ticks fill-free).

* Books: +0.25 per LONG leg, -0.25 per SHORT leg, CASH absorbs the residual
  and is never a symbol.  ``entry_type == "FORCE_FLAT"`` marks the fold-end
  liquidation events (all-CASH book).

Two independent generation paths are provided and must agree BYTE-IDENTICALLY
(canonical JSON), pinned by tests:

* :func:`build_arm_schedule` — global session walk: one pass over the full
  session list, ticks discovered while walking, fills appended as the book
  changes, force-flat events appended at fold ends;
* :func:`build_arm_schedule_by_folds` — fold-sliced: per fold, the tick list
  is computed independently (by index arithmetic), books are rebuilt from
  the seed rule, and the fold payloads are concatenated.

:func:`schedule_only_feasibility` is the REAL-DATA entry point: it consumes
ISO session lists (dates) and per-symbol session history (dates) and returns
dates and counts ONLY — no returns, no features, no PnL, ever.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.assets.common.contracts import canonical_json
from research.assets.stocks.factory import CASH_SYMBOL, etf_leg_turnover
from research.stocks_free_v4.family_semivar.config import (
    CLOCK_ANCHOR_SESSION,
    CLOCK_STEP_SESSIONS,
    FAMILY_ID,
    FAMILY_SCHEMA,
    FOLDS,
    S0_END,
    ArmConfig,
    ArmConfigError,
)
from research.stocks_free_v4.family_semivar.signals import (
    eligibility,
    feature_value,
    rank_symbols,
    seed_book,
    step_book,
    target_weights,
)

#: The implicit book before the first fill of a fold is all-CASH.
INITIAL_WEIGHTS: Mapping[str, float] = {CASH_SYMBOL: 1.0}

_ALL_CASH_TARGETS: Mapping[str, float] = {CASH_SYMBOL: 1.0}


class ScheduleError(ValueError):
    """Raised when a schedule cannot be built from the declared sessions."""


# --------------------------------------------------------------------------- #
# anchored 21-session decision clock (byte-exact pin)
# --------------------------------------------------------------------------- #
def _require_sessions(sessions: Sequence[str]) -> None:
    if not sessions:
        raise ScheduleError("sessions must be a non-empty ascending ISO list")
    if list(sessions) != sorted(set(sessions)):
        raise ScheduleError("sessions must be sorted ascending and unique")
    for s in sessions:
        if not isinstance(s, str) or len(s) != 10 or s[4] != s[7] != "-":
            raise ScheduleError(f"non-ISO session string: {s!r}")


def clock_anchor_index(sessions: Sequence[str]) -> int:
    """Index of the byte-exact clock anchor ``2018-04-04`` in the calendar.

    Fail-closed: the anchor must BE a session of the declared calendar — the
    frozen pin is meaningless on a calendar that does not contain it.
    """
    try:
        return list(sessions).index(CLOCK_ANCHOR_SESSION)
    except ValueError:
        raise ScheduleError(
            f"clock anchor {CLOCK_ANCHOR_SESSION} is not a session of the "
            "declared calendar; the byte-exact pin cannot be applied"
        ) from None


def decision_indices(sessions: Sequence[str]) -> tuple[int, ...]:
    """Indices of decision sessions under the anchored global clock.

    ``i`` is a decision index iff ``i >= anchor_index`` and
    ``(i - anchor_index) % CLOCK_STEP == 0``.
    """
    _require_sessions(sessions)
    a = clock_anchor_index(sessions)
    return tuple(range(a, len(sessions), CLOCK_STEP_SESSIONS))


def fold_of(session: str) -> str | None:
    """The fold id owning ``session``, or None outside every fold."""
    for fold_id, start, end in FOLDS:
        if start <= session <= end:
            return fold_id
    return None


def fold_sessions(sessions: Sequence[str], fold_id: str) -> tuple[str, ...]:
    """Sessions of the shared calendar inside one frozen fold."""
    for fid, start, end in FOLDS:
        if fid == fold_id:
            return tuple(s for s in sessions if start <= s <= end)
    raise ScheduleError(f"unknown fold {fold_id!r}")


def next_session(sessions: Sequence[str], session: str) -> str:
    """The next allowed session strictly after ``session`` (fill clock)."""
    _require_sessions(sessions)
    for s in sessions:
        if s > session:
            return s
    raise ScheduleError(
        f"no session after {session!r}: the fill clock never fills beyond "
        "the declared calendar (a decision on the last session is a "
        "configuration error)"
    )


# --------------------------------------------------------------------------- #
# scheduled fills
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ScheduledFill:
    """One scheduled fill event.

    ``decision_session`` is the completed session whose data determined the
    book; ``fill_session`` is the NEXT allowed session (never the same
    session).  ``book_kind`` is ``"SEED"`` (fold-start seed), ``"REBAL"`` (a
    hysteresis book change), or ``"FORCE_FLAT"`` (fold-end liquidation,
    all-CASH).  ``turnover_one_way`` is the schedule-only one-way turnover
    of the pure target books (non-CASH legs only).
    """

    fill_session: str
    decision_session: str | None
    book_kind: str
    targets: Mapping[str, float]
    turnover_one_way: float
    fold_id: str

    @property
    def establishment(self) -> bool:
        return self.book_kind == "SEED"

    def to_payload(self) -> dict[str, Any]:
        return {
            "fill_session": self.fill_session,
            "decision_session": self.decision_session,
            "book_kind": self.book_kind,
            "targets": {s: self.targets[s] for s in sorted(self.targets)},
            "turnover_one_way": self.turnover_one_way,
            "fold_id": self.fold_id,
        }


@dataclass(frozen=True)
class ArmSchedule:
    """One arm's deterministic schedule over the declared sessions."""

    arm_id: str
    arm_key: str
    config_digest: str
    sessions: tuple[str, ...]
    decision_sessions: tuple[str, ...]
    folds: tuple[str, ...]
    fills: tuple[ScheduledFill, ...]

    @property
    def transitions(self) -> tuple[ScheduledFill, ...]:
        """All fills except the per-fold seed fills."""
        return tuple(f for f in self.fills if not f.establishment)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": FAMILY_SCHEMA,
            "family_id": FAMILY_ID,
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "config_digest": self.config_digest,
            "sessions": list(self.sessions),
            "decision_sessions": list(self.decision_sessions),
            "folds": list(self.folds),
            "fills": [f.to_payload() for f in self.fills],
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())

    @property
    def schedule_digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def schedules_equal(a: ArmSchedule, b: ArmSchedule) -> bool:
    """Byte-level equality of two schedules' canonical JSON payloads."""
    return a.canonical_json() == b.canonical_json()


# --------------------------------------------------------------------------- #
# books from ranks (signals enter ONLY here, from caller-supplied ranks)
# --------------------------------------------------------------------------- #
def _fold_tick_books(cfg: ArmConfig, ranks_by_tick: Sequence[Sequence[str]]) -> list[dict[str, str]]:
    """Book states for one fold's tick sequence under the frozen automaton.

    The automaton RE-SEEDS at the fold's first tick (seed rule) and applies
    the hysteresis transition at every subsequent tick.
    """
    books: list[dict[str, str]] = []
    state: dict[str, str] | None = None
    for ranks in ranks_by_tick:
        if state is None:
            state = seed_book(ranks)
        else:
            state = step_book(state, ranks)
        books.append(state)
    return books


def _tick_ranks(cfg: ArmConfig, history: Mapping[str, Sequence[float]],
                decision_session: str,
                eligible: Sequence[str] | None = None) -> tuple[str, ...]:
    """Ranks at one decision session from caller-supplied trailing windows.

    ``history[s]`` is the symbol's trailing ``state_window`` return window
    ENDING at the decision session (the CALLER owns the PIT windowing — this
    module never touches price data).  Ineligible symbols are absent from
    ``history`` (held FLAT by the availability rule).
    """
    feats: dict[str, float] = {}
    for s in (eligible if eligible is not None else history):
        win = history.get(s)
        if win is None or len(win) != cfg.state_window_sessions:
            raise ScheduleError(
                f"{s!r} trailing window at {decision_session} must hold "
                f"exactly {cfg.state_window_sessions} completed returns, got "
                f"{None if win is None else len(win)}"
            )
        feats[s] = feature_value(win, cfg.sort_statistic)
    if len(feats) < 8:
        raise ScheduleError(
            f"only {len(feats)} eligible sectors at {decision_session}; the "
            "4/4 book cannot be formed (fail closed)"
        )
    return rank_symbols(feats)


def _fills_for_fold(cfg: ArmConfig, sessions: Sequence[str],
                    fold_id: str, ranks_by_tick: Sequence[Sequence[str]],
                    tick_sessions: Sequence[str]) -> list[ScheduledFill]:
    """Fills of one fold: seed, changes-only rebalances, and the force-flat.

    The decision at tick t fills at the next allowed session; a rebalance
    fill is emitted ONLY when the target book differs from the current book
    (static weights between decisions).  The fold-end FORCE_FLAT closes the
    book at the fold's last session.
    """
    fold_cal = fold_sessions(sessions, fold_id)
    if not fold_cal:
        raise ScheduleError(f"fold {fold_id!r} has no sessions in the calendar")
    books = _fold_tick_books(cfg, ranks_by_tick)
    fills: list[ScheduledFill] = []
    current: Mapping[str, float] = INITIAL_WEIGHTS
    fold_set = set(fold_cal)
    for ranks, dec in zip(books, tick_sessions):
        if dec not in fold_set:
            raise ScheduleError(f"decision {dec!r} outside fold {fold_id!r}")
        fill_session = next_session(sessions, dec)
        if fill_session > fold_cal[-1]:
            raise ScheduleError(
                f"decision {dec!r} fills at {fill_session!r} beyond fold "
                f"{fold_id!r} end {fold_cal[-1]!r}; the frozen clock never "
                "crosses a fold boundary"
            )
        targets = target_weights(ranks, cfg.leg_weight)
        if not fills or _differs(current, targets):
            kind = "SEED" if not fills else "REBAL"
            fills.append(ScheduledFill(
                fill_session=fill_session,
                decision_session=dec,
                book_kind=kind,
                targets=targets,
                turnover_one_way=etf_leg_turnover(current, targets),
                fold_id=fold_id,
            ))
            current = targets
    # force-flat at the fold boundary (all-CASH; non-CASH turnover is the
    # sum of leg liquidations, CASH excluded per the frozen convention).
    end_session = fold_cal[-1]
    fills.append(ScheduledFill(
        fill_session=end_session,
        decision_session=None,
        book_kind="FORCE_FLAT",
        targets=dict(_ALL_CASH_TARGETS),
        turnover_one_way=etf_leg_turnover(current, _ALL_CASH_TARGETS),
        fold_id=fold_id,
    ))
    return fills


def _differs(a: Mapping[str, float], b: Mapping[str, float]) -> bool:
    """Book inequality over non-CASH legs (CASH is the residual, derived)."""
    legs = (set(a) | set(b)) - {CASH_SYMBOL}
    return any(
        abs(float(a.get(s, 0.0)) - float(b.get(s, 0.0))) > 1e-12 for s in legs
    )


def build_arm_schedule(cfg: ArmConfig, sessions: Sequence[str],
                       history_by_tick: Sequence[tuple[str, Mapping[str, Sequence[float]]]],
                       ) -> ArmSchedule:
    """Path 1 — global session walk (one pass over the whole calendar).

    ``history_by_tick`` pairs every decision session with each symbol's
    trailing completed-return window (length = the arm's state window)
    ENDING at that decision session; symbols without full history are simply
    absent (the XLC availability rule holds them FLAT).  Ticks are the
    anchored global clock's sessions inside the frozen folds.
    """
    if cfg.arm_key not in ("A", "N", "C"):
        raise ArmConfigError(f"unknown arm key {cfg.arm_key!r}")
    _require_sessions(sessions)
    ticks = [s for s in decision_indices(sessions) if fold_of(sessions[s]) is not None]
    tick_sessions = [sessions[i] for i in ticks]
    by_tick = _align_history(tick_sessions, history_by_tick)
    fills: list[ScheduledFill] = []
    for fold_id, start, end in FOLDS:
        idxs = [i for i, s in enumerate(tick_sessions) if start <= s <= end]
        ranks = [_tick_ranks(cfg, by_tick[tick_sessions[i]], tick_sessions[i])
                 for i in idxs]
        fills.extend(_fills_for_fold(
            cfg, sessions, fold_id,
            [list(r) for r in ranks],
            [tick_sessions[i] for i in idxs],
        ))
    return ArmSchedule(
        arm_id=cfg.arm_id,
        arm_key=cfg.arm_key,
        config_digest=cfg.digest,
        sessions=tuple(sessions),
        decision_sessions=tuple(tick_sessions),
        folds=tuple(f[0] for f in FOLDS),
        fills=tuple(fills),
    )


def _align_history(tick_sessions: Sequence[str],
                   history_by_tick: Sequence[tuple[str, Mapping[str, Sequence[float]]]],
                   ) -> dict[str, Mapping[str, Sequence[float]]]:
    """Decision session -> history map, fail-closed on duplicates/mismatch."""
    wanted = set(tick_sessions)
    provided = [d for d, _ in history_by_tick]
    if len(set(provided)) != len(provided):
        raise ScheduleError("duplicate decision sessions in history_by_tick")
    mapping = dict(history_by_tick)
    missing = sorted(wanted - set(provided))
    if missing:
        raise ScheduleError(
            f"missing trailing history for decision sessions (first 5): {missing}"
        )
    return mapping


def build_arm_schedule_by_folds(
    cfg: ArmConfig, sessions: Sequence[str],
    history_by_tick: Sequence[tuple[str, Mapping[str, Sequence[float]]]],
) -> ArmSchedule:
    """Path 2 — fold-sliced construction (MUST match path 1 byte-identically).

    Independently re-derives each fold's decision list from the anchored
    clock by index arithmetic restricted to the fold window, rebuilds the
    books from the seed rule inside the fold, and concatenates the per-fold
    fill payloads.  Deliberately a different traversal from the global walk
    so that the byte-equality check is a genuine double generation.
    """
    if cfg.arm_key not in ("A", "N", "C"):
        raise ArmConfigError(f"unknown arm key {cfg.arm_key!r}")
    _require_sessions(sessions)
    anchor = clock_anchor_index(sessions)
    all_ticks = [sessions[i] for i in range(anchor, len(sessions),
                                            CLOCK_STEP_SESSIONS)]
    in_fold_ticks = [s for s in all_ticks if fold_of(s) is not None]
    by_tick = _align_history(in_fold_ticks, history_by_tick)
    fills: list[ScheduledFill] = []
    tick_sessions: list[str] = []
    for fold_id, start, end in FOLDS:
        fold_idx = [
            i for i in range(anchor, len(sessions), CLOCK_STEP_SESSIONS)
            if start <= sessions[i] <= end
        ]
        fold_tick_sessions = [sessions[i] for i in fold_idx]
        tick_sessions.extend(fold_tick_sessions)
        ranks_by_tick = [
            list(_tick_ranks(cfg, by_tick[sessions[i]], sessions[i]))
            for i in fold_idx
        ]
        fills.extend(_fills_for_fold(
            cfg, sessions, fold_id, ranks_by_tick, fold_tick_sessions
        ))
    return ArmSchedule(
        arm_id=cfg.arm_id,
        arm_key=cfg.arm_key,
        config_digest=cfg.digest,
        sessions=tuple(sessions),
        decision_sessions=tuple(tick_sessions),
        folds=tuple(f[0] for f in FOLDS),
        fills=tuple(fills),
    )


# --------------------------------------------------------------------------- #
# schedule-only feasibility (REAL DATA: dates and counts ONLY, no returns)
# --------------------------------------------------------------------------- #
def schedule_only_feasibility(
    sessions: Sequence[str],
    symbol_sessions: Mapping[str, Sequence[str]],
    state_window_by_arm: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Real-calendar feasibility: DATES AND COUNTS ONLY — NO returns, NO PnL.

    ``sessions`` is the real SPY session calendar (ISO strings, ascending,
    S0-bounded by the caller); ``symbol_sessions`` maps each of the 11 sector
    symbols to its OWN authorized session dates (ascending).  Reports per arm
    and per fold: session counts, the anchored decision sessions, the next-
    session fills, per-tick eligibility counts under the symbol's own
    availability rule (a COUNT check on dates, never a return), the
    warmup-availability verdict (the full state window of history exists for
    every eligible symbol at every tick), and the force-flat boundary dates.
    """
    _require_sessions(sessions)
    from research.stocks_free_v4.family_semivar.config import (
        STATE_WINDOW_ANCHOR, STATE_WINDOW_CONTROL, STATE_WINDOW_NEIGHBOUR,
        build_arm_configs,
    )
    windows = state_window_by_arm or {
        "A": STATE_WINDOW_ANCHOR, "N": STATE_WINDOW_NEIGHBOUR,
        "C": STATE_WINDOW_CONTROL,
    }
    anchor = clock_anchor_index(sessions)
    tick_idx_all = list(range(anchor, len(sessions), CLOCK_STEP_SESSIONS))
    arms: dict[str, Any] = {}
    for key in ("A", "N", "C"):
        cfg = build_arm_configs()[key]
        window = windows[key]
        per_fold: dict[str, Any] = {}
        all_ticks: list[str] = []
        min_eligible = None
        warmup_ok = True
        first_eligible_full: str | None = None
        for fold_id, start, end in FOLDS:
            idxs = [i for i in tick_idx_all if start <= sessions[i] <= end]
            ticks = [sessions[i] for i in idxs]
            all_ticks.extend(ticks)
            fills = [next_session(sessions, t) for t in ticks]
            elig_counts = []
            thin: list[str] = []
            for t in ticks:
                elig = eligibility(symbol_sessions, t, window,
                                   cfg.symbols)
                elig_counts.append(len(elig))
                if len(elig) < 8:
                    thin.append(t)
                    warmup_ok = False
                if min_eligible is None or len(elig) < min_eligible:
                    min_eligible = len(elig)
                if first_eligible_full is None and len(elig) == len(cfg.symbols):
                    first_eligible_full = t
            per_fold[fold_id] = {
                "fold_start": start,
                "fold_end": end,
                "n_sessions": sum(1 for s in sessions if start <= s <= end),
                "n_decisions": len(ticks),
                "first_decision": ticks[0] if ticks else None,
                "last_decision": ticks[-1] if ticks else None,
                "first_fill": fills[0] if fills else None,
                "last_fill": fills[-1] if fills else None,
                "decision_sessions": ticks,
                "fill_sessions": fills,
                "eligible_count_per_tick": elig_counts,
                "ticks_below_full_book": thin,
                "force_flat_session": end,
                "decisions_per_fold_floor_ok": len(ticks) >= 5,
            }
        arms[key] = {
            "arm_id": cfg.arm_id,
            "config_digest": cfg.digest,
            "state_window_sessions": window,
            "n_decisions_total": len(all_ticks),
            "decisions_total_floor_ok": len(all_ticks) >= 30,
            "min_eligible_sectors_at_any_tick": min_eligible,
            "warmup_available_at_every_tick": warmup_ok,
            "first_tick_full_universe": first_eligible_full,
            "folds": per_fold,
        }
    return {
        "schema": FAMILY_SCHEMA,
        "feasibility": "SCHEDULE_ONLY_DATES_AND_COUNTS_NO_RETURNS_NO_PNL",
        "clock": {
            "step_sessions": CLOCK_STEP_SESSIONS,
            "anchor_session": CLOCK_ANCHOR_SESSION,
            "anchor_index_in_calendar": anchor,
            "n_calendar_sessions": len(sessions),
            "calendar_first": sessions[0],
            "calendar_last": sessions[-1],
        },
        "folds": {fid: {"start": s, "end": e} for fid, s, e in FOLDS},
        "arms": arms,
    }


__all__ = [
    "INITIAL_WEIGHTS",
    "ArmSchedule",
    "ScheduleError",
    "ScheduledFill",
    "build_arm_schedule",
    "build_arm_schedule_by_folds",
    "clock_anchor_index",
    "decision_indices",
    "fold_of",
    "fold_sessions",
    "next_session",
    "schedule_only_feasibility",
    "schedules_equal",
]
