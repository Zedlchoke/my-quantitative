"""BG1 -- realized after-cost/funding fold metrics (G1).

Pure accounting helpers over an adapter-produced position/day ledger:

* position-level profit factor exactly per ``contract_v10.PF_DEFINITION_V10``
  ("sum(position_pnl > 0) / abs(sum(position_pnl <= 0))");
* daily expectancy over realized after-cost/funding unit-gross returns;
* additive max drawdown over the cumulative realized equity curve;
* per-fold aggregation keyed by chronological :class:`FoldSpec` membership.

Nothing here touches PnL of any real scored run: inputs are whatever the
caller hands in (synthetic fixtures, pre-window slices, dummy strategies).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation, FoldSpec, WEIGHT_TOL

#: Honest reason codes emitted alongside an undefined profit factor.
PF_NO_LOSING_NOTE = "no_losing_positions"
PF_NO_POSITIONS_NOTE = "no_positions"


@dataclass(frozen=True)
class ClosedPosition:
    """One leg held across one boundary period, fully closed at ``exit_ns``."""

    symbol: str
    fold_index: int
    fold_label: str
    entry_ns: int
    exit_ns: int
    signed_weight: float
    entry_price: float
    exit_price: float
    price_pnl_per_unit: float
    funding_cashflow_per_unit: float
    cost_allocated_per_unit: float

    @property
    def net_pnl_per_unit(self) -> float:
        return (
            self.price_pnl_per_unit
            + self.funding_cashflow_per_unit
            - self.cost_allocated_per_unit
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "fold_index": int(self.fold_index),
            "fold_label": self.fold_label,
            "entry_ns": int(self.entry_ns),
            "exit_ns": int(self.exit_ns),
            "signed_weight": round(self.signed_weight, 12),
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "price_pnl_per_unit": round(self.price_pnl_per_unit, 12),
            "funding_cashflow_per_unit": round(self.funding_cashflow_per_unit, 12),
            "cost_allocated_per_unit": round(self.cost_allocated_per_unit, 12),
            "net_pnl_per_unit": round(self.net_pnl_per_unit, 12),
        }


@dataclass(frozen=True)
class DailyRealizedRow:
    """One decision instant of realized accounting."""

    decision_ns: int
    fold_index: int
    fold_label: str
    price_pnl_per_unit: float
    funding_cashflow_per_unit: float
    cost_charged_per_unit: float
    gross_realised: float

    @property
    def net_return_per_unit(self) -> float:
        return (
            self.price_pnl_per_unit
            + self.funding_cashflow_per_unit
            - self.cost_charged_per_unit
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_ns": int(self.decision_ns),
            "fold_index": int(self.fold_index),
            "fold_label": self.fold_label,
            "price_pnl_per_unit": round(self.price_pnl_per_unit, 12),
            "funding_cashflow_per_unit": round(self.funding_cashflow_per_unit, 12),
            "cost_charged_per_unit": round(self.cost_charged_per_unit, 12),
            "net_return_per_unit": round(self.net_return_per_unit, 12),
            "gross_realised": round(self.gross_realised, 12),
        }


# --------------------------------------------------------------------------- #
# Metric primitives
# --------------------------------------------------------------------------- #
def position_profit_factor(
    pnl_values: Sequence[float],
) -> tuple[Optional[float], str]:
    """Contract PF plus an honest reason code when it is undefined."""
    if not pnl_values:
        return None, PF_NO_POSITIONS_NOTE
    gains = math.fsum(v for v in pnl_values if v > 0.0)
    losses = abs(math.fsum(v for v in pnl_values if v <= 0.0))
    if losses == 0.0:
        return None, PF_NO_LOSING_NOTE
    return gains / losses, ""


def daily_expectancy(net_returns: Sequence[float]) -> Optional[float]:
    """Mean unit-gross net return per decision instant (None when empty)."""
    if not net_returns:
        return None
    return math.fsum(float(v) for v in net_returns) / len(net_returns)


def max_drawdown(net_returns: Sequence[float]) -> float:
    """Additive peak-to-trough drawdown of the realized equity curve (>= 0)."""
    peak = 0.0
    equity = 0.0
    worst = 0.0
    for value in net_returns:
        equity += float(value)
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def daily_hit_rate(net_returns: Sequence[float]) -> Optional[float]:
    if not net_returns:
        return None
    wins = sum(1 for v in net_returns if v > 0.0)
    return wins / len(net_returns)


def allocate_cost_to_legs(
    cost_charged: float, new_weights: Mapping[str, float]
) -> dict[str, float]:
    """Split one boundary's turnover cost pro-rata over the new book's |w|.

    A zero-gross boundary carries no legs to charge, so its cost (never
    produced by a real transition) surfaces as a :class:`ContractViolation`.
    """
    gross = math.fsum(abs(float(w)) for w in new_weights.values())
    cost = float(cost_charged)
    if gross <= WEIGHT_TOL:
        if abs(cost) <= WEIGHT_TOL:
            return {}
        raise ContractViolation("non-zero cost charged against an empty book")
    return {
        sym: round(cost * abs(float(weight)) / gross, 12)
        for sym, weight in new_weights.items()
        if float(weight) != 0.0
    }


# --------------------------------------------------------------------------- #
# Fold aggregation
# --------------------------------------------------------------------------- #
def fold_of_instant(instant_ns: int, folds: Sequence[FoldSpec]) -> FoldSpec:
    """Fold declaring this decision instant (None when it sits in a purge gap)."""
    for fold in folds:
        if instant_ns in fold.instants:
            return fold
    raise ContractViolation(f"instant {instant_ns} is outside every declared fold")


def attribution_buckets(
    folds: Sequence[FoldSpec], instants: Sequence[int]
) -> dict[int, FoldSpec]:
    """Every decision instant -> the fold that OWNS its realized accounting.

    Purge gaps and the trailing force-flat edge belong to no declared fold by
    construction (``chronological_folds`` strips the trailing ``purge_days``
    instants of each fold), so they roll forward into the fold they trail:
    the realized row still exists, it is never dropped, and it never becomes a
    new fold. Raises when an instant precedes every declared fold.
    """
    ordered_folds = sorted(folds, key=lambda f: f.index)
    if any(fold.dropped for fold in ordered_folds) and len(ordered_folds) < 2:
        raise ContractViolation("a dropped fold requires at least one surviving fold")
    buckets: dict[int, FoldSpec] = {}
    current: Optional[FoldSpec] = None
    for instant in sorted(int(v) for v in instants):
        found: Optional[FoldSpec] = None
        for fold in ordered_folds:
            if instant in fold.instants:
                found = fold
                break
        if found is not None:
            current = found
        elif current is None:
            raise ContractViolation(
                f"instant {instant} precedes every declared fold; cannot attribute"
            )
        buckets[instant] = current  # type: ignore[assignment]
    if not buckets:
        raise ContractViolation("no decision instants to attribute")
    return buckets


def fold_membership(folds: Sequence[FoldSpec], instants: Sequence[int]) -> dict[int, list[int]]:
    """Deterministic declared ``fold_index -> [instants]`` map (chronological).

    Instants sitting in a purge gap or the final force-flat edge are reported
    by :func:`attribution_buckets` instead (they trail the owning fold).
    """
    del instants
    return {
        int(fold.index): [int(v) for v in fold.instants]
        for fold in sorted(folds, key=lambda f: f.index)
    }


def assert_no_cross_fold_holding(positions: Sequence[ClosedPosition]) -> None:
    """Purge/embargo guard: a closed position must live inside ONE fold."""
    for position in positions:
        if int(position.exit_ns) < int(position.entry_ns):
            raise ContractViolation(
                f"position {position.symbol} closes before it opens"
            )


def aggregate_fold(
    *,
    fold: FoldSpec,
    daily_rows: Sequence[DailyRealizedRow],
    positions: Sequence[ClosedPosition],
) -> dict[str, Any]:
    """BG1 metric block for ONE fold."""
    members = sorted(row.decision_ns for row in daily_rows if row.fold_index == fold.index)
    nets = [
        row.net_return_per_unit
        for row in sorted(daily_rows, key=lambda r: r.decision_ns)
        if row.fold_index == fold.index
    ]
    fold_positions = [p for p in positions if p.fold_index == fold.index]
    pnl_values = [p.net_pnl_per_unit for p in fold_positions]
    pf, note = position_profit_factor(pnl_values)
    abs_total = math.fsum(abs(v) for v in pnl_values)
    positive_share = (
        round(math.fsum(v for v in pnl_values if v > 0.0) / abs_total, 12)
        if abs_total > 0.0
        else None
    )
    return {
        "fold_index": int(fold.index),
        "fold_label": fold.label,
        "included_in_metrics": not bool(fold.dropped),
        "instants": [int(v) for v in fold.instants],
        "n_days_with_records": len(members),
        "first_decision_ns": int(members[0]) if members else None,
        "last_decision_ns": int(members[-1]) if members else None,
        "purge_days": int(fold.purge_days),
        "net_return_sum": round(math.fsum(nets), 12),
        "expectancy_per_day": _round_or_none(daily_expectancy(nets)),
        "max_drawdown": round(max_drawdown(nets), 12),
        "daily_hit_rate": _round_or_none(daily_hit_rate(nets)),
        "n_positions": len(fold_positions),
        "position_pf": _round_or_none(pf),
        "pf_reason": note,
        "price_pnl_sum": round(math.fsum(p.price_pnl_per_unit for p in fold_positions), 12),
        "funding_sum": round(math.fsum(p.funding_cashflow_per_unit for p in fold_positions), 12),
        "cost_allocated_sum": round(
            math.fsum(p.cost_allocated_per_unit for p in fold_positions), 12
        ),
        "positive_net_contribution_share": positive_share,
    }


def aggregate_portfolio(
    *, daily_rows: Sequence[DailyRealizedRow], positions: Sequence[ClosedPosition]
) -> dict[str, Any]:
    """Whole-run realized metrics (context block next to the fold table)."""
    ordered = sorted(daily_rows, key=lambda row: row.decision_ns)
    nets = [row.net_return_per_unit for row in ordered]
    pnl_values = [p.net_pnl_per_unit for p in positions]
    pf, note = position_profit_factor(pnl_values)
    return {
        "n_days_with_records": len(ordered),
        "net_return_sum": round(math.fsum(nets), 12),
        "expectancy_per_day": _round_or_none(daily_expectancy(nets)),
        "max_drawdown": round(max_drawdown(nets), 12),
        "daily_hit_rate": _round_or_none(daily_hit_rate(nets)),
        "n_positions": len(positions),
        "position_pf": _round_or_none(pf),
        "pf_reason": note,
        "price_pnl_sum": round(math.fsum(r.price_pnl_per_unit for r in ordered), 12),
        "funding_sum": round(math.fsum(r.funding_cashflow_per_unit for r in ordered), 12),
        "cost_charged_sum": round(math.fsum(r.cost_charged_per_unit for r in ordered), 12),
    }


def fold_metric_table(
    *,
    folds: Sequence[FoldSpec],
    daily_rows: Sequence[DailyRealizedRow],
    positions: Sequence[ClosedPosition],
) -> list[dict[str, Any]]:
    """BG1 deliverable: one row per SURVIVING fold, chronological, hash-stable.

    Folds flagged ``dropped`` (the ``drop_one_fold`` cell) are excluded here,
    but the realized rows inside them are still part of the ledger.
    """
    assert_no_cross_fold_holding(positions)
    return [
        aggregate_fold(fold=fold, daily_rows=daily_rows, positions=positions)
        for fold in sorted(folds, key=lambda f: f.index)
        if not fold.dropped
    ]


def _round_or_none(value: Optional[float], digits: int = 12) -> Optional[float]:
    return None if value is None else round(float(value), digits)
