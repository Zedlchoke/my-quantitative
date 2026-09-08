"""Generic adapter/runner: schedule -> folds -> metrics -> payloads (G1).

Orchestrates a :class:`research.adapter_v10.protocol.ResearchStrategy`
without ever knowing which family/arm/trial it belongs to:

1. identity + immutable schedule provider;
2. universe under the selected stress cell;
3. chronological folds with purge and the final force-flat boundary;
4. daily target books (BG2 conversion) and strict-later fill sweeps;
5. realized after-cost/funding accounting -> closed-position ledger +
   per-decision-instant realized rows (BG1);
6. fold-level PF / expectancy / max-drawdown table;
7. portfolio/fill/scoring payload assembly (BG2);
8. context-only benchmark block (BG5);
9. deterministic artifact emission into unique stress-specific roots (BG4).

Nothing here evaluates or publishes a scored V10 metric: scoring remains the
harness' job, publication is gated through ``publish.publish_trial``.
"""

from __future__ import annotations

import dataclasses
import math
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.benchmarks import build_benchmark_block
from research.adapter_v10.converters import (
    STATUS_FORCE_FLAT,
    build_portfolio_payload,
    fill_payload_row,
    normalise_target_book,
    summarise_books,
)
from research.adapter_v10.metrics import (
    ClosedPosition,
    DailyRealizedRow,
    aggregate_portfolio,
    attribution_buckets,
    allocate_cost_to_legs,
    assert_no_cross_fold_holding,
    fold_metric_table,
    fold_membership,
)
from research.adapter_v10.protocol import (
    DEFAULT_WEIGHT_CAP_MAX,
    WEIGHT_TOL,
    ContractViolation,
    DataUnavailable,
    FillRecord,
    ImmutableSchedule,
    PositionSpan,
    ResearchStrategy,
    SCHEMA_VERSION,
    StrategyIdentity,
    StressSpec,
)
from research.adapter_v10.stress import (
    BASELINE_NAME,
    assert_unique_roots,
    stress_matrix_cells,
)
from research.adapter_v10.hashes import atomic_write_json, payload_sha256

ACTION_OPEN = "OPEN_REBALANCE"
ACTION_OPEN_SKIPPED = "OPEN_REBALANCE_SKIPPED"
ACTION_CARRY = "OPEN_CARRIED_FORWARD"
ACTION_PURGE_GAP_CARRY = "PURGE_GAP_CARRY"
PURGE_GAP_ENTRY_FORBIDDEN = "purge_gap_entry_forbidden"
FOLD_SOURCE_MISMATCH = "fold_source_mismatch"


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def run_strategy(
    strategy: ResearchStrategy,
    *,
    stress: Optional[StressSpec] = None,
    cap_max: float = DEFAULT_WEIGHT_CAP_MAX,
    out_dir: Optional[str | Path] = None,
    write_artifact_file: bool = True,
) -> dict[str, Any]:
    """Run ONE stress cell end-to-end and return the deterministic bundle."""
    baseline = strategy.baseline_stress()
    if not baseline.is_baseline or baseline.name != BASELINE_NAME:
        raise ContractViolation(
            f"baseline_stress() must be named {BASELINE_NAME!r}, got {baseline.name!r}"
        )
    selected = baseline if (stress is None or stress.is_baseline) else stress
    _validate_strategy_shape(strategy, baseline=selected)

    identity = strategy.identity()
    schedule = strategy.schedule()
    universe = strategy.universe(selected)
    if len(universe) < 2:
        raise ContractViolation("universe needs at least two names")
    excluded = {str(s) for s in identity.benchmark_symbols_excluded}
    leaked = sorted(excluded & set(universe))
    if leaked:
        raise ContractViolation(
            f"benchmark-excluded symbols cannot be tradeable members: {leaked}"
        )
    context_symbols = tuple(
        str(sym) for sym in _context_symbols_for(strategy, universe, excluded)
    )

    folds = strategy.folds(stress=selected, instants=list(schedule.instants))
    _validate_folds(folds, instants=list(schedule.instants))
    fold_by_instant = attribution_buckets(folds, list(schedule.instants))

    books = _collect_books(
        strategy,
        schedule=schedule,
        universe=universe,
        stress=selected,
        cap_max=cap_max,
    )

    declared_members = {
        int(instant)
        for fold in folds
        if not fold.dropped
        for instant in fold.instants
    }
    gap_instants = {int(v) for v in schedule.instants} - declared_members
    boundaries = _resolve_boundaries(
        strategy,
        schedule=schedule,
        books=books,
        stress=selected,
        gap_instants=gap_instants,
    )
    positions, daily_rows, payload_rows = _account_boundaries(
        strategy,
        identity=identity,
        fold_by_instant=fold_by_instant,
        boundaries=boundaries,
        books=books,
        stress=selected,
    )
    assert_no_cross_fold_holding(positions)

    fold_table = fold_metric_table(
        folds=folds, daily_rows=daily_rows, positions=positions
    )
    portfolio_block = aggregate_portfolio(daily_rows=daily_rows, positions=positions)
    portfolio = build_portfolio_payload(payload_rows, stress=selected)
    benchmarks = build_benchmark_block(
        identity=identity,
        context_symbols=context_symbols,
        instants=list(schedule.instants),
        marks_at=lambda syms, ts: _marks_or_fail(strategy, syms, ts),
    )

    membership = fold_membership(folds, list(schedule.instants))
    attributed: dict[int, list[int]] = {
        int(fold.index): [] for fold in sorted(folds, key=lambda f: f.index)
    }
    for instant, owner in sorted(fold_by_instant.items()):
        attributed[int(owner.index)].append(int(instant))
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "producer_role": "G1",
        "identity": identity.public_payload(),
        "cost_model": {
            "taker_fee_bps": float(strategy.cost_model().taker_fee_bps),
            "adverse_tick_slip_floor": int(strategy.cost_model().adverse_tick_slip_floor),
            "default_tick_sizes": {
                str(k): float(v)
                for k, v in sorted(strategy.cost_model().default_tick_sizes.items())
            },
        },
        "stress": selected.signature(),
        "universe": list(universe),
        "benchmark_symbols_excluded": sorted(excluded),
        "schedule": {
            "source": schedule.source,
            "clock": schedule.clock,
            "n_instants": len(schedule.instants),
            "sha256": schedule.sha256,
            "first_decision_ns": int(schedule.instants[0]),
            "last_decision_ns": int(schedule.instants[-1]),
        },
        "folds": [
            {
                "index": int(fold.index),
                "label": fold.label,
                "purge_days": int(fold.purge_days),
                "instants": [int(v) for v in fold.instants],
                "dropped": bool(fold.dropped),
            }
            for fold in sorted(folds, key=lambda f: f.index)
        ],
        "fold_membership": {str(k): v for k, v in sorted(membership.items())},
        "fold_attribution": {
            str(k): sorted(v) for k, v in sorted(attributed.items())
        },
        "purge_gap_instants": sorted(int(v) for v in gap_instants),
        "books": [
            {
                "decision_ns": int(book.decision_ns),
                "status": book.status,
                "carried_forward": book.carried_forward,
                "weights": [[sym, round(w, 12)] for sym, w in book.weights],
                "longs": [[sym, round(w, 12)] for sym, w in book.longs],
                "shorts": [[sym, round(w, 12)] for sym, w in book.shorts],
                "diagnostics": dict(book.diagnostics),
            }
            for book in (books[i] for i in sorted(books))
        ],
        "portfolio_payload": portfolio,
        "daily_returns": [row.as_dict() for row in daily_rows],
        "positions": [p.as_dict() for p in positions],
        "fold_metrics": fold_table,
        "portfolio_metrics": portfolio_block,
        "benchmarks": benchmarks,
        "book_summary": summarise_books(list(books.values())),
        "scored": False,
        "artifacts": {},
    }

    result["hashes"] = {
        "result_sha256": payload_sha256(_strip(result, ("hashes", "artifacts"))),
        "portfolio_payload_sha256": payload_sha256(portfolio),
        "fold_metrics_sha256": payload_sha256(fold_table),
        "positions_sha256": payload_sha256([p.as_dict() for p in positions]),
        "benchmarks_sha256": payload_sha256(benchmarks),
        "schedule_sha256": schedule.sha256,
    }
    if write_artifact_file:
        root = out_dir if out_dir is not None else Path("results") / selected.key
        paths = write_cell_artifacts(result, root=root)
        result["artifacts"] = paths
    return result


def run_full_stress_matrix(
    strategy: ResearchStrategy,
    *,
    cap_max: float = DEFAULT_WEIGHT_CAP_MAX,
    out_root: Optional[str | Path] = None,
) -> dict[str, Any]:
    """BG4 driver: baseline + every frozen named variant, unique roots."""
    cells = stress_matrix_cells(
        strategy_baseline=strategy.baseline_stress(),
        droppable_symbols=tuple(strategy.tradeable_universe()),
    )
    uniqueness = assert_unique_roots(cells)
    runs: dict[str, Any] = {}
    base_root = Path(out_root) if out_root is not None else Path("results") / "adapter_v10_matrix"
    for cell in cells:
        cell_dir = base_root / cell.spec.key
        runs[cell.name] = run_strategy(
            strategy,
            stress=cell.spec,
            cap_max=cap_max,
            out_dir=cell_dir,
        )
        runs[cell.name]["artifact_paths"] = {
            "result_root": str(cell_dir / "results"),
            "shard_root": str(cell_dir / cell.shard_root),
            "log_root": str(cell_dir / cell.log_root),
            "artifact_name": cell.artifact_name,
            "artifact_path": str(cell_dir / cell.artifact_name),
            "canonical_artifact": str(runs[cell.name]["artifacts"]["artifact"]),
        }
        named_payload = dict(runs[cell.name])
        named_payload.pop("artifacts", None)
        atomic_write_json(named_payload, cell_dir / cell.artifact_name)
    matrix_digest = payload_sha256({name: runs[name]["hashes"] for name in runs})
    return {
        "schema_version": SCHEMA_VERSION,
        "producer_role": "G1",
        "matrix_cells": [cell.name for cell in cells],
        "uniqueness": uniqueness,
        "runs": {cell.name: runs[cell.name] for cell in cells},
        "matrix_digest": matrix_digest,
    }


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
def _context_symbols_for(
    strategy: ResearchStrategy, universe: Sequence[str], excluded: set[str]
) -> list[str]:
    """Context-only candidates (e.g. the pinned benchmark leg + the cohort)."""
    declared = [str(sym) for sym in strategy.benchmark_context_symbols()]
    if not declared:
        raise ContractViolation("benchmark_context_symbols() returned no names")
    missing = sorted(excluded - set(declared))
    if missing:
        raise ContractViolation(
            f"declared exclusions absent from the context candidates: {missing}"
        )
    if any(str(sym) in excluded for sym in universe):
        raise ContractViolation("excluded benchmark symbol present in the universe")
    return sorted(set(declared) | {str(sym) for sym in universe})


def _validate_strategy_shape(strategy: ResearchStrategy, *, baseline: StressSpec) -> None:
    if not callable(getattr(strategy, "targets_at", None)):
        raise ContractViolation("strategy must expose targets_at()")
    if not callable(getattr(strategy, "fills_at", None)):
        raise ContractViolation("strategy must expose fills_at()")
    if not callable(getattr(strategy, "marks_at", None)):
        raise ContractViolation("strategy must expose marks_at()")
    if not callable(getattr(strategy, "settlements", None)):
        raise ContractViolation("strategy must expose settlements()")
    if not callable(getattr(strategy, "rebalance_cost_between", None)):
        raise ContractViolation("strategy must expose rebalance_cost_between()")
    del baseline


def _validate_folds(folds: Sequence[Any], *, instants: Sequence[int]) -> None:
    ordered = sorted(folds, key=lambda f: f.index)
    indexes = [int(fold.index) for fold in ordered]
    if len(set(indexes)) != len(indexes):
        raise ContractViolation(f"duplicate fold indexes: {indexes}")
    covered: list[int] = []
    labels: list[str] = []
    for fold in ordered:
        if fold.label in labels:
            raise ContractViolation(f"duplicate fold label {fold.label}")
        labels.append(fold.label)
        if int(fold.purge_days) < 0:
            raise ContractViolation(f"negative purge for fold {fold.label}")
        covered.extend(int(v) for v in fold.instants)
    surviving = [fold for fold in ordered if not fold.dropped]
    if not surviving:
        raise ContractViolation("every fold was dropped; nothing remains to score")
    if len(covered) != len(set(covered)):
        raise ContractViolation(
            "folds must not overlap: a decision instant is a member of two folds"
        )
    if any(not fold.instants for fold in surviving):
        raise ContractViolation("a surviving fold has no instants")
    unknown = sorted(set(covered) - {int(v) for v in instants})
    if unknown:
        raise ContractViolation(
            f"folds declare instants outside the schedule: {unknown[:5]}"
        )
    ordered_instants = sorted(int(v) for v in instants)
    for fold in ordered:
        members = sorted(int(v) for v in fold.instants)
        if members != [v for v in ordered_instants if v in set(members)]:
            raise ContractViolation(f"fold {fold.label} members are not chronological")


# --------------------------------------------------------------------------- #
# Book + boundary construction
# --------------------------------------------------------------------------- #
def _collect_books(
    strategy: ResearchStrategy,
    *,
    schedule: ImmutableSchedule,
    universe: Sequence[str],
    stress: StressSpec,
    cap_max: float,
) -> dict[int, Any]:
    """Target books for every OPEN instant (never the force-flat boundary)."""
    instants = list(schedule.instants)
    open_instants, _final = instants[:-1], instants[-1]
    if not open_instants:
        raise ContractViolation("schedule must contain at least one open instant")
    books: dict[int, Any] = {}
    for instant in open_instants:
        raw = strategy.targets_at(instant, universe=universe, stress=stress)
        book = normalise_target_book(raw, decision_ns=instant, cap_max=cap_max)
        if book.status == STATUS_FORCE_FLAT:
            raise ContractViolation("an OPEN instant may not report FORCE_FLAT status")
        books[instant] = book
    return books


def _resolve_boundaries(
    strategy: ResearchStrategy,
    *,
    schedule: ImmutableSchedule,
    books: Mapping[int, Any],
    stress: StressSpec,
    gap_instants: set[int],
) -> list[dict[str, Any]]:
    """Turn books + strict-later fills into boundary transitions.

    ``gap_instants`` are the schedule edges no fold claims (the purge gaps and
    the trailing force-flat edge). Books never OPEN there: holdings carry
    through the gap unchanged, so a position opened inside a fold is always
    closed inside the same fold -- the purge/embargo contract holds by
    construction and the runner refuses any spill (see
    ``_account_boundaries``).
    """
    instants = list(schedule.instants)
    current: dict[str, float] = {}
    boundaries: list[dict[str, Any]] = []
    for index, instant in enumerate(instants):
        is_final = index == len(instants) - 1
        fills: tuple[FillRecord, ...] = ()
        action: str
        carry = False
        if not is_final and int(instant) in gap_instants:
            action = ACTION_PURGE_GAP_CARRY
            carry = True
            boundaries.append(
                {
                    "index": index,
                    "decision_ns": int(instant),
                    "action": action,
                    "carry_forward": carry,
                    "prior_weights": dict(current),
                    "target_weights": dict(current),
                    "fills": [],
                    "purge_gap": True,
                }
            )
            continue
        if is_final:
            action = STATUS_FORCE_FLAT
            target: dict[str, float] = {}
            if current:
                fills = strategy.fills_at(
                    instant, symbols=sorted(current), stress=stress
                )
        else:
            book = books[instant]
            if book.carried_forward:
                action = ACTION_CARRY
                carry = True
                target = dict(current)
            else:
                proposal = book.as_mapping()
                fills = strategy.fills_at(
                    instant,
                    symbols=sorted(set(proposal) | set(current)),
                    stress=stress,
                )
                if fills and all(record.applied for record in fills):
                    action = ACTION_OPEN
                    target = proposal
                else:
                    action = ACTION_OPEN_SKIPPED
                    carry = True
                    target = dict(current)
        boundaries.append(
            {
                "index": index,
                "decision_ns": int(instant),
                "action": action,
                "carry_forward": carry,
                "prior_weights": dict(current),
                "target_weights": dict(target),
                "fills": list(fills),
                "purge_gap": False,
            }
        )
        current = dict(target)
    if boundaries[-1]["action"] != STATUS_FORCE_FLAT:
        raise ContractViolation("final boundary must be the force-flat edge")
    if any(row["purge_gap"] and row["target_weights"] != row["prior_weights"] for row in boundaries):
        raise ContractViolation(PURGE_GAP_ENTRY_FORBIDDEN)
    return boundaries


def _boundary_stamp(boundary: Mapping[str, Any]) -> int:
    """Accounting stamp of a boundary: first applied fill-open else the instant."""
    stamps = [
        int(record.fill_open_ns)
        for record in boundary["fills"]
        if record.applied and record.fill_open_ns is not None
    ]
    return min(stamps) if stamps else int(boundary["decision_ns"])


def _marks_or_fail(
    strategy: ResearchStrategy, symbols: Sequence[str], instant_ns: int
) -> dict[str, Optional[float]]:
    observed = strategy.marks_at(list(symbols), int(instant_ns))
    for sym in symbols:
        if sym not in observed:
            raise DataUnavailable(f"mark missing for {sym} at {instant_ns}")
    return dict(observed)


def _prices_for_boundary(
    strategy: ResearchStrategy,
    *,
    symbols: Sequence[str],
    boundary: Mapping[str, Any],
    instant_ns: int,
) -> dict[str, float]:
    """Fill prices take precedence; valuation marks cover untouched legs."""
    prices: dict[str, float] = {}
    pending: list[str] = []
    for record in boundary["fills"]:
        if record.applied and record.price is not None:
            prices[record.symbol] = float(record.price)
    for sym in symbols:
        if sym not in prices:
            pending.append(str(sym))
    if pending:
        observed = _marks_or_fail(strategy, pending, instant_ns)
        for sym, price in observed.items():
            if price is None:
                raise DataUnavailable(f"valuation mark unavailable for {sym} at {instant_ns}")
            prices[sym] = float(price)
    for sym, price in prices.items():
        if not math.isfinite(price) or price <= 0.0:
            raise DataUnavailable(f"invalid price {price!r} for {sym} at {instant_ns}")
    return prices


def _account_boundaries(
    strategy: ResearchStrategy,
    *,
    identity: StrategyIdentity,
    fold_by_instant: Mapping[int, Any],
    boundaries: Sequence[Mapping[str, Any]],
    books: Mapping[int, Any],
    stress: StressSpec,
) -> tuple[list[ClosedPosition], list[DailyRealizedRow], list[dict[str, Any]]]:
    """Realized after-cost/funding ledger across the whole schedule."""
    if len(identity.window_start_iso) < 4 or len(identity.window_end_iso) < 4:
        raise ContractViolation("identity window edges must be ISO strings")
    live: dict[str, dict[str, float]] = {}
    previous_stamp: Optional[int] = None
    positions: list[ClosedPosition] = []
    daily_rows: list[DailyRealizedRow] = []
    payload_rows: list[dict[str, Any]] = []

    for boundary in boundaries:
        instant = int(boundary["decision_ns"])
        prior = dict(boundary["prior_weights"])
        target = dict(boundary["target_weights"])
        touched = sorted(
            {sym for sym, w in prior.items() if float(w) != 0.0}
            | {sym for sym, w in target.items() if float(w) != 0.0}
        )
        prices = (
            {}
            if not touched
            else _prices_for_boundary(
                strategy, symbols=touched, boundary=boundary, instant_ns=instant
            )
        )
        fold = _fold_for_instant(fold_by_instant, instant)
        stamp = _boundary_stamp(boundary)

        # -- settle/closed legs ------------------------------------------------
        closed_now: dict[str, ClosedPosition] = {}
        price_sum = 0.0
        funding_sum = 0.0
        if live and previous_stamp is not None:
            spans = [
                PositionSpan(sym, float(entry["weight"]), int(previous_stamp), int(stamp))
                for sym, entry in sorted(live.items())
            ]
            flows = strategy.funding_cashflows_for_spans(spans)
            funding_by_symbol: dict[str, float] = {}
            for flow in flows:
                funding_by_symbol[str(flow["symbol"])] = funding_by_symbol.get(
                    str(flow["symbol"]), 0.0
                ) + float(flow["cashflow_per_unit_capital"])
            funding_sum = math.fsum(funding_by_symbol.values())
            for sym, entry in sorted(live.items()):
                weight = float(entry["weight"])
                entry_px = float(entry["entry_price"])
                exit_px = float(prices[sym])
                position = ClosedPosition(
                    symbol=str(sym),
                    fold_index=int(entry["fold_index"]),
                    fold_label=str(entry["fold_label"]),
                    entry_ns=int(entry["entry_ns"]),
                    exit_ns=int(stamp),
                    signed_weight=weight,
                    entry_price=entry_px,
                    exit_price=exit_px,
                    price_pnl_per_unit=round(weight * (exit_px / entry_px - 1.0), 12),
                    funding_cashflow_per_unit=round(
                        funding_by_symbol.get(sym, 0.0), 12
                    ),
                    cost_allocated_per_unit=float(entry["cost_allocated"]),
                )
                if closing_allocation:
                    position = dataclasses.replace(
                        position,
                        cost_allocated_per_unit=round(
                            float(position.cost_allocated_per_unit)
                            + float(closing_allocation.get(sym, 0.0)),
                            12,
                        ),
                    )
                positions.append(position)
                closed_now[sym] = position
                price_sum += position.price_pnl_per_unit
                if entry["is_new_entry"] and (
                    int(entry["fold_index"]) != int(fold.index)
                    or str(entry["fold_label"]) != str(fold.label)
                ):
                    raise ContractViolation(
                        f"cross-fold holding for {sym}: established in fold "
                        f"{entry['fold_index']}/{entry['fold_label']} but closed in "
                        f"fold {fold.index}/{fold.label} "
                        f"({position.entry_ns}->{position.exit_ns}); purge/embargo "
                        "must cover the holding horizon"
                    )

        # -- turnover cost of this transition ---------------------------------
        cost_charged = strategy.rebalance_cost_between(
            prior, target, prices=prices, stress=stress
        )
        # Entry costs attach to the book being established; a liquidating
        # transition (force-flat) attaches pro-rata to the legs being closed.
        opens_new_book = any(abs(float(w)) > WEIGHT_TOL for w in target.values())
        allocation = allocate_cost_to_legs(
            cost_charged, target if opens_new_book else prior
        )
        closing_allocation = {} if opens_new_book else allocation

        # -- rebuild the live book --------------------------------------------
        live = {
            str(sym): {
                "weight": float(weight),
                "entry_price": float(prices[str(sym)]),
                "entry_ns": int(stamp),
                "fold_index": int(fold.index),
                "fold_label": str(fold.label),
                "cost_allocated": float(allocation.get(str(sym), 0.0)),
                "is_new_entry": abs(
                    float(weight) - float(prior.get(str(sym), 0.0))
                )
                > WEIGHT_TOL,
            }
            for sym, weight in sorted(target.items())
            if float(weight) != 0.0
        }
        previous_stamp = int(stamp)

        book = books.get(instant)
        gross_realised = math.fsum(abs(float(w)) for w in target.values())
        daily_rows.append(
            DailyRealizedRow(
                decision_ns=int(instant),
                fold_index=int(fold.index),
                fold_label=str(fold.label),
                price_pnl_per_unit=round(price_sum, 12),
                funding_cashflow_per_unit=round(funding_sum, 12),
                cost_charged_per_unit=round(float(cost_charged), 12),
                gross_realised=round(gross_realised, 12),
            )
        )
        payload_rows.append(
            fill_payload_row(
                decision_ns=int(instant),
                action=str(boundary["action"]),
                book=book,
                fills=list(boundary["fills"]),
                prior_weights=prior,
                new_weights=target,
                cost_charged=float(cost_charged),
                carry_forward=bool(boundary["carry_forward"]),
            )
        )
        del closed_now
    if not daily_rows:
        raise ContractViolation("no realized records produced")
    return positions, daily_rows, payload_rows


def _fold_for_instant(fold_by_instant: Mapping[int, Any], instant: int) -> Any:
    owner = fold_by_instant.get(int(instant))
    if owner is None:
        raise ContractViolation(f"instant {instant} has no attribution bucket")
    return owner


# --------------------------------------------------------------------------- #
# Validation helpers
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Deterministic artifact emission
# --------------------------------------------------------------------------- #
def write_cell_artifacts(result: Mapping[str, Any], *, root: str | Path) -> dict[str, str]:
    """Atomic JSON artifacts under uniquely-named result/shard/log roots."""
    root_path = Path(root)
    results_dir = root_path / "results"
    shards_dir = root_path / "shards" / Path(str(root_path)).name
    log_path = root_path / "logs" / f"{root_path.name}.log"
    manifest = {"artifact_kind": "adapter_v10_cell_log", "producer_role": "G1"}
    payload = dict(result)
    payload.pop("artifacts", None)
    written = atomic_write_json(payload, results_dir / "artifact.json")
    shard_written = atomic_write_json(manifest, shards_dir / "shard.json")
    logs_dir = log_path.parent
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_text = (
        f"adapter_v10 cell={Path(str(root_path)).name} "
        f"result_sha256={payload['hashes']['result_sha256']}\n"
    )
    log_path.write_text(log_text, encoding="utf-8")
    return {
        "artifact": str(written),
        "shard": str(shard_written),
        "log": str(log_path),
    }


def _strip(payload: Mapping[str, Any], keys: Sequence[str]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k not in set(keys)}
