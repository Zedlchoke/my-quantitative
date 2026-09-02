"""V11 lane A3 -- schedule-only cost feasibility gate (PLAN section 7, A3).

The gate consumes SCHEDULE ARTIFACTS ONLY: decision instants, target books,
fill prices used as cost inputs, funding-cadence settlements and the declared
:class:`research.adapter_v10.protocol.CostModel`. It emits the frozen
feasibility metrics and enforces the frozen pre-score floors as explicit
PASS/FAIL/UNAVAILABLE flags.

Hard scientific constraint: the gate MUST NOT compute or expose any scored
outcome series. Every metric below is a count, a duration, a traded-notional
fraction or a cost drag -- never a capital path. Cost arithmetic is reused
verbatim from the V10 adapter (:meth:`GenericStrategyBase.rebalance_cost_between`);
nothing here re-implements fee or slippage math.

Fail-closed rule: any missing input marks the affected metric ``UNAVAILABLE``
and forces the overall verdict to ``UNAVAILABLE_FAIL_CLOSED``. A missing input
can never produce an inferred PASS.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    AdapterError,
    ContractViolation,
    CostModel,
    ImmutableSchedule,
    SettlementPoint,
    StressSpec,
)

SCHEMA_VERSION = "v11.cost_feasibility.a3.v1"
PRODUCER_ROLE = "A3"

DAY_NS = 86_400_000_000_000
YEAR_DAYS = 365.0

#: Decision vocabulary. Risk/terminal forced-flat actions are counted and
#: reported SEPARATELY from discretionary rebalance decisions.
KIND_DISCRETIONARY = "DISCRETIONARY"
KIND_FORCED_FLAT = "FORCED_FLAT"
KNOWN_DECISION_KINDS = (KIND_DISCRETIONARY, KIND_FORCED_FLAT)

#: Frozen stressed cell: fee x1.5 PLUS +2 adverse ticks on the declared floor
#: (PLAN section 7 / A3: "fee x1.5/+2-tick stressed cost drag").
STRESS_NAME = "stress_fee_x1_5_plus_2_ticks"
STRESS_FEE_MULTIPLIER = 1.5
STRESS_EXTRA_TICKS = 2

#: Frozen pre-score floors (PLAN section 7 / lane A3). Any threshold change
#: requires an owner amendment BEFORE proposal scoring; never after a failure.
FLOOR_MAX_DISCRETIONARY_DECISIONS_PER_365D = 60.0
FLOOR_MIN_MEDIAN_INTENDED_HOLDING_DAYS = 3.0
FLOOR_MAX_BASE_COST_DRAG_FRAC_OF_GROSS = 0.08
FLOOR_MAX_STRESSED_COST_DRAG_FRAC_OF_GROSS = 0.12
FLOOR_MAX_SYMBOL_TURNOVER_SHARE = 0.25

METRIC_OK = "OK"
METRIC_UNAVAILABLE = "UNAVAILABLE"
VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"

#: Frozen floor table emitted verbatim into every report payload.
FLOOR_TABLE: tuple[dict[str, Any], ...] = (
    {
        "floor_id": "max_discretionary_decisions_per_365d",
        "metric_key": "decisions_per_365d",
        "comparator": "lte",
        "frozen_threshold": FLOOR_MAX_DISCRETIONARY_DECISIONS_PER_365D,
        "definition": (
            "scheduled discretionary rebalance decisions normalised to a "
            "365-day equivalent window must not exceed 60"
        ),
    },
    {
        "floor_id": "min_median_intended_holding_days",
        "metric_key": "median_intended_holding_days",
        "comparator": "gte",
        "frozen_threshold": FLOOR_MIN_MEDIAN_INTENDED_HOLDING_DAYS,
        "definition": (
            "median completed intended holding span (calendar days, from "
            "target-book occupancy) must be at least 3"
        ),
    },
    {
        "floor_id": "max_base_cost_drag_frac_of_gross",
        "metric_key": "annualised_base_cost_drag_frac_of_gross",
        "comparator": "lte",
        "frozen_threshold": FLOOR_MAX_BASE_COST_DRAG_FRAC_OF_GROSS,
        "definition": (
            "annualised transition cost at the declared cost floor, divided "
            "by average gross capital, must not exceed 0.08"
        ),
    },
    {
        "floor_id": "max_stressed_cost_drag_frac_of_gross",
        "metric_key": "annualised_stressed_cost_drag_frac_of_gross",
        "comparator": "lte",
        "frozen_threshold": FLOOR_MAX_STRESSED_COST_DRAG_FRAC_OF_GROSS,
        "definition": (
            "annualised transition cost under fee x1.5 and +2 adverse ticks, "
            "divided by average gross capital, must not exceed 0.12"
        ),
    },
    {
        "floor_id": "max_symbol_turnover_share",
        "metric_key": "max_symbol_turnover_share",
        "comparator": "lte",
        "frozen_threshold": FLOOR_MAX_SYMBOL_TURNOVER_SHARE,
        "definition": (
            "no single symbol may contribute more than 25% of total one-way "
            "turnover (sum of absolute target deltas)"
        ),
    },
)


# --------------------------------------------------------------------------- #
# Schedule artifact inputs (data only; no outcome series is representable)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ScheduleDecision:
    """One scheduled decision instant with its intended target book.

    ``kind`` separates discretionary rebalances from risk/terminal
    forced-flat actions; forced-flat actions never enter the discretionary
    decision count or the per-365d normalisation.
    """

    instant_ns: int
    kind: str
    weights: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if int(self.instant_ns) < 0:
            raise ContractViolation("decision.instant_ns must be non-negative")
        if self.kind not in KNOWN_DECISION_KINDS:
            raise ContractViolation(
                f"decision kind {self.kind!r} outside {KNOWN_DECISION_KINDS}"
            )
        for sym, weight in dict(self.weights).items():
            if not str(sym).strip():
                raise ContractViolation("decision weight symbol must be non-empty")
            if not math.isfinite(float(weight)):
                raise ContractViolation(
                    f"non-finite target weight for {sym} at {self.instant_ns}"
                )


@dataclass(frozen=True)
class SignalAvailability:
    """Proposed-signal availability observed at one decision instant."""

    instant_ns: int
    available: bool
    missing_symbols: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if int(self.instant_ns) < 0:
            raise ContractViolation("signal_availability.instant_ns must be non-negative")


@dataclass(frozen=True)
class ScheduleArtifacts:
    """The complete schedule-artifact bundle the gate is allowed to read."""

    instants_ns: Sequence[int]
    decisions: Mapping[int, ScheduleDecision]
    #: Strict-later fill price per (decision instant, symbol); COST INPUT ONLY.
    fill_prices: Mapping[int, Mapping[str, float]] = field(default_factory=dict)
    #: Funding cadence: native settlement points per symbol (counts only).
    settlements: Mapping[str, tuple[SettlementPoint, ...]] = field(default_factory=dict)
    cost_model: Optional[CostModel] = None
    signal_availability: Optional[Mapping[int, SignalAvailability]] = None
    source: str = "ScheduleArtifacts"

    def __post_init__(self) -> None:
        if self.cost_model is None:
            raise ContractViolation("cost_model is required (declared floors only)")
        instants = tuple(int(v) for v in self.instants_ns)
        if list(instants) != sorted(set(instants)):
            raise ContractViolation("schedule instants must be strictly increasing")
        object.__setattr__(self, "instants_ns", instants)
        for instant in instants:
            if int(instant) not in self.decisions:
                raise ContractViolation(
                    f"missing ScheduleDecision for scheduled instant {instant}"
                )


class _GateCostAdapter(GenericStrategyBase):
    """Minimal adapter surface so the gate REUSES the frozen cost math.

    No arithmetic lives here: transition cost comes verbatim from
    :meth:`GenericStrategyBase.rebalance_cost_between`, which applies
    ``taker_fee_bps * 1e-4 * fee_multiplier`` per side plus
    ``ticks * tick_size / price`` adverse slippage and fails closed on any
    missing price or tick size.
    """

    def __init__(
        self,
        cost_model: CostModel,
        settlements_by_symbol: Mapping[str, tuple[SettlementPoint, ...]],
    ) -> None:
        self._cost_model = cost_model
        self._settlements = {
            str(sym): tuple(points) for sym, points in dict(settlements_by_symbol).items()
        }

    def cost_model(self) -> CostModel:
        return self._cost_model

    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        return self._settlements.get(str(symbol), ())


@dataclass(frozen=True)
class CostFeasibilityReport:
    """Gate outcome: an explicit verdict plus the reproducible payload."""

    verdict: str
    payload: Mapping[str, Any]


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #
def _r9(value: float) -> float:
    """Round for deterministic JSON emission (well below any floor margin)."""
    rounded = round(float(value), 9)
    if not math.isfinite(rounded):
        raise ContractViolation("non-finite metric value cannot be emitted")
    return rounded


def _metric(definition: str, status: str = METRIC_OK, value: Any = None, reason: str = "") -> dict[str, Any]:
    return {
        "definition": definition,
        "status": status,
        "value": value,
        "reason": reason,
    }


def _unavailable(definition: str, reason: str) -> dict[str, Any]:
    return _metric(definition, status=METRIC_UNAVAILABLE, value=None, reason=reason)


def _settlements_inside_count(
    points: Sequence[SettlementPoint], start_ns: int, end_ns: int
) -> int:
    """Count settlement events strictly inside ``(start_ns, end_ns]``.

    Identical interval semantics to the adapter's funding accrual window, but
    this counts cadence only -- no rate is multiplied out, so no capital
    path can be reconstructed from this metric.
    """
    return sum(1 for p in points if start_ns < int(p.publish_ts_ns) <= end_ns)


def _holding_spans(
    instants: Sequence[int], books: Sequence[Mapping[str, float]]
) -> tuple[list[tuple[str, int, int]], list[tuple[str, int]]]:
    """Intended holding spans per symbol from target-book occupancy.

    Returns ``(completed, censored)`` where a completed span is
    ``(symbol, start_ns, end_ns)`` and a censored span is still open at the
    last scheduled instant (typically closed by the terminal force-flat).
    Censored spans are never silently closed by inference.
    """
    open_spans: dict[str, int] = {}
    completed: list[tuple[str, int, int]] = []
    censored: list[tuple[str, int]] = []
    for instant, book in zip(instants, books):
        held = {str(sym) for sym, w in book.items() if float(w) != 0.0}
        for sym in sorted(held - set(open_spans)):
            open_spans[sym] = int(instant)
        for sym in sorted(set(open_spans) - held):
            completed.append((sym, open_spans.pop(sym), int(instant)))
    for sym in sorted(open_spans):
        censored.append((sym, open_spans[sym]))
    return completed, censored


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
def evaluate_schedule_cost_feasibility(artifacts: ScheduleArtifacts) -> CostFeasibilityReport:
    """Compute every frozen feasibility metric from schedule artifacts alone."""
    if not isinstance(artifacts, ScheduleArtifacts):
        raise ContractViolation("evaluate_schedule_cost_feasibility needs ScheduleArtifacts")

    # Reuse the adapter's schedule validation + canonical hash.
    schedule = ImmutableSchedule(
        instants=tuple(artifacts.instants_ns),
        source=artifacts.source,
        clock="schedule_artifacts_utc_epoch_ns",
    )
    instants: tuple[int, ...] = tuple(schedule.instants)
    decisions = dict(artifacts.decisions)
    books: list[Mapping[str, float]] = [
        {str(sym): float(w) for sym, w in decisions[int(t)].weights.items()} for t in instants
    ]
    kinds = [decisions[int(t)].kind for t in instants]

    metrics: dict[str, dict[str, Any]] = {}

    # ---------------- window ---------------- #
    window_days = (instants[-1] - instants[0]) / DAY_NS
    if window_days <= 0.0:
        metrics["window_days"] = _unavailable(
            "scheduled window length in calendar days", "degenerate schedule window"
        )
    else:
        metrics["window_days"] = _metric(
            "scheduled window length in calendar days "
            "(last decision instant minus first, normalised by one day)",
            value=_r9(window_days),
        )
    window_ok = metrics["window_days"]["status"] == METRIC_OK

    # ---------------- decision counts ---------------- #
    n_discretionary = sum(1 for k in kinds if k == KIND_DISCRETIONARY)
    n_forced_flat = sum(1 for k in kinds if k == KIND_FORCED_FLAT)
    metrics["discretionary_decision_count"] = _metric(
        "scheduled discretionary rebalance decisions "
        "(risk/terminal forced-flat actions counted separately)",
        value=int(n_discretionary),
    )
    metrics["forced_flat_decision_count"] = _metric(
        "risk/terminal forced-flat actions, reported separately from "
        "discretionary decisions and excluded from the per-365d floor",
        value=int(n_forced_flat),
    )
    if window_ok:
        metrics["decisions_per_365d"] = _metric(
            "discretionary decisions normalised to a 365-day equivalent: "
            "n_discretionary * 365 / window_days",
            value=_r9(n_discretionary * YEAR_DAYS / window_days),
        )
    else:
        metrics["decisions_per_365d"] = _unavailable(
            "discretionary decisions normalised to a 365-day equivalent: "
            "n_discretionary * 365 / window_days",
            "window unavailable",
        )

    # ---------------- one-way turnover from actual target deltas ---------------- #
    prev_book: dict[str, float] = {}
    per_symbol_delta: dict[str, float] = {str(sym): 0.0 for sym in _union_symbols(books)}
    disc_turnover = 0.0
    forced_turnover = 0.0
    for book, kind in zip(books, kinds):
        transition = 0.0
        for sym in sorted(per_symbol_delta):
            delta = abs(float(book.get(sym, 0.0)) - float(prev_book.get(sym, 0.0)))
            per_symbol_delta[sym] += delta
            transition += delta
        if kind == KIND_FORCED_FLAT:
            forced_turnover += transition
        else:
            disc_turnover += transition
        prev_book = dict(book)
    total_turnover = disc_turnover + forced_turnover
    metrics["one_way_turnover_discretionary"] = _metric(
        "one-way turnover (sum of absolute target deltas, capital-weight "
        "units) across transitions into discretionary books, including the "
        "initial entry from flat",
        value=_r9(disc_turnover),
    )
    metrics["one_way_turnover_forced_flat"] = _metric(
        "one-way turnover across transitions into forced-flat books, "
        "reported separately from discretionary turnover",
        value=_r9(forced_turnover),
    )
    metrics["one_way_turnover_total"] = _metric(
        "total one-way turnover: discretionary plus forced-flat transitions",
        value=_r9(total_turnover),
    )
    total_for_share = _r9(total_turnover)
    if total_for_share > 0.0:
        shares = {
            sym: _r9(delta / total_turnover)
            for sym, delta in sorted(per_symbol_delta.items())
        }
        worst = max(shares.items(), key=lambda kv: (kv[1], kv[0]))
        metrics["per_symbol_turnover_share"] = _metric(
            "per-symbol share of total one-way turnover", value=shares
        )
        metrics["max_symbol_turnover_share"] = _metric(
            "largest single-symbol share of total one-way turnover",
            value=worst[1],
        )
        metrics["max_symbol_turnover_share_symbol"] = _metric(
            "symbol holding the largest turnover share", value=worst[0]
        )
    else:
        metrics["per_symbol_turnover_share"] = _unavailable(
            "per-symbol share of total one-way turnover",
            "total one-way turnover is zero; shares are undefined",
        )
        metrics["max_symbol_turnover_share"] = _unavailable(
            "largest single-symbol share of total one-way turnover",
            "total one-way turnover is zero; shares are undefined",
        )

    # ---------------- cost drag from the adapter cost functions ---------------- #
    baseline_stress = StressSpec(
        name="baseline",
        fee_multiplier=1.0,
        tick_slip_ticks=int(artifacts.cost_model.adverse_tick_slip_floor),
        event_delay_events=0,
        drop_symbols=(),
        dropped_fold_index=None,
    )
    stressed_stress = StressSpec(
        name=STRESS_NAME,
        fee_multiplier=STRESS_FEE_MULTIPLIER,
        tick_slip_ticks=int(artifacts.cost_model.adverse_tick_slip_floor) + STRESS_EXTRA_TICKS,
        event_delay_events=0,
        drop_symbols=(),
        dropped_fold_index=None,
    )
    adapter = _GateCostAdapter(artifacts.cost_model, artifacts.settlements)
    gross_values = [math.fsum(abs(float(w)) for w in book.values()) for book in books]
    avg_gross = math.fsum(gross_values) / len(gross_values) if gross_values else 0.0
    metrics["average_gross_capital"] = _metric(
        "mean target-book gross capital (sum of absolute weights) over all "
        "scheduled decision instants",
        value=_r9(avg_gross),
    )

    def _annualised_drag(spec: StressSpec, key: str, definition: str) -> None:
        if not window_ok:
            metrics[key] = _unavailable(definition, "window unavailable")
            return
        if avg_gross <= 0.0:
            metrics[key] = _unavailable(
                definition, "average gross capital is zero; drag is undefined"
            )
            return
        try:
            transition_costs = [
                adapter.rebalance_cost_between(
                    prev,
                    book,
                    prices=dict(artifacts.fill_prices.get(int(instant), {})),
                    stress=spec,
                )
                for prev, book, instant in _transitions(instants, books)
            ]
        except AdapterError as exc:
            metrics[key] = _unavailable(definition, f"adapter cost function failed closed: {exc}")
            return
        total_cost = _r9(math.fsum(transition_costs))
        annualised = total_cost / (window_days / YEAR_DAYS)
        metrics[f"{key}_total_cost"] = _metric(
            f"total transition cost over the window under stress {spec.name!r} "
            "(capital-weight units, adapter cost arithmetic)",
            value=total_cost,
        )
        metrics[key] = _metric(
            definition,
            value=_r9(annualised / avg_gross),
        )

    _annualised_drag(
        baseline_stress,
        "annualised_base_cost_drag_frac_of_gross",
        "annualised base cost drag as a fraction of average gross capital, "
        "using the declared cost floors via the adapter cost function",
    )
    _annualised_drag(
        stressed_stress,
        "annualised_stressed_cost_drag_frac_of_gross",
        "annualised cost drag as a fraction of average gross capital under "
        "the frozen fee x1.5 / +2-tick stressed cell, via the adapter cost "
        "function",
    )

    # ---------------- holding duration ---------------- #
    completed, censored = _holding_spans(instants, books)
    metrics["completed_holding_span_count"] = _metric(
        "intended holding spans closed by the schedule (symbol weight is "
        "zero again at a scheduled decision)",
        value=int(len(completed)),
    )
    metrics["censored_open_span_count"] = _metric(
        "intended holding spans still open at the last scheduled instant; "
        "excluded from duration statistics and never silently closed",
        value=int(len(censored)),
    )
    if completed:
        durations = [
            (end - start) / DAY_NS for _, start, end in sorted(completed, key=lambda s: (s[0], s[1]))
        ]
        metrics["median_intended_holding_days"] = _metric(
            "median completed intended holding span in calendar days",
            value=_r9(statistics.median(durations)),
        )
        metrics["max_intended_holding_days"] = _metric(
            "maximum completed intended holding span in calendar days",
            value=_r9(max(durations)),
        )
    else:
        metrics["median_intended_holding_days"] = _unavailable(
            "median completed intended holding span in calendar days",
            "no completed holding span in the schedule (all spans censored)",
        )
        metrics["max_intended_holding_days"] = _unavailable(
            "maximum completed intended holding span in calendar days",
            "no completed holding span in the schedule (all spans censored)",
        )

    # ---------------- funding-event count while held ---------------- #
    held_symbols = sorted({sym for sym, _, _ in completed} | {sym for sym, _ in censored})
    missing_settlements = [sym for sym in held_symbols if sym not in artifacts.settlements]
    if not held_symbols:
        metrics["funding_events_while_held_total"] = _unavailable(
            "expected funding-event count while held",
            "no intended holding span exists in the schedule",
        )
        metrics["funding_events_per_365d"] = _unavailable(
            "funding events while held normalised to a 365-day equivalent",
            "no intended holding span exists in the schedule",
        )
    elif missing_settlements:
        metrics["funding_events_while_held_total"] = _unavailable(
            "expected funding-event count while held",
            f"missing settlement cadence for held symbols: {missing_settlements}",
        )
        metrics["funding_events_per_365d"] = _unavailable(
            "funding events while held normalised to a 365-day equivalent",
            f"missing settlement cadence for held symbols: {missing_settlements}",
        )
    else:
        events = 0
        for sym, start, end in completed:
            events += _settlements_inside_count(artifacts.settlements[sym], start, end)
        for sym, start in censored:
            events += _settlements_inside_count(artifacts.settlements[sym], start, instants[-1])
        metrics["funding_events_while_held_total"] = _metric(
            "count of native settlement events falling inside intended "
            "holding spans (cadence only; no rate is applied)",
            value=int(events),
        )
        if window_ok:
            metrics["funding_events_per_365d"] = _metric(
                "funding events while held normalised to a 365-day equivalent",
                value=_r9(events * YEAR_DAYS / window_days),
            )
        else:
            metrics["funding_events_per_365d"] = _unavailable(
                "funding events while held normalised to a 365-day equivalent",
                "window unavailable",
            )

    # ---------------- proposed signal availability / missingness ---------------- #
    availability = artifacts.signal_availability
    if availability is None:
        metrics["signal_availability_fraction"] = _unavailable(
            "fraction of scheduled decision instants where the proposed "
            "signal was available",
            "signal availability artifact not supplied",
        )
        metrics["signal_missing_instant_count"] = _unavailable(
            "count of scheduled instants where the proposed signal was unavailable",
            "signal availability artifact not supplied",
        )
        metrics["signal_missing_instants"] = _unavailable(
            "scheduled instants where the proposed signal was unavailable",
            "signal availability artifact not supplied",
        )
    else:
        coverage_gaps = [int(t) for t in instants if int(t) not in availability]
        if coverage_gaps:
            metrics["signal_availability_fraction"] = _unavailable(
                "fraction of scheduled decision instants where the proposed "
                "signal was available",
                f"signal availability missing for instants: {coverage_gaps}",
            )
            metrics["signal_missing_instant_count"] = _unavailable(
                "count of scheduled instants where the proposed signal was unavailable",
                f"signal availability missing for instants: {coverage_gaps}",
            )
            metrics["signal_missing_instants"] = _unavailable(
                "scheduled instants where the proposed signal was unavailable",
                f"signal availability missing for instants: {coverage_gaps}",
            )
        else:
            rows = [availability[int(t)] for t in instants]
            missing = [int(t) for t, row in zip(instants, rows) if not row.available]
            metrics["signal_availability_fraction"] = _metric(
                "fraction of scheduled decision instants where the proposed "
                "signal was available",
                value=_r9((len(instants) - len(missing)) / len(instants)),
            )
            metrics["signal_missing_instant_count"] = _metric(
                "count of scheduled instants where the proposed signal was unavailable",
                value=int(len(missing)),
            )
            metrics["signal_missing_instants"] = _metric(
                "scheduled instants where the proposed signal was unavailable",
                value=missing,
            )

    # ---------------- floors ---------------- #
    floors: list[dict[str, Any]] = []
    for spec in FLOOR_TABLE:
        metric = metrics[spec["metric_key"]]
        if metric["status"] != METRIC_OK:
            status: str = METRIC_UNAVAILABLE
            observed = None
        else:
            observed = metric["value"]
            if spec["comparator"] == "lte":
                ok = float(observed) <= float(spec["frozen_threshold"])
            elif spec["comparator"] == "gte":
                ok = float(observed) >= float(spec["frozen_threshold"])
            else:
                raise ContractViolation(f"unknown floor comparator {spec['comparator']!r}")
            status = VERDICT_PASS if ok else VERDICT_FAIL
        floors.append(
            {
                "floor_id": spec["floor_id"],
                "metric_key": spec["metric_key"],
                "comparator": spec["comparator"],
                "frozen_threshold": spec["frozen_threshold"],
                "observed": observed,
                "status": status,
            }
        )

    unavailable_metrics = sorted(
        key for key, metric in metrics.items() if metric["status"] != METRIC_OK
    )
    if unavailable_metrics:
        verdict = VERDICT_UNAVAILABLE
    elif all(row["status"] == VERDICT_PASS for row in floors):
        verdict = VERDICT_PASS
    else:
        verdict = VERDICT_FAIL

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "producer_role": PRODUCER_ROLE,
        "verdict": verdict,
        "schedule_sha256": schedule.sha256,
        "schedule_source": schedule.source,
        "schedule_instant_count": len(instants),
        "stress_surface": {
            "baseline": baseline_stress.signature(),
            "stressed": stressed_stress.signature(),
        },
        "metrics": metrics,
        "floors": floors,
        "floor_table_frozen": [dict(spec) for spec in FLOOR_TABLE],
        "unavailable_metrics": unavailable_metrics,
        "outcome_blind_attestation": {
            "schedule_artifacts_only": True,
            "scored_outcome_series_emitted": False,
            "explanation": (
                "every metric derives from decision instants, target books, "
                "fill-price cost inputs, funding cadence and declared cost "
                "parameters; the gate computes and exposes no scored "
                "capital path of any candidate"
            ),
        },
    }
    return CostFeasibilityReport(verdict=verdict, payload=payload)


def _transitions(
    instants: Sequence[int], books: Sequence[Mapping[str, float]]
) -> list[tuple[Mapping[str, float], Mapping[str, float], int]]:
    """(previous book, new book, instant) triples including the flat entry."""
    out: list[tuple[Mapping[str, float], Mapping[str, float], int]] = []
    prev: Mapping[str, float] = {}
    for instant, book in zip(instants, books):
        out.append((prev, book, int(instant)))
        prev = book
    return out


def _union_symbols(books: Sequence[Mapping[str, float]]) -> set[str]:
    union: set[str] = set()
    for book in books:
        union |= {str(sym) for sym in book}
    return union


__all__ = [
    "DAY_NS",
    "FLOOR_TABLE",
    "KIND_DISCRETIONARY",
    "KIND_FORCED_FLAT",
    "PRODUCER_ROLE",
    "SCHEMA_VERSION",
    "ScheduleArtifacts",
    "ScheduleDecision",
    "SignalAvailability",
    "STRESS_EXTRA_TICKS",
    "STRESS_FEE_MULTIPLIER",
    "STRESS_NAME",
    "CostFeasibilityReport",
    "VERDICT_FAIL",
    "VERDICT_PASS",
    "VERDICT_UNAVAILABLE",
    "evaluate_schedule_cost_feasibility",
]
