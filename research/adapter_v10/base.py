"""Reusable adapter plumbing shared by every strategy plugin (G1).

A plugin subclasses :class:`GenericStrategyBase` and supplies only its own
specifics (identity, cost floors, tradeable universe, targets, fills, marks,
settlements). Everything else -- baseline cell construction, drop-one-symbol
filtering, chronological fold assembly with purge + force-flat boundary, and
the long-pays-positive-rate funding accrual -- is provided once here and is
identical for every strategy, which is what makes the dummy strategy and any
panel-family plugin interchangeable in the tests.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence
import math

from research.adapter_v10.protocol import (
    ContractViolation,
    FoldSpec,
    ImmutableSchedule,
    PositionSpan,
    SettlementPoint,
    StressSpec,
)

BASELINE_NAME = "baseline"
FUNDING_SIGN_LONG_PAYS_POSITIVE = "LONG_PAYS_POSITIVE_RATE"


class GenericStrategyBase:
    """Partial :class:`research.adapter_v10.protocol.ResearchStrategy`."""

    # ------------------------------------------------------------------ #
    # Provided by the adapter layer
    # ------------------------------------------------------------------ #
    def cost_model(self):
        raise NotImplementedError("plugin must declare its cost model")

    def identity(self):
        raise NotImplementedError("plugin must declare its identity")

    def tradeable_universe(self) -> tuple[str, ...]:
        raise NotImplementedError("plugin must declare its tradeable universe")

    def minimum_tradeable_names(self) -> int:
        """Diversification floor applied AFTER any symbol-dropping stress."""
        return 2

    def baseline_stress(self) -> StressSpec:
        """Unstressed reference cell built from the plugin's own cost floors."""
        model = self.cost_model()
        return StressSpec(
            name=BASELINE_NAME,
            fee_multiplier=1.0,
            tick_slip_ticks=int(model.adverse_tick_slip_floor),
            event_delay_events=0,
            drop_symbols=(),
            dropped_fold_index=None,
        )

    def schedule(self) -> ImmutableSchedule:
        raise NotImplementedError("plugin must provide an immutable schedule")

    def universe(self, stress: StressSpec) -> tuple[str, ...]:
        """Tradeable names minus this cell's dropped symbols (fail closed)."""
        base = sorted(str(s) for s in self.tradeable_universe())
        dropped = [str(s) for s in stress.drop_symbols]
        unknown = sorted(set(dropped) - set(base))
        if unknown:
            raise ContractViolation(f"dropped symbols outside the cohort: {unknown}")
        survivors = tuple(sym for sym in base if sym not in set(dropped))
        if len(survivors) < self.minimum_tradeable_names():
            raise ContractViolation(
                f"stress {stress.name!r} leaves {len(survivors)} names < "
                f"{self.minimum_tradeable_names()}; book cannot stay diversified"
            )
        return survivors

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Context-only candidates; defaults to the tradeable universe."""
        return self.tradeable_universe()

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        """Generic contiguous chronological folds with purge >= holding span."""
        ordered = [int(v) for v in sorted(set(instants))]
        n_folds = max(1, int(self.fold_count()))
        purge_days = max(0, int(self.purge_days()))
        if len(ordered) < n_folds + 1:
            raise ContractViolation(
                f"cannot form {n_folds} folds with purge {purge_days} from {len(ordered)} instants"
            )
        edges = [round(i * len(ordered) / n_folds) for i in range(n_folds + 1)]
        out: list[FoldSpec] = []
        for index in range(n_folds):
            label = self.fold_label(index)
            stop = max(edges[index] + 1, edges[index + 1] - purge_days)
            members = tuple(ordered[edges[index]:stop])
            if not members:
                raise ContractViolation(f"fold {label} empty after purge={purge_days}")
            dropped = (
                stress.dropped_fold_index is not None
                and index == int(stress.dropped_fold_index)
            )
            out.append(
                FoldSpec(
                    index=index,
                    label=label,
                    instants=members,
                    purge_days=purge_days,
                    dropped=dropped,
                )
            )
        return tuple(out)

    def fold_label(self, index: int) -> str:
        return f"F{index + 1}"

    def fold_count(self) -> int:
        return 3

    def purge_days(self) -> int:
        return 1

    # ------------------------------------------------------------------ #
    # Turnover cost (per-side fee floor + adverse tick slippage)
    # ------------------------------------------------------------------ #
    def rebalance_cost_between(
        self,
        previous: Mapping[str, float],
        new: Mapping[str, float],
        *,
        prices: Mapping[str, float],
        stress: StressSpec,
    ) -> float:
        """Traded-notional cost of one transition under this cell's stress.

        Identical arithmetic to the repo's panel cost primitive: one-side
        traded notional charged once per side at
        ``taker_fee_bps * 1e-4 * fee_multiplier + ticks * tick_size / price``.
        A plugin may override to call its own frozen cost function instead.
        """
        model = self.cost_model()
        fee_rate = float(model.taker_fee_bps) * 1e-4 * float(stress.fee_multiplier)
        total = 0.0
        for sym in sorted(set(previous) | set(new)):
            delta = abs(float(new.get(sym, 0.0)) - float(previous.get(sym, 0.0)))
            if delta == 0.0:
                continue
            price = prices.get(sym)
            if price is None or not math.isfinite(float(price)) or float(price) <= 0.0:
                raise ContractViolation(f"missing/invalid fill price for {sym}")
            ticks = int(stress.tick_slip_ticks)
            rate = fee_rate
            if ticks:
                size = model.default_tick_sizes.get(sym)
                if size is None or float(size) <= 0.0:
                    raise ContractViolation(
                        f"tick slippage requested without a positive tick_size for {sym}"
                    )
                rate += ticks * float(size) / float(price)
            total += delta * rate
        return round(total, 12)

    # ------------------------------------------------------------------ #
    # Funding accrual (long pays positive rate) over held spans
    # ------------------------------------------------------------------ #
    def funding_sign_convention(self) -> str:
        return FUNDING_SIGN_LONG_PAYS_POSITIVE

    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        raise NotImplementedError("plugin must supply per-symbol native settlements")

    def funding_cashflows_for_spans(
        self, spans: Sequence[PositionSpan]
    ) -> list[dict[str, Any]]:
        """Accrue native settlements on legs held across each instant.

        Sign convention ``LONG_PAYS_POSITIVE_RATE`` means a LONG leg loses
        ``+rate`` of capital (cashflow negative) and a SHORT leg receives it.
        A plugin declaring a different convention MUST override this method.
        """
        if self.funding_sign_convention() != FUNDING_SIGN_LONG_PAYS_POSITIVE:
            raise ContractViolation(
                "unsupported funding sign convention; override funding_cashflows_for_spans"
            )
        flat: list[dict[str, Any]] = []
        for span in spans:
            weight = float(span.signed_weight)
            if weight == 0.0:
                continue
            for point in self._settlements_inside(span):
                flat.append(
                    {
                        "symbol": str(span.symbol),
                        "publish_ts_ns": int(point.publish_ts_ns),
                        "rate": float(point.value),
                        "signed_weight": weight,
                        "cashflow_per_unit_capital": round(
                            -weight * float(point.value), 12
                        ),
                        "sign_convention": self.funding_sign_convention(),
                    }
                )
        flat.sort(key=lambda row: (row["publish_ts_ns"], row["symbol"]))
        return flat

    def _settlements_inside(self, span: PositionSpan) -> list[SettlementPoint]:
        start, end = int(span.start_ns), int(span.end_ns)
        points = [p for p in self.settlements(str(span.symbol)) if start < p.publish_ts_ns <= end]
        seen: set[int] = set()
        for point in points:
            if point.publish_ts_ns in seen:
                raise ContractViolation(
                    f"duplicate settlement instant for {span.symbol}: {point.publish_ts_ns}"
                )
            seen.add(point.publish_ts_ns)
        points.sort(key=lambda p: p.publish_ts_ns)
        return points

    # ------------------------------------------------------------------ #
    # Marks fallback used when no fill traded a leg at one boundary
    # ------------------------------------------------------------------ #
    def marks_at(self, symbols: Sequence[str], instant_ns: int) -> dict[str, Optional[float]]:
        raise NotImplementedError("plugin must supply valuation marks")


__all__ = [
    "BASELINE_NAME",
    "FUNDING_SIGN_LONG_PAYS_POSITIVE",
    "GenericStrategyBase",
]
