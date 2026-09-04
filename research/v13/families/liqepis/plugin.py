"""Adapter plugin joining A13-V13-A5-LIQEPIS to the generic adapter.

THIN family-specific plugin (the lane's only family-aware wiring module):
it wraps the frozen primitives in
:mod:`research.v13.families.liqepis.strategy` without re-implementing any
adapter semantics -- universe filtering under symbol-dropping stress,
baseline cell construction, fold assembly and the LONG_PAYS_POSITIVE_RATE
funding accrual all come from
:class:`research.adapter_v10.base.GenericStrategyBase`.

Data is injected at construction time (synthetic fixtures or a read-only
pre-load of the workspace snapshot; see ``audits.py`` for the audit-only
loaders).  This plugin never reads real data itself and never scores.  The
three frozen arms (anchor / neighbour / causal negative control) are three
plugin instances of this one class, differing only in ``arm_id``.

Frozen adapter surface:

* identity -- the frozen V13 identity (strategy/family/arm ids, the frozen
  per-arm ``config`` dict, benchmark exclusion ``("BTCUSDT",)``, funding
  sign ``LONG_PAYS_POSITIVE_RATE``, matrix cohort hint ``v13``);
* tradeable universe -- the injected non-benchmark names (19 on the staged
  snapshot); the minimum tradeable names floor is the frozen
  ``min_eligible`` (13), so any stress that thins the cohort below the
  tercile book's breadth requirement fails closed;
* schedule -- weekly Monday 00:00:00Z decision stamps over the frozen
  window (52 stamps, 51 effective after the 1-day purge) with the ONE
  declared execution lag: fills at the CLOSE of the first completed 15m
  bar strictly after the decision instant (00:15Z close; the +1-delay
  stress fills at the 00:30Z close);
* folds -- the pinned chronological F0/F1/F2 calendar folds with the
  1-day purge zone and force-flat boundaries; the contract ACCEPTS a
  dropped fold (probe friendly for the L-V11-1 per-family cell-matrix
  derivation);
* funding -- native per-symbol settlements with the inherited
  LONG_PAYS_POSITIVE_RATE accrual (a settlement accrues on a holding span
  iff its timestamp lies inside the span per the adapter's frozen rule
  ``start < ts <= end``).
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
from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    FILL_CLOCK_V10,
    TAKER_FEE_FLOOR_BPS_V10,
)
from research.pit_hooks_v10 import normalize_info_series
from research.v13.families.liqepis.frozen_identity import frozen_identity
from research.v13.families.liqepis.strategy import (
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    DECISION_CLOCK,
    MIN_ELIGIBLE,
    PURGE_DAYS,
    FusionBarSeries,
    compute_targets_at,
    effective_schedule,
    fold_assignments,
    next_allowed_close_fill,
    stamp_calendar,
)

PLUGIN_SCHEMA = "v13i.liqepis.plugin.v1"

#: Declared cost floors (contract_v10; identical to the inherited families).
TAKER_FEE_FLOOR_BPS = float(TAKER_FEE_FLOOR_BPS_V10)
ADVERSE_TICK_SLIP_FLOOR = int(ADVERSE_TICKS_SLIPPAGE_FLOOR_V10)

#: The frozen one declared execution lag (documented; the fill resolver
#: itself takes the FIRST allowed execution event after availability).
DECLARED_EXECUTION_LAG = (
    "fill at the close of the first completed 15m bar strictly after the "
    "decision stamp (Monday 00:15:00Z close); stress event delays walk "
    "strictly later completed bars (00:30:00Z close at +1 delay)"
)

#: The family's inherited stress cell (fee x1.5 / +2 adverse ticks / +1
#: event delay over the baseline; V12-inherited convention).
STRESS_CELL_NAME = "fee_x1_5_plus2ticks_plus1delay"


def family_stress_cell(baseline: StressSpec) -> StressSpec:
    """The family's frozen stress cell over a plugin's baseline spec."""
    return StressSpec(
        name=STRESS_CELL_NAME,
        fee_multiplier=1.5,
        tick_slip_ticks=int(baseline.tick_slip_ticks) + 2,
        event_delay_events=int(baseline.event_delay_events) + 1,
    )


class LiqepisPlugin(GenericStrategyBase):
    """Adapter-facing view of one configured LIQEPIS frozen arm."""

    def __init__(
        self,
        *,
        arm_id: str,
        bars_by_symbol: Mapping[str, FusionBarSeries],
        settlements_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        tick_sizes: Optional[Mapping[str, float]] = None,
        benchmark_symbol: str = BENCHMARK_SYMBOL,
        context_only_symbols: Sequence[str] = (BENCHMARK_SYMBOL,),
        window_start_iso: str = "2025-08-22T00:00:00Z",
        window_end_iso: str = "2026-08-21T00:00:00Z",
        cap: float = CAP_MAX,
        gross: float = 1.0,
    ) -> None:
        arm_id = str(arm_id)
        if arm_id not in ARM_ROLES:
            raise ContractViolation(
                f"unknown arm_id {arm_id!r}; expected {sorted(ARM_ROLES)}"
            )
        if not bars_by_symbol:
            raise ContractViolation("plugin needs at least one symbol of bars")
        self._arm_id = arm_id
        self._bars: dict[str, FusionBarSeries] = {
            str(sym): series for sym, series in sorted(bars_by_symbol.items())
        }
        self._context_only = {str(s) for s in context_only_symbols}
        pinned = str(benchmark_symbol)
        if pinned not in self._context_only:
            raise ContractViolation(
                f"the pinned benchmark leg {pinned} must be declared context-only"
            )
        unknown_context = sorted(self._context_only - set(self._bars))
        if unknown_context:
            raise ContractViolation(
                f"context-only symbols have no injected bars: {unknown_context}"
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

    # ------------------------------------------------------------------ #
    # Identity / costs
    # ------------------------------------------------------------------ #
    def identity(self):
        """The FROZEN V13 identity of this arm (digest equality test-pinned)."""
        return frozen_identity(self._arm_id)

    def cost_model(self) -> CostModel:
        """Generic adapter cost model on the frozen V10 floors."""
        return CostModel(
            taker_fee_bps=float(TAKER_FEE_FLOOR_BPS),
            adverse_tick_slip_floor=int(ADVERSE_TICK_SLIP_FLOOR),
            default_tick_sizes=dict(self._tick_sizes),
        )

    # ------------------------------------------------------------------ #
    # Universe / schedule / folds
    # ------------------------------------------------------------------ #
    def tradeable_universe(self) -> tuple[str, ...]:
        """Every injected bar candidate except the pinned benchmark leg."""
        return tuple(sorted(set(self._bars) - self._context_only))

    def minimum_tradeable_names(self) -> int:
        """The frozen breadth floor: the tercile book needs >= 13 names."""
        return int(MIN_ELIGIBLE)

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable cohort PLUS the pinned context-only benchmark leg."""
        return tuple(sorted(set(self.tradeable_universe()) | self._context_only))

    def schedule(self) -> ImmutableSchedule:
        """Weekly Monday 00:00:00Z stamps; one declared execution lag."""
        return ImmutableSchedule(
            instants=tuple(stamp_calendar()),
            source=(
                "research.v13.families.liqepis.strategy.stamp_calendar "
                f"({self._window_start_iso}..{self._window_end_iso}; "
                f"{DECISION_CLOCK})"
            ),
            clock=FILL_CLOCK_V10,
        )

    def declared_execution_lag(self) -> str:
        """The frozen one declared execution lag (documentation hook)."""
        return DECLARED_EXECUTION_LAG

    def fold_count(self) -> int:
        return 3

    def purge_days(self) -> int:
        return int(PURGE_DAYS)

    def fold_label(self, index: int) -> str:
        """Frozen fold labels F0/F1/F2 (pinned calendar windows)."""
        return f"F{int(index)}"

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        """Pinned F0/F1/F2 calendar folds; ACCEPTS a dropped fold (L-V11-1)."""
        out: list[FoldSpec] = []
        for index, label, members, _purged in fold_assignments(list(instants)):
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

    def effective_instants(self) -> tuple[int, ...]:
        """The effective (purge-applied) decision stamps of the frozen schedule."""
        effective, _purged = effective_schedule(stamp_calendar())
        return tuple(effective)

    # ------------------------------------------------------------------ #
    # Targets / fills / marks
    # ------------------------------------------------------------------ #
    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        """Frozen target book (EligibilityShortfall fail-closed on breadth)."""
        del stress  # the frozen signal/book carries no stress parameters
        return compute_targets_at(
            self._arm_id,
            bars_by_symbol=self._bars,
            stamp_ns=int(instant_ns),
            universe=universe,
            gross=self._gross,
        )

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        """Close-fill at the first completed 15m bar strictly after the stamp."""
        out: list[FillRecord] = []
        for sym in sorted(set(symbols)):
            event = next_allowed_close_fill(
                self._bars[sym],
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
                        fill_open_ns=int(event.fill_ns),
                        fill_bar_close_ns=int(event.fill_ns),
                        event_offset=int(event.event_offset),
                    )
                )
        return tuple(out)

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        """Valuation mark = close of the last completed bar at/before the instant."""
        import math

        out: dict[str, Optional[float]] = {}
        for sym in sorted(set(symbols)):
            series = self._bars.get(sym)
            if series is None:
                out[sym] = None
                continue
            mark = None
            try:
                last_idx = series.slot_index(int(instant_ns))
            except ContractViolation:
                out[sym] = None
                continue
            for idx in range(min(last_idx, series.close.shape[0] - 1), -1, -1):
                close = float(series.close[idx])
                if math.isfinite(close) and int(series.available_ns[idx]) <= int(
                    instant_ns
                ):
                    mark = close
                    break
            out[sym] = mark
        return out

    # ------------------------------------------------------------------ #
    # Funding (native, per-symbol; accrual inherited from the base)
    # ------------------------------------------------------------------ #
    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        """Native settlement points injected from the funding bundles."""
        raw = self._settlements_raw.get(str(symbol), ())
        points = normalize_info_series(
            [dict(p) if isinstance(p, Mapping) else p for p in raw]
        )
        return tuple(
            SettlementPoint(publish_ts_ns=int(p.publish_ts_ns), value=float(p.value))
            for p in points
        )


__all__ = [
    "DECLARED_EXECUTION_LAG",
    "LiqepisPlugin",
    "PLUGIN_SCHEMA",
    "STRESS_CELL_NAME",
    "family_stress_cell",
]
