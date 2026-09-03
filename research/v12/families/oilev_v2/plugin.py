"""Adapter plugin joining A12-V12-OILEVER-V2-DELEV to the generic adapter.

THIN family-specific plugin (the lane's only family-aware wiring module):
it wraps the frozen primitives in
:mod:`research.v12.families.oilev_v2.strategy` without re-implementing any
adapter semantics -- universe filtering, drop-one stress, baseline cell
construction, fold assembly and the LONG_PAYS_POSITIVE_RATE funding
accrual all come from
:class:`research.adapter_v10.base.GenericStrategyBase`.

Data is injected at construction time (synthetic fixtures or a pre-window
read of the read-only workspace snapshot; see ``audits.py`` for the
audit-only loaders).  This plugin never reads real data itself and never
scores.  The three frozen arms (anchor / neighbour / causal negative
control) are three plugin instances of this one class, differing only in
``arm_id``.

Frozen adapter surface:

* identity -- the frozen V12 identity (strategy/family/arm ids, the
  recorded per-arm ``config`` dict, benchmark exclusion ``("BTCUSDT",)``,
  funding sign ``LONG_PAYS_POSITIVE_RATE``, matrix cohort hint ``v12``);
* tradeable universe -- the injected non-benchmark names (19 on the
  staged snapshot); the minimum tradeable names floor is the frozen
  ``min_eligible`` (9), so any stress that thins the cohort below the
  book's breadth requirement fails closed;
* schedule -- weekly Monday 00:00:00Z decision stamps over the frozen
  window (52 stamps) with the ONE declared execution lag: fills at the
  open of the 15m bar covering the decision instant;
* folds -- the pinned chronological F0/F1/F2 force-flat folds with the
  frozen 1-stamp purge; the contract ACCEPTS a dropped fold (probe
  friendly for the L-V11-1 per-family cell-matrix derivation);
* funding -- native per-symbol settlements with the inherited
  LONG_PAYS_POSITIVE_RATE accrual (a settlement accrues on a holding
  span iff its timestamp lies inside the span per the adapter's frozen
  rule).
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
    Bar,
    covering_bar,
    resolve_fill_event,
)
from research.v12.families.oilev_v2.strategy import (
    ADVERSE_TICK_SLIP_FLOOR,
    ARM_ROLES,
    BENCHMARK_SYMBOL,
    CAP_MAX,
    DECISION_CLOCK,
    FILL_CLOCK,
    MIN_ELIGIBLE,
    PURGE_DAYS,
    TAKER_FEE_FLOOR_BPS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    compute_targets_at,
    fold_assignments,
    frozen_identity,
    purge_fold_members,
    stamp_calendar,
)

PLUGIN_SCHEMA = "v12i.oilev_v2.plugin.v1"

#: The frozen one declared execution lag (documented; the fill resolver
#: itself takes the FIRST allowed execution event after availability).
DECLARED_EXECUTION_LAG = (
    "fill at the open of the 15m bar covering the decision instant "
    "(first allowed execution event after availability); stress event "
    "delays walk strictly later completed bars"
)


class OilevV2Plugin(GenericStrategyBase):
    """Adapter-facing view of one configured OILEV-V2 frozen arm."""

    def __init__(
        self,
        *,
        arm_id: str,
        oi_by_symbol: Mapping[str, Sequence[tuple[int, float]]],
        bars_by_symbol: Optional[Mapping[str, Sequence[Bar]]] = None,
        settlements_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        tick_sizes: Optional[Mapping[str, float]] = None,
        benchmark_symbol: str = BENCHMARK_SYMBOL,
        context_only_symbols: Sequence[str] = (BENCHMARK_SYMBOL,),
        window_start_iso: str = WINDOW_START_ISO,
        window_end_iso: str = WINDOW_END_ISO,
        cap: float = CAP_MAX,
        gross: float = 1.0,
    ) -> None:
        arm_id = str(arm_id)
        if arm_id not in ARM_ROLES:
            raise ContractViolation(
                f"unknown arm_id {arm_id!r}; expected {sorted(ARM_ROLES)}"
            )
        if not oi_by_symbol:
            raise ContractViolation("plugin needs at least one symbol of OI rows")
        self._arm_id = arm_id
        self._oi: dict[str, tuple[tuple[int, float], ...]] = {
            str(sym): tuple((int(t), float(v)) for t, v in series)
            for sym, series in sorted(oi_by_symbol.items())
        }
        for sym, series in self._oi.items():
            if not series:
                raise ContractViolation(f"symbol {sym} injected an empty OI series")
            times = [t for t, _ in series]
            if list(times) != sorted(set(times)):
                raise ContractViolation(
                    f"OI series for {sym} must be strictly increasing"
                )
        self._bars: dict[str, tuple[Bar, ...]] = {
            str(sym): tuple(bars)
            for sym, bars in sorted((bars_by_symbol or {}).items())
            if bars
        }
        missing_bars = sorted(set(self._oi) - set(self._bars))
        if missing_bars:
            raise ContractViolation(
                f"symbols without injected completed bars: {missing_bars}"
            )
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
        if pinned in self._oi:
            raise ContractViolation(
                "the pinned benchmark leg can never be a tradeable candidate"
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
        """The FROZEN V12 identity of this arm (digest equality test-pinned)."""
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
        """Every injected OI candidate except the pinned benchmark leg."""
        return tuple(sorted(set(self._oi) - self._context_only))

    def minimum_tradeable_names(self) -> int:
        """The frozen breadth floor: the book needs >= min_eligible names."""
        return int(MIN_ELIGIBLE)

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable cohort PLUS the pinned context-only benchmark leg."""
        return tuple(sorted(set(self.tradeable_universe()) | self._context_only))

    def schedule(self) -> ImmutableSchedule:
        """Weekly Monday 00:00:00Z stamps; one declared execution lag."""
        return ImmutableSchedule(
            instants=tuple(stamp_calendar()),
            source=(
                "research.v12.families.oilev_v2.strategy.stamp_calendar "
                f"(V11 weekly_mondays reuse; {self._window_start_iso}.."
                f"{self._window_end_iso}; {DECISION_CLOCK})"
            ),
            clock=FILL_CLOCK,
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
        purged = purge_fold_members(
            fold_assignments(list(instants)), purge_days=self.purge_days()
        )
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
        """Frozen target book (EligibilityShortfall fail-closed on breadth)."""
        del stress  # the frozen feature/book carries no stress parameters
        return compute_targets_at(
            self._arm_id,
            oi_by_symbol=self._oi,
            stamp_ns=int(instant_ns),
            universe=universe,
            gross=self._gross,
        )

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        """Fill at the open of the bar covering the decision (frozen lag)."""
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
        """Valuation mark = open of the bar covering the instant."""
        out: dict[str, Optional[float]] = {}
        for sym in sorted(set(symbols)):
            bar = covering_bar(self._bars.get(sym) or (), int(instant_ns))
            out[sym] = None if bar is None else float(bar.open)
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
    "OilevV2Plugin",
    "PLUGIN_SCHEMA",
]
