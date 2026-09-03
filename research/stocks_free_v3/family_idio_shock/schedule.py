"""Trigger / selection / budget / concurrency state machine and the canonical
target-weight schedule for SFV3-A5-IDIO-SHOCK-REVERSAL (schedule-only).

Frozen clocks (ADJ-1-EXEC-CLOCK): the decision pass runs once per completed
session ``t`` at its CLOSE, on features through ``t`` only; a committed
episode FILLS at the CLOSE of session ``t+1``; the hold is close-to-close
(exit fill at the close of ``entry + hold_sessions``); a trigger at close of
``t`` may enter at the close of ``t+1`` when that episode's exit also lands
there (same-close switch — both orders were decided at earlier closes, so it
is PIT-clean).

Emitted schedule: an ascending list of records ::

    {"entry_type": "FILL" | "FORCE_FLAT",
     "fill_date": str,
     "targets": {..., "CASH": w},          # explicit CASH leg, always present
     "cash_weight": float,
     "turnover_one_way": float,            # net ETF-leg one-way turnover
     "kind": "ENTRY" | "EXIT" | "SWITCH" | "WINDOW_END_FLAT",
     "decision_date": str, "symbol": str | None, "z_at_decision": float | None,
     "episode": int | None}

— the exact shape ``research.assets.stocks.factory.value_book`` and the V2
harness consume (they ignore the diagnostic fields).  When an exit and a new
entry land on the SAME fill session they merge into ONE record carrying the
final targets and the NET ETF-leg turnover (identical to the single fill
``value_book`` charges for that date; a same-close switch between different
symbols therefore books both legs = 1.0, a same-symbol re-entry books 0.0).

SCHEDULE-ONLY: this module computes episodes, gross exposure and turnover
arithmetic — never PnL, expectancy, PF, Sharpe or drawdown.  A position whose
frozen exit fill session does not exist inside the session list (data-edge
truncation) is closed by a terminal ``FORCE_FLAT`` at the last session; the
hold rule itself is never altered.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Mapping, Sequence

from research.assets.common.contracts import canonical_json
from research.assets.stocks.factory import CASH_SYMBOL, etf_leg_turnover
from research.stocks_free_v3.family_idio_shock.arms import FrozenArmConfig
from research.stocks_free_v3.family_idio_shock.features import (
    FeatureFrame,
    compute_features,
)

SCHEDULE_SCHEMA = "stocks_free_v3/family_idio_shock/schedule@1"

KIND_ENTRY = "ENTRY"
KIND_EXIT = "EXIT"
KIND_SWITCH = "SWITCH"
KIND_WINDOW_END_FLAT = "WINDOW_END_FLAT"

#: Frozen ceiling (falsification rule 5): realized two-way turnover per year.
TURNOVER_CEILING_TWO_WAY_PER_YEAR = 6.0

#: Feasibility annualization convention: 252 sessions per year (the budget
#: window constant), so ``years = n_sessions / 252``.
SESSIONS_PER_YEAR = 252


class ScheduleError(ValueError):
    """Raised when a schedule would breach a frozen invariant (fail closed)."""


def entries_in_budget_window(entry_index: int, prior_entry_indices: Sequence[int],
                             window_sessions: int, max_entries: int) -> bool:
    """Rolling episode-budget gate (pure helper, unit-tested directly).

    The candidate entry at ``entry_index`` is a new entry inside the rolling
    ``window_sessions``-session window ``[entry_index - window_sessions + 1,
    entry_index]``.  Allowed iff the committed prior entries inside that
    window number at most ``max_entries - 1``.
    """
    lower = entry_index - window_sessions + 1
    prior = sum(1 for e in prior_entry_indices if lower <= e <= entry_index - 1)
    return prior + 1 <= max_entries


def _select_trigger(config: FrozenArmConfig,
                    z_row: Mapping[str, float | None]) -> tuple[str, float] | None:
    """Frozen selection among simultaneous triggers at one decision close.

    A1/N1: the smallest z; C1: the largest z; an exact tie breaks to the
    alphabetically first symbol.  ``None`` z values never trigger.
    """
    if config.selects_extreme_low:
        candidates = [(float(z), sym) for sym, z in z_row.items()
                      if z is not None and float(z) <= config.z_threshold]
        if not candidates:
            return None
        z, sym = min(candidates)  # smallest z, exact tie -> alphabetically first
        return sym, z
    candidates = [(float(z), sym) for sym, z in z_row.items()
                  if z is not None and float(z) >= config.z_threshold]
    if not candidates:
        return None
    best_z = max(z for z, _ in candidates)
    sym = min(s for z, s in candidates if z == best_z)  # tie -> alphabetically first
    return sym, best_z


def build_arm_schedule_from_features(
    config: FrozenArmConfig,
    sessions: Sequence[str],
    features: FeatureFrame,
) -> ScheduleResult:
    """Run the frozen state machine from a precomputed :class:`FeatureFrame`.

    This is one of the two equal code paths used for the double-generation
    equality test (the other regenerates features from raw returns).
    """
    sessions = list(sessions)
    n = len(sessions)
    last_index = n - 1

    # pending events: (fill_index, seq, kind, symbol, decision_date, z_at_decision)
    events: list[tuple[int, int, str, str | None, str | None, float | None]] = []
    open_exit_index: int | None = None
    open_symbol: str | None = None
    entry_indices: list[int] = []
    n_triggers = n_entries = n_switches = n_budget_rej = n_conc_blocks = 0
    n_decision_sessions = 0

    for d, session in enumerate(sessions):
        z_row = features.z.get(session)
        if z_row is None:
            continue  # warmup session: no feature, no decision pass
        n_decision_sessions += 1
        if d + 1 > last_index:
            continue  # no t+1 session exists to fill on (data-edge truncation)
        selection = _select_trigger(config, z_row)
        if selection is None:
            continue
        n_triggers += 1
        symbol, z_value = selection
        fill_index = d + 1
        # concurrency 1 with the ADJ-1 same-close switch allowance: a fill is
        # blocked only when an open episode's exit lands STRICTLY later.
        if open_exit_index is not None and open_exit_index > fill_index:
            n_conc_blocks += 1
            continue
        # rolling episode budget, counted by entry (fill) session
        if not entries_in_budget_window(
            fill_index, entry_indices,
            config.episode_budget_window_sessions, config.episode_budget_max_entries,
        ):
            n_budget_rej += 1
            continue
        is_switch = open_exit_index is not None and open_exit_index == fill_index
        if is_switch:
            # the old episode's EXIT event was already scheduled at this fill
            # session when it was committed (seq 0); the new entry joins it as
            # seq 1 so the pair merges into one SWITCH record below.
            n_switches += 1
        events.append((fill_index, 1 if is_switch else 0, KIND_ENTRY,
                       symbol, session, z_value))
        entry_indices.append(fill_index)
        n_entries += 1
        open_symbol = symbol
        exit_index = fill_index + config.hold_sessions
        if exit_index <= last_index:
            open_exit_index = exit_index
            events.append((exit_index, 0, KIND_EXIT, symbol, session, None))
        else:
            # data-edge truncation: the exit fill session does not exist; the
            # book is closed by a terminal FORCE_FLAT at the last session and
            # stays blocked until then (concurrency is preserved).
            open_exit_index = last_index
            events.append((last_index, 0, KIND_WINDOW_END_FLAT, symbol, session, None))

    events.sort(key=lambda e: (e[0], e[1]))

    # merge events landing on the same fill session into ONE canonical record
    records: list[dict] = []
    current: dict[str, float] = {CASH_SYMBOL: 1.0}
    episodes_held = 0
    episode_counter = 0
    i = 0
    while i < len(events):
        j = i
        group = []
        while j < len(events) and events[j][0] == events[i][0]:
            group.append(events[j])
            j += 1
        fill_index = events[i][0]
        kinds = [g[2] for g in group]
        targets: dict[str, float] = {CASH_SYMBOL: 1.0}
        for g in group:
            if g[2] == KIND_ENTRY:
                targets = {g[3]: config.gross, CASH_SYMBOL: config.cash_weight}
            else:
                targets = {CASH_SYMBOL: 1.0}
        holds = any(w != 0.0 for s, w in targets.items() if s != CASH_SYMBOL)
        if holds and KIND_ENTRY in kinds:
            kind = KIND_SWITCH if KIND_EXIT in kinds else KIND_ENTRY
        elif not holds and KIND_WINDOW_END_FLAT in kinds:
            # data-edge truncation (possibly merged with a same-session entry
            # that could never hold a session): the canonical record is the
            # FORCE_FLAT.
            kind = KIND_WINDOW_END_FLAT
        else:
            kind = KIND_EXIT
        decision_date = next((g[4] for g in reversed(group) if g[4] is not None), None)
        symbol = next((g[3] for g in reversed(group) if g[3] is not None), None)
        z_value = next((g[5] for g in reversed(group) if g[5] is not None), None)
        turnover = etf_leg_turnover(current, targets)
        holds = any(w != 0.0 for s, w in targets.items() if s != CASH_SYMBOL)
        if holds:
            episodes_held += 1
        if kind in (KIND_ENTRY, KIND_SWITCH):
            episode_counter += 1
        episode_field: int | None = None
        if kind in (KIND_ENTRY, KIND_SWITCH, KIND_EXIT) or (
                kind == KIND_WINDOW_END_FLAT and episode_counter > 0):
            # ENTRY/SWITCH open the episode; EXIT/WINDOW_END_FLAT close it.
            episode_field = episode_counter
        records.append({
            "entry_type": "FORCE_FLAT" if kind == KIND_WINDOW_END_FLAT else "FILL",
            "fill_date": sessions[fill_index],
            "targets": dict(targets),
            "cash_weight": float(targets[CASH_SYMBOL]),
            "turnover_one_way": turnover,
            "kind": kind,
            "decision_date": decision_date,
            "symbol": symbol,
            "z_at_decision": z_value,
            "episode": episode_field,
        })
        current = dict(targets)
        i = j

    _assert_schedule_invariants(config, records, entry_indices)

    schedule_digest = hashlib.sha256(canonical_json({
        "schema": SCHEDULE_SCHEMA,
        "arm_id": config.arm_id,
        "config_digest": config.config_digest,
        "records": records,
    }).encode("utf-8")).hexdigest()

    return ScheduleResult(
        arm_id=config.arm_id,
        config_digest=config.config_digest,
        schedule_digest=schedule_digest,
        records=tuple(records),
        n_decision_sessions=n_decision_sessions,
        n_triggers_observed=n_triggers,
        n_entries_committed=n_entries,
        n_episodes_held=episodes_held,
        n_same_close_switches=n_switches,
        n_budget_rejections=n_budget_rej,
        n_concurrency_blocks=n_conc_blocks,
    )


def build_arm_schedule(
    config: FrozenArmConfig,
    sessions: Sequence[str],
    returns: Mapping[str, Mapping[str, float]],
    benchmark_symbol: str | None = None,
) -> ScheduleResult:
    """Direct path: compute the frozen features from raw issuer-TR returns,
    then run the state machine (code path 1 of the double-generation check)."""
    frame = compute_features(
        sessions, returns, config.universe, benchmark_symbol or config.benchmark_symbol,
        lookback_sessions=config.beta_lookback_sessions,
    )
    return build_arm_schedule_from_features(config, sessions, frame)


@dataclass(frozen=True)
class ScheduleResult:
    """One arm's canonical target-weight schedule (no PnL anywhere)."""

    arm_id: str
    config_digest: str
    schedule_digest: str
    records: tuple[dict, ...]
    n_decision_sessions: int
    n_triggers_observed: int
    n_entries_committed: int
    n_episodes_held: int
    n_same_close_switches: int
    n_budget_rejections: int
    n_concurrency_blocks: int

    def to_payload(self) -> dict:
        return {
            "schema": SCHEDULE_SCHEMA,
            "arm_id": self.arm_id,
            "config_digest": self.config_digest,
            "schedule_digest": self.schedule_digest,
            "n_decision_sessions": self.n_decision_sessions,
            "n_triggers_observed": self.n_triggers_observed,
            "n_entries_committed": self.n_entries_committed,
            "n_episodes_held": self.n_episodes_held,
            "n_same_close_switches": self.n_same_close_switches,
            "n_budget_rejections": self.n_budget_rejections,
            "n_concurrency_blocks": self.n_concurrency_blocks,
        }


def _assert_schedule_invariants(config: FrozenArmConfig,
                                records: Sequence[Mapping[str, object]],
                                entry_indices: Sequence[int]) -> None:
    """Fail closed on any frozen-invariant breach in the emitted schedule."""
    seen_dates: list[str] = []
    for record in records:
        date = str(record["fill_date"])
        if seen_dates and date <= seen_dates[-1]:
            raise ScheduleError(f"schedule fill dates not strictly ascending at {date}")
        seen_dates.append(date)
        targets = dict(record["targets"])  # type: ignore[arg-type]
        etf_weight = sum(w for s, w in targets.items() if s != CASH_SYMBOL)
        cash = float(record["cash_weight"])  # type: ignore[arg-type]
        if abs(etf_weight + cash - 1.0) > 1e-9:
            raise ScheduleError(f"weights do not sum to 1.0 at {date}")
        if etf_weight > 1.0 + 1e-9:
            raise ScheduleError(f"gross exposure exceeds 1.0 at {date}")
        for s, w in targets.items():
            if s != CASH_SYMBOL and w != 0.0 and abs(w - config.gross) > 1e-9:
                raise ScheduleError(f"non-frozen ETF weight {w!r} for {s} at {date}")
        if float(record["turnover_one_way"]) < 0.0:  # type: ignore[arg-type]
            raise ScheduleError(f"negative turnover at {date}")
    # rolling episode budget over the committed entry sessions
    window = config.episode_budget_window_sessions
    max_entries = config.episode_budget_max_entries
    for e in entry_indices:
        in_window = sum(1 for x in entry_indices if e - window + 1 <= x <= e)
        if in_window > max_entries:
            raise ScheduleError(
                f"episode budget breached: {in_window} entries in the "
                f"{window}-session window ending at fill index {e}"
            )


@dataclass(frozen=True)
class ScheduleFeasibility:
    """Schedule-only feasibility of one arm (NO PnL, no scored metric)."""

    arm_id: str
    config_digest: str
    schedule_digest: str
    n_sessions: int
    n_decision_sessions: int
    n_triggers_observed: int
    n_entries_committed: int
    n_episodes_held: int
    n_same_close_switches: int
    n_budget_rejections: int
    n_concurrency_blocks: int
    n_fill_records: int
    n_window_end_flats: int
    years: float
    entries_per_year: float
    max_gross_observed: float
    gross_within_limit: bool
    turnover_one_way_total: float
    turnover_two_way_per_year: float
    turnover_ceiling_two_way_per_year: float
    within_turnover_ceiling: bool

    def to_payload(self) -> dict:
        return {
            "schema": "stocks_free_v3/family_idio_shock/feasibility@1",
            "arm_id": self.arm_id,
            "config_digest": self.config_digest,
            "schedule_digest": self.schedule_digest,
            "n_sessions": self.n_sessions,
            "n_decision_sessions": self.n_decision_sessions,
            "n_triggers_observed": self.n_triggers_observed,
            "n_entries_committed": self.n_entries_committed,
            "n_episodes_held": self.n_episodes_held,
            "n_same_close_switches": self.n_same_close_switches,
            "n_budget_rejections": self.n_budget_rejections,
            "n_concurrency_blocks": self.n_concurrency_blocks,
            "n_fill_records": self.n_fill_records,
            "n_window_end_flats": self.n_window_end_flats,
            "years": self.years,
            "entries_per_year": self.entries_per_year,
            "max_gross_observed": self.max_gross_observed,
            "gross_within_limit": self.gross_within_limit,
            "turnover_one_way_total": self.turnover_one_way_total,
            "turnover_two_way_per_year": self.turnover_two_way_per_year,
            "turnover_ceiling_two_way_per_year": self.turnover_ceiling_two_way_per_year,
            "within_turnover_ceiling": self.within_turnover_ceiling,
            "scored_metrics_computed": False,
        }


def schedule_feasibility(sessions: Sequence[str], result: ScheduleResult,
                         config: FrozenArmConfig) -> ScheduleFeasibility:
    """Schedule-only feasibility: entries/yr, gross check, turnover vs ceiling.

    ``turnover_two_way_per_year`` sums one-way ETF-leg turnover across ALL
    fills (purchases + sales, the freeze's conservative counting; CASH never
    counts) and annualizes by ``n_sessions / 252``.  No return of any kind is
    computed.
    """
    n_sessions = len(sessions)
    if n_sessions <= 0:
        raise ScheduleError("feasibility needs a non-empty session list")
    years = n_sessions / SESSIONS_PER_YEAR
    fills = [r for r in result.records if r["entry_type"] == "FILL"]
    flats = [r for r in result.records if r["entry_type"] == "FORCE_FLAT"]
    max_gross = max(
        (sum(w for s, w in r["targets"].items() if s != CASH_SYMBOL)
         for r in result.records),
        default=0.0,
    )
    turnover_total = sum(float(r["turnover_one_way"]) for r in result.records)
    two_way_per_year = turnover_total / years
    return ScheduleFeasibility(
        arm_id=result.arm_id,
        config_digest=result.config_digest,
        schedule_digest=result.schedule_digest,
        n_sessions=n_sessions,
        n_decision_sessions=result.n_decision_sessions,
        n_triggers_observed=result.n_triggers_observed,
        n_entries_committed=result.n_entries_committed,
        n_episodes_held=result.n_episodes_held,
        n_same_close_switches=result.n_same_close_switches,
        n_budget_rejections=result.n_budget_rejections,
        n_concurrency_blocks=result.n_concurrency_blocks,
        n_fill_records=len(fills),
        n_window_end_flats=len(flats),
        years=years,
        entries_per_year=result.n_entries_committed / years,
        max_gross_observed=max_gross,
        gross_within_limit=max_gross <= config.gross + 1e-9,
        turnover_one_way_total=turnover_total,
        turnover_two_way_per_year=two_way_per_year,
        turnover_ceiling_two_way_per_year=TURNOVER_CEILING_TWO_WAY_PER_YEAR,
        within_turnover_ceiling=two_way_per_year
        <= TURNOVER_CEILING_TWO_WAY_PER_YEAR + 1e-9,
    )


__all__ = [
    "KIND_ENTRY",
    "KIND_EXIT",
    "KIND_SWITCH",
    "KIND_WINDOW_END_FLAT",
    "SESSIONS_PER_YEAR",
    "SCHEDULE_SCHEMA",
    "ScheduleError",
    "ScheduleFeasibility",
    "ScheduleResult",
    "TURNOVER_CEILING_TWO_WAY_PER_YEAR",
    "build_arm_schedule",
    "build_arm_schedule_from_features",
    "entries_in_budget_window",
    "schedule_feasibility",
]
