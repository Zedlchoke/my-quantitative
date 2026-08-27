"""THIN plugin that joins the A8 panel family to the generic adapter (G1).

This file is the ONLY family-aware module in the lane: it wraps existing
``research.hyp_a8_m01`` primitives without editing them, so the panel module
keeps its frozen contract while participating in the generic pipeline:

* schedule  -> ``hyp_a8_m01.decision_days``
* folds     -> ``hyp_a8_m01.chronological_folds`` (purge + drop-one-fold)
* targets   -> ``hyp_a8_m01.compute_targets`` over ``symbol_day_feature``
* fills     -> ``hyp_a8_m01.resolve_fill_event`` (strict-later event clock)
* universe  -> ``hyp_a8_m01.apply_stress_filter`` (drop-one-symbol)
* costs     -> ``hyp_a8_m01.rebalance_cost`` / ``fill_cost_rate``
* funding   -> ``hyp_a8_m01.funding_cashflows`` over native ``HoldingSpan``s
* marks     -> ``hyp_a8_m01.resolve_fill_event`` covering-bar open price

Bars are injected at construction time (synthetic fixtures or a pre-window
catalog read); this plugin never reads real data itself and never scores.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

import research.hyp_a8_m01 as m01
from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    ContractViolation,
    CostModel,
    FillRecord,
    FillStatusVocabulary,
    FoldSpec,
    ImmutableSchedule,
    PositionSpan,
    SettlementPoint,
    StrategyIdentity,
    StressSpec,
)
from research.contract_v10 import FILL_CLOCK_V10, MIN_FOLDS_V10


def _point_payload(point: Any) -> dict[str, Any]:
    """Native settlement row accepted by the panel's PIT normaliser."""
    return {
        "publish_ts_ns": int(point.publish_ts_ns),
        "value": float(point.value),
        "kind": str(getattr(point, "kind", "info")),
    }


class M01Plugin(GenericStrategyBase):
    """Adapter-facing view of one configured A8 panel arm."""

    def __init__(
        self,
        *,
        bars_by_symbol: Mapping[str, Sequence[m01.M01Bar]],
        window_start_iso: str,
        window_end_iso: str,
        control_mode: str = m01.CONTROL_ANCHOR,
        neighbour_mode: str = m01.NEIGHBOUR_CROSS_SECTIONAL_Z,
        prewindow_sigma: Optional[Mapping[str, Optional[float]]] = None,
        min_eligible: int = m01.MIN_ELIGIBLE,
        cap: float = m01.CAP,
        gross: float = m01.GROSS_TARGET,
        tick_sizes: Optional[Mapping[str, float]] = None,
        settle_points_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        require_all_fills: bool = True,
        context_only_symbols: Sequence[str] = (),
    ) -> None:
        if not bars_by_symbol:
            raise ContractViolation("M01Plugin needs at least one symbol of bars")
        self._bars: dict[str, tuple[m01.M01Bar, ...]] = {
            str(sym): tuple(bars) for sym, bars in sorted(bars_by_symbol.items())
        }
        #: Data-backed symbols reserved for benchmark context (never tradeable).
        self._context_only = {str(s) for s in context_only_symbols}
        unknown_context = sorted(self._context_only - set(self._bars))
        if unknown_context:
            raise ContractViolation(
                f"context-only symbols have no injected bars: {unknown_context}"
            )
        pinned = str(m01.BENCHMARK_SYMBOL_EXCLUDED)
        if pinned not in self._context_only:
            raise ContractViolation(
                f"the pinned benchmark leg {pinned} must be declared context-only"
            )
        self._window_start_iso = str(window_start_iso)
        self._window_end_iso = str(window_end_iso)
        self._control_mode = str(control_mode)
        self._neighbour_mode = str(neighbour_mode)
        self._prewindow_sigma = (
            None if prewindow_sigma is None else dict(prewindow_sigma)
        )
        self._min_eligible = int(min_eligible)
        self._cap = float(cap)
        self._gross = float(gross)
        self._tick_sizes = {str(k): float(v) for k, v in (tick_sizes or {}).items()}
        self._settlements = {
            str(k): tuple(v) for k, v in (settle_points_by_symbol or {}).items()
        }
        self._require_all_fills = bool(require_all_fills)

    # ------------------------------------------------------------------ #
    # Identity / costs / schedule
    # ------------------------------------------------------------------ #
    def identity(self) -> StrategyIdentity:
        return StrategyIdentity(
            strategy_id="a8_panel_family",
            family_id=m01.FAMILY_ID,
            arm_config_id=self._control_mode,
            direction="BOTH_WITH_SIGN_SEMANTICS",
            window_start_iso=self._window_start_iso,
            window_end_iso=self._window_end_iso,
            benchmark_symbols_excluded=(m01.BENCHMARK_SYMBOL_EXCLUDED,),
            funding_sign_convention=m01.FUNDING_SIGN_CONVENTION,
            config={
                "neighbour_mode": self._neighbour_mode,
                "min_eligible": self._min_eligible,
                "cap": self._cap,
                "gross": self._gross,
                "require_all_fills": self._require_all_fills,
            },
        )

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=float(m01.TAKER_FEE_FLOOR_BPS),
            adverse_tick_slip_floor=int(m01.ADVERSE_TICK_SLIP_FLOOR),
            default_tick_sizes=dict(self._tick_sizes),
        )

    def baseline_stress(self) -> StressSpec:
        return super().baseline_stress()

    def tradeable_universe(self) -> tuple[str, ...]:
        return tuple(sorted(set(self._bars) - self._context_only))

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable cohort PLUS the pinned context-only benchmark leg."""
        return tuple(sorted(set(self.tradeable_universe()) | self._context_only))

    def schedule(self) -> ImmutableSchedule:
        instants = m01.decision_days(
            window_start_iso=self._window_start_iso,
            window_end_iso=self._window_end_iso,
        )
        return ImmutableSchedule(
            instants=tuple(int(v) for v in instants),
            source=f"{m01.__name__}.decision_days",
            clock=FILL_CLOCK_V10,
        )

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        params = self._stress_params(stress)
        purge_days = int(self.purge_days())
        full = m01.chronological_folds(
            list(instants), folds=int(self.fold_count()), purge_days=purge_days
        )
        survivors = {
            str(label)
            for _idx, label, _members in m01.chronological_folds(
                list(instants),
                folds=int(self.fold_count()),
                purge_days=purge_days,
                stress=params,
            )
        }
        return tuple(
            FoldSpec(
                index=int(idx),
                label=str(label),
                instants=tuple(members),
                purge_days=purge_days,
                dropped=str(label) not in survivors,
            )
            for idx, label, members in full
        )

    def fold_count(self) -> int:
        return int(MIN_FOLDS_V10)

    # ------------------------------------------------------------------ #
    # Targets / fills / marks
    # ------------------------------------------------------------------ #
    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        features = {
            str(sym): m01.symbol_day_feature(
                self._bars.get(str(sym)) or (),
                str(sym),
                int(instant_ns),
                prewindow_sigma=(
                    None
                    if self._prewindow_sigma is None
                    else self._prewindow_sigma.get(str(sym))
                ),
                require_prewindow_sigma=(self._neighbour_mode == m01.NEIGHBOUR_PREWINDOW_DISPERSION),
            )
            for sym in universe
        }
        return m01.compute_targets(
            features=features,
            control_mode=self._control_mode,
            neighbour_mode=self._neighbour_mode,
            prewindow_sigma=self._prewindow_sigma,
            min_eligible=self._min_eligible,
            cap=self._cap,
            gross=self._gross,
        )

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        params = self._stress_params(stress)
        out: list[FillRecord] = []
        for sym in sorted(set(symbols)):
            event = m01.resolve_fill_event(
                self._bars.get(sym) or (),
                sym,
                decision_ns=int(instant_ns),
                event_delay_events=params.event_delay_events,
            )
            if event is None:
                out.append(FillRecord(symbol=sym, decision_ns=int(instant_ns)))
            else:
                out.append(
                    FillRecord(
                        symbol=sym,
                        decision_ns=int(instant_ns),
                        status=FillStatusVocabulary.APPLIED,
                        applied=True,
                        price=float(event.price),
                        fill_open_ns=int(event.fill_open_ns),
                        fill_bar_close_ns=int(event.fill_bar_close_ns),
                        event_offset=int(event.event_offset),
                    )
                )
        return tuple(out)

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        out: dict[str, Optional[float]] = {}
        for sym in sorted(set(symbols)):
            bar = self._covering_bar(sym, int(instant_ns))
            out[sym] = None if bar is None else float(bar.open)
        return out

    def _covering_bar(self, symbol: str, instant_ns: int):
        for bar in self._bars.get(symbol) or ():
            if m01.bar_open_ns(bar) <= instant_ns < int(bar.ts_event_ns):
                return bar
        return None

    # ------------------------------------------------------------------ #
    # Costs / funding
    # ------------------------------------------------------------------ #
    def rebalance_cost_between(
        self,
        previous: Mapping[str, float],
        new: Mapping[str, float],
        *,
        prices: Mapping[str, float],
        stress: StressSpec,
    ) -> float:
        params = self._stress_params(stress)
        try:
            return float(
                m01.rebalance_cost(
                    dict(previous),
                    dict(new),
                    prices={str(k): float(v) for k, v in prices.items()},
                    tick_sizes=dict(self._tick_sizes),
                    stress=params,
                )
            )
        except m01.SpecViolation as exc:  # fail closed with the adapter error type
            raise ContractViolation(str(exc)) from exc

    def _native_points(self, symbol: str):
        """Panel-native settlement series (validated through the shared PIT hook)."""
        raw = self._settlements.get(str(symbol), ())
        native = [
            dict(point) if isinstance(point, Mapping) else _point_payload(point)
            for point in raw
        ]
        return m01.normalize_settlements(native)

    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        return tuple(
            SettlementPoint(publish_ts_ns=int(p.publish_ts_ns), value=float(p.value))
            for p in self._native_points(str(symbol))
        )

    def funding_cashflows_for_spans(self, spans: Sequence[PositionSpan]) -> list[dict[str, Any]]:
        """Delegate to the panel's own native accrual primitive.

        Per-symbol series are normalised and accrued separately (a merged
        series across symbols would trip the strict duplicate-stamp check on
        shared settlement instants).
        """
        out: list[dict[str, Any]] = []
        symbols = sorted({span.symbol for span in spans})
        for symbol in symbols:
            legs = [
                m01.HoldingSpan(
                    symbol=span.symbol,
                    signed_weight=float(span.signed_weight),
                    start_ns=int(span.start_ns),
                    end_ns=int(span.end_ns),
                )
                for span in spans
                if span.symbol == symbol
            ]
            if not legs:
                continue
            flows = m01.funding_cashflows(legs, self._native_points(symbol))
            out.extend(
                {
                    "symbol": flow.symbol,
                    "publish_ts_ns": int(flow.settle_ts_ns),
                    "rate": float(flow.rate),
                    "signed_weight": float(flow.signed_weight),
                    "cashflow_per_unit_capital": float(flow.cashflow_per_unit_capital),
                    "sign_convention": flow.sign_convention,
                }
                for flow in flows
            )
        out.sort(key=lambda row: (row["publish_ts_ns"], row["symbol"]))
        return out

    # ------------------------------------------------------------------ #
    # Stress plumbing -> panel parameter object
    # ------------------------------------------------------------------ #
    def _stress_params(self, stress: StressSpec) -> m01.StressParams:
        return m01.StressParams(
            fee_multiplier=float(stress.fee_multiplier),
            tick_slip_ticks=int(stress.tick_slip_ticks),
            event_delay_events=int(stress.event_delay_events),
            drop_symbols=tuple(str(s) for s in stress.drop_symbols),
            dropped_fold_index=None if stress.dropped_fold_index is None else int(stress.dropped_fold_index),
        )


__all__ = ["M01Plugin"]
