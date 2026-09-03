"""Adapter plugin joining A8-V11-OILEVER-DELEV to the generic V10 adapter.

THIN family-specific plugin (the lane's only family-aware module): it wraps
the frozen primitives in :mod:`research.v11.families.oilever_delev.strategy`
without re-implementing any adapter semantics -- schedule, folds, universe
filtering, costs, funding and stress plumbing all come from
:class:`research.adapter_v10.base.GenericStrategyBase`.

Data is injected at construction time (synthetic fixtures or a pre-window
read of the staged read-only snapshot); this plugin never reads real data
itself and never scores.  The three frozen arms (anchor / neighbour / causal
negative control) are three plugin instances of this one class, differing
only in ``arm_id`` -- their identities reproduce the frozen
``selection_freeze.json`` digests exactly (test-pinned).
"""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    ContractViolation,
    CostModel,
    FillRecord,
    FillStatusVocabulary,
    FoldSpec,
    ImmutableSchedule,
    SettlementPoint,
    StressSpec,
)
from research.pit_hooks_v10 import normalize_info_series
from research.v11.families.oilever_delev.strategy import (
    ADVERSE_TICK_SLIP_FLOOR,
    ANCHOR_ARM,
    ARM_ROLES,
    Bar,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    FAMILY_ID,
    FILL_CLOCK,
    TAKER_FEE_FLOOR_BPS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    compute_targets_at,
    covering_bar,
    frozen_identity,
    purge_fold_members,
    resolve_fill_event,
    weekly_mondays,
    fold_assignments,
)

PLUGIN_SCHEMA = "v11i.oilever_delev.plugin.v1"


class OileverDelevPlugin(GenericStrategyBase):
    """Adapter-facing view of one configured OILEVER-DELEV frozen arm."""

    def __init__(
        self,
        *,
        arm_id: str,
        bars_by_symbol: Mapping[str, Sequence[Bar]],
        oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
        settlements_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        tick_sizes: Optional[Mapping[str, float]] = None,
        benchmark_symbol: str = BENCHMARK_SYMBOL,
        context_only_symbols: Sequence[str] = (BENCHMARK_SYMBOL,),
        window_start_iso: str = WINDOW_START_ISO,
        window_end_iso: str = WINDOW_END_ISO,
        cap: float = CAP_MAX,
        gross: float = 1.0,
        require_all_fills: bool = True,
    ) -> None:
        arm_id = str(arm_id)
        if arm_id not in ARM_ROLES:
            raise ContractViolation(f"unknown arm_id {arm_id!r}; expected {sorted(ARM_ROLES)}")
        if not bars_by_symbol:
            raise ContractViolation("plugin needs at least one symbol of bars")
        self._arm_id = arm_id
        self._bars: dict[str, tuple[Bar, ...]] = {
            str(sym): tuple(bars) for sym, bars in sorted(bars_by_symbol.items())
        }
        for sym, bars in self._bars.items():
            if not bars:
                raise ContractViolation(f"symbol {sym} injected an empty bar series")
        self._oi: dict[str, tuple[tuple[int, float], ...]] = {
            str(sym): tuple((int(t), float(v)) for t, v in series)
            for sym, series in sorted(oi_by_symbol.items())
        }
        missing_oi = sorted(set(self._bars) - set(self._oi))
        if missing_oi:
            raise ContractViolation(f"symbols without an injected OI series: {missing_oi}")
        for sym, series in self._oi.items():
            times = [t for t, _ in series]
            if list(times) != sorted(set(times)):
                raise ContractViolation(f"OI series for {sym} must be strictly increasing")
        self._context_only = {str(s) for s in context_only_symbols}
        unknown_context = sorted(self._context_only - set(self._bars))
        if unknown_context:
            raise ContractViolation(
                f"context-only symbols have no injected bars: {unknown_context}"
            )
        pinned = str(benchmark_symbol)
        if pinned not in self._context_only:
            raise ContractViolation(
                f"the pinned benchmark leg {pinned} must be declared context-only"
            )
        self._benchmark_symbol = pinned
        self._settlements_raw = {
            str(k): tuple(v) for k, v in (settlements_by_symbol or {}).items()
        }
        self._tick_sizes = {str(k): float(v) for k, v in (tick_sizes or {}).items()}
        self._window_start_iso = str(window_start_iso)
        self._window_end_iso = str(window_end_iso)
        self._cap = float(cap)
        self._gross = float(gross)
        self._require_all_fills = bool(require_all_fills)

    # ------------------------------------------------------------------ #
    # Identity / costs
    # ------------------------------------------------------------------ #
    def identity(self):
        """The FROZEN V11 identity of this arm (digest equality test-pinned)."""
        return frozen_identity(self._arm_id)

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=float(TAKER_FEE_FLOOR_BPS),
            adverse_tick_slip_floor=int(ADVERSE_TICK_SLIP_FLOOR),
            default_tick_sizes=dict(self._tick_sizes),
        )

    # ------------------------------------------------------------------ #
    # Universe / schedule / folds
    # ------------------------------------------------------------------ #
    def tradeable_universe(self) -> tuple[str, ...]:
        return tuple(sorted(set(self._bars) - self._context_only))

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable cohort PLUS the pinned context-only benchmark leg."""
        return tuple(sorted(set(self.tradeable_universe()) | self._context_only))

    def schedule(self) -> ImmutableSchedule:
        return ImmutableSchedule(
            instants=tuple(weekly_mondays(
                window_start_iso=self._window_start_iso,
                window_end_iso=self._window_end_iso,
            )),
            source=(
                "research.v11.families.oilever_delev.strategy.weekly_mondays"
                f"({self._window_start_iso}..{self._window_end_iso})"
            ),
            clock=FILL_CLOCK,
        )

    def fold_count(self) -> int:
        return 3

    def purge_days(self) -> int:
        return 1

    def fold_label(self, index: int) -> str:
        """Frozen fold labels F0/F1/F2 (pinned calendar windows)."""
        return f"F{int(index)}"

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        """Pinned F0/F1/F2 calendar folds with the frozen purge posture."""
        purged = purge_fold_members(fold_assignments(list(instants)), purge_days=self.purge_days())
        out: list[FoldSpec] = []
        for index, label, members, _gaps in purged:
            dropped = (
                stress.dropped_fold_index is not None
                and index == int(stress.dropped_fold_index)
            )
            out.append(
                FoldSpec(
                    index=int(index),
                    label=str(label),
                    instants=tuple(members),
                    purge_days=int(self.purge_days()),
                    dropped=bool(dropped),
                )
            )
        return tuple(out)

    # ------------------------------------------------------------------ #
    # Targets / fills / marks
    # ------------------------------------------------------------------ #
    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        del stress  # the frozen feature/book carries no stress parameters
        return compute_targets_at(
            self._arm_id,
            bars_by_symbol=self._bars,
            oi_by_symbol=self._oi,
            stamp_ns=int(instant_ns),
            universe=universe,
            gross=self._gross,
        )

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        out: list[FillRecord] = []
        for sym in sorted(set(symbols)):
            event = resolve_fill_event(
                self._bars.get(sym) or (),
                sym,
                decision_ns=int(instant_ns),
                event_delay_events=int(stress.event_delay_events),
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
            bar = covering_bar(self._bars.get(sym) or (), int(instant_ns))
            out[sym] = None if bar is None else float(bar.open)
        return out

    # ------------------------------------------------------------------ #
    # Funding (native, per-symbol)
    # ------------------------------------------------------------------ #
    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        raw = self._settlements_raw.get(str(symbol), ())
        points = normalize_info_series([dict(p) if isinstance(p, Mapping) else p for p in raw])
        return tuple(
            SettlementPoint(publish_ts_ns=int(p.publish_ts_ns), value=float(p.value))
            for p in points
        )


__all__ = ["ANCHOR_ARM", "OileverDelevPlugin", "PLUGIN_SCHEMA"]
