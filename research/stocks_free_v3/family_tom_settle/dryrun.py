"""Exact-arm dry run: schedule + canonical accounting + publication gate.

Owner: lane A9, STOCKS-FREE-V3 family 2 (SFV3-A6-TOM-SETTLE).  One function,
:func:`run_exact_arm_dry_run`, exercises the EXACT frozen arm end-to-end
without ever computing, asserting on, or persisting a scored metric:

1. build the schedule twice via the two independent code paths and fail
   closed unless the two are byte-identical (double-generation equality);
2. convert the scheduled fills to canonical factory book entries (explicit
   CASH residual leg, matching ``cash_weight``) and value them through the
   ONE canonical accounting path :func:`research.assets.stocks.factory
   .value_book` (raw closes at fills, issuer distributions on ex-dates,
   official split factors; fill day earns no same-day return on the new
   weights; costs charged exactly once; CASH never in turnover);
3. assert the canonical books close (:func:`factory.assert_reconciles` —
   attribution identity at 1e-12 and cost accumulator equal to the fsum of
   per-fill costs);
4. drive the :class:`research.assets.stocks.factory.GatedTrialLedger`
   publication gate on the CALLER-SUPPLIED (temporary) ledger path: record
   the compute, gate-and-publish a SCHEDULE-ONLY artifact (counts, digests,
   turnover — never a scored number), then verify the idempotent replay is
   zero-delta.

The returned :class:`DryRunReport` carries ONLY schedule/structural facts and
boolean accounting outcomes.  Valuation-level numbers (equity, PnL, PF, MDD,
expectancy) are consumed internally by the reconciliation assert and are
deliberately NOT returned, NOT printed, and NOT persisted.  A dry run is not
a scored run: real-data callers must still keep every read inside S0 and
delete the temporary ledger afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.assets.stocks.factory import (
    CASH_SYMBOL,
    GatedTrialLedger,
    assert_reconciles,
    normalize_entry_targets,
    publication_metrics,
    value_book,
)
from research.stocks_free_v3.family_tom_settle.config import ArmConfig
from research.stocks_free_v3.family_tom_settle.schedule import (
    ArmSchedule,
    ScheduleError,
    build_schedule,
    build_schedule_from_windows,
    schedules_equal,
)


class DryRunError(ValueError):
    """Raised when the exact-arm dry run cannot proceed (fail closed)."""


@dataclass(frozen=True)
class DryRunReport:
    """Schedule-only dry-run facts — deliberately contains NO scored metric.

    ``valuation`` carries only booleans and counts proving the canonical
    accounting ran and closed; every numeric valuation output of
    ``factory.value_book`` is discarded inside :func:`run_exact_arm_dry_run`.
    """

    arm_id: str
    arm_key: str
    config_digest: str
    schedule_digest: str
    double_generation_identical: bool
    coverage_sessions: int
    window_sessions: int
    n_fills: int
    n_transitions: int
    establishment_fill_session: str
    transitions_turnover_one_way_total: float
    valuation: dict[str, Any]
    ledger: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": "stocks_free_v3/family_tom_settle_dry_run@1",
            "arm_id": self.arm_id,
            "arm_key": self.arm_key,
            "config_digest": self.config_digest,
            "schedule_digest": self.schedule_digest,
            "double_generation_identical": self.double_generation_identical,
            "coverage_sessions": self.coverage_sessions,
            "window_sessions": self.window_sessions,
            "n_fills": self.n_fills,
            "n_transitions": self.n_transitions,
            "establishment_fill_session": self.establishment_fill_session,
            "transitions_turnover_one_way_total": self.transitions_turnover_one_way_total,
            "valuation": dict(self.valuation),
            "ledger": dict(self.ledger),
            "scored_metric": "NONE_SCHEDULE_AND_VALUATION_ONLY",
        }


def schedule_book_entries(schedule: ArmSchedule) -> list[dict[str, Any]]:
    """Canonical factory book entries from a schedule (explicit CASH leg).

    Each entry carries the explicit ``"CASH"`` leg AND the equal
    ``cash_weight`` (factory ``normalize_entry_targets`` fails closed on any
    disagreement; equal values are the contract-true redundancy).  The
    schedule's ``turnover_one_way`` is informational only — the canonical
    factory recomputes turnover from realized weights at each fill.
    """
    entries: list[dict[str, Any]] = []
    for fill in schedule.fills:
        targets, cash = normalize_entry_targets(
            {
                "entry_type": "FILL",
                "fill_date": fill.fill_session,
                "targets": dict(fill.targets),
            }
        )
        expected_cash = fill.targets.get(CASH_SYMBOL)
        if expected_cash is None or abs(cash - expected_cash) > 1e-12:
            raise DryRunError(
                f"cash residual mismatch at {fill.fill_session}: "
                f"{cash!r} vs {expected_cash!r}"
            )
        entries.append(
            {
                "entry_type": "FILL",
                "fill_date": fill.fill_session,
                "targets": dict(fill.targets),
                "cash_weight": cash,
                "turnover_one_way": fill.turnover_one_way,
            }
        )
    return entries


def run_exact_arm_dry_run(
    cfg: ArmConfig,
    sessions: Sequence[str],
    raw_close: Mapping[str, Mapping[str, float]],
    distributions: Mapping[str, Mapping[str, float]],
    split_factors: Mapping[str, Mapping[str, float]],
    *,
    cost_bps: float,
    ledger: GatedTrialLedger,
    trial_key: str,
) -> DryRunReport:
    """Full schedule build + canonical accounting + publication gate.

    ``ledger`` must be a fresh :class:`GatedTrialLedger` the caller owns
    (in-memory, or backed by a caller-deleted temporary path — a dry run never
    writes to a real ledger location).  See the module docstring for the
    no-scored-metric discipline.
    """
    if not isinstance(ledger, GatedTrialLedger):
        raise DryRunError("dry run requires a GatedTrialLedger owned by the caller")

    # 1. double generation: two independent code paths, byte-identical.
    sched_walk = build_schedule(cfg, sessions)
    sched_blocks = build_schedule_from_windows(cfg, sessions)
    identical = schedules_equal(sched_walk, sched_blocks)
    if not identical:
        raise DryRunError(
            f"{cfg.arm_id}: the two schedule generation paths disagree "
            "(canonical JSON inequality)"
        )
    schedule = sched_walk

    # fail closed unless every fill date has closes for every held symbol
    missing: list[str] = []
    for fill in schedule.fills:
        for s, w in fill.targets.items():
            if s == CASH_SYMBOL or w == 0.0:
                continue
            if fill.fill_session not in raw_close.get(s, {}):
                missing.append(f"{s}@{fill.fill_session}")
    if missing:
        raise ScheduleError(
            f"fills lack raw closes for held legs (first 5): {missing[:5]}"
        )

    # 2. canonical factory valuation (numbers consumed internally only).
    entries = schedule_book_entries(schedule)
    result = value_book(
        entries,
        raw_close,
        distributions,
        split_factors,
        list(sessions),
        cost_bps=cost_bps,
    )

    # 3. the canonical books must close (raises AttributionBreakError otherwise).
    assert_reconciles(result)
    once_only_ok = len(result.fill_costs) == len(entries) and result.total_cost >= 0.0

    # 4. publication gate on the caller-owned (temporary) ledger.
    metrics = publication_metrics(entries)
    if metrics["n_fill_events"] != len(schedule.fills):
        raise DryRunError(
            f"publication fill-event count {metrics['n_fill_events']} != "
            f"schedule fills {len(schedule.fills)}"
        )
    artifact = {
        "kind": "EXACT_ARM_DRY_RUN_SCHEDULE_ONLY",
        "arm_id": cfg.arm_id,
        "config_digest": cfg.digest,
        "schedule_digest": schedule.schedule_digest,
        "coverage_sessions": len(schedule.sessions),
        "window_sessions": len(schedule.window_sessions),
        "n_fills": len(schedule.fills),
        "n_transitions": len(schedule.transitions),
        "transitions_turnover_one_way_total": sum(
            f.turnover_one_way for f in schedule.transitions
        ),
        "cost_bps": cost_bps,
        "accounting": {"attribution_reconciled": True, "cost_charged_once": once_only_ok},
    }
    ledger.compute_recorded(trial_key)
    observed_after_compute = ledger.observed
    published = ledger.publish_result(
        trial_key, artifact,
        n_fill_events=metrics["n_fill_events"],
        n_held_positions=metrics["n_held_positions"],
    )
    replay_delta = ledger.publish_result(
        trial_key, artifact,
        n_fill_events=metrics["n_fill_events"],
        n_held_positions=metrics["n_held_positions"],
    )
    if not published or replay_delta:
        raise DryRunError(
            f"publication gate semantics broken for {trial_key!r}: "
            f"first={published} replay={replay_delta}"
        )

    return DryRunReport(
        arm_id=cfg.arm_id,
        arm_key=cfg.arm_key,
        config_digest=cfg.digest,
        schedule_digest=schedule.schedule_digest,
        double_generation_identical=identical,
        coverage_sessions=len(schedule.sessions),
        window_sessions=len(schedule.window_sessions),
        n_fills=len(schedule.fills),
        n_transitions=len(schedule.transitions),
        establishment_fill_session=schedule.establishment_fill.fill_session,
        transitions_turnover_one_way_total=artifact[
            "transitions_turnover_one_way_total"
        ],
        valuation={
            "attribution_reconciled": True,
            "cost_charged_once": once_only_ok,
            "n_fills_costed": len(result.fill_costs),
            "n_held_positions": metrics["n_held_positions"],
        },
        ledger={
            "observed_after_compute": observed_after_compute,
            "published": bool(published),
            "replay_zero_delta": not replay_delta,
            "n_published_keys": len(ledger.published_keys),
        },
    )


__all__ = [
    "DryRunError",
    "DryRunReport",
    "run_exact_arm_dry_run",
    "schedule_book_entries",
]
