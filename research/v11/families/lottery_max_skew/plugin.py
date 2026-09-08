"""Adapter plugin for the frozen V11-SEED-LOTTERY-MAX-SKEW family.

A thin :class:`research.adapter_v10.base.GenericStrategyBase` subclass: all
generic schedule/fold/cost/funding behaviour comes from the shared adapter
layer, and the family supplies only its frozen identity, cost floors,
schedule, PIT target books, strict-later fills, marks and native
settlements.  Nothing here forks shared code and nothing here scores.

The identity payload is BYTE-FROZEN: :func:`frozen_identity` reproduces the
``arm_config_digest`` values recorded in
``research/control/v11_run/selection_freeze.json`` (``frozen_cells``) and a
test asserts exact equality.
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

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
from research.contract_v10 import FILL_CLOCK_V10, TAKER_FEE_FLOOR_BPS_V10
from research.v11.families.lottery_max_skew.strategy import (
    BAR_NS,
    FEATURE_KIND_RESMAX,
    FEATURE_KIND_RESSKEW,
    FOLD_RANGES,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    BookDecision,
    DailyFrame,
    FeatureEngine,
    STATUS_OK,
    STATUS_SKIP_NO_SELECTION,
    build_quintile_book,
    day_index,
    fold_force_flat_instants,
    fold_of_instant,
)

# --------------------------------------------------------------------------- #
# Frozen family / arm vocabulary (selection_freeze_specs, verbatim)
# --------------------------------------------------------------------------- #
FAMILY_ID = "V11-SEED-LOTTERY-MAX-SKEW"
STRATEGY_ID = "V11-SEED-LOTTERY-MAX-SKEW.v1"
DIRECTION = "long_short_beta_neutral"
BENCHMARK_EXCLUDED = ("BTCUSDT",)
BENCHMARK_INSTRUMENT = "BTCUSDT-PERP.BINANCE"

ANCHOR_ARM = "LOT-RESMAX-7D-W"
NEIGHBOUR_ARM = "LOT-RESSKEW-30D-W"
CONTROL_ARM = "LOT-RESMAX-7D-W-INV"
ARM_IDS = (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM)

ROLE_BY_ARM = {
    ANCHOR_ARM: "anchor",
    NEIGHBOUR_ARM: "neighbour",
    CONTROL_ARM: "causal_negative_control",
}
FEATURE_KIND_BY_ARM = {
    ANCHOR_ARM: FEATURE_KIND_RESMAX,
    NEIGHBOUR_ARM: FEATURE_KIND_RESSKEW,
    CONTROL_ARM: FEATURE_KIND_RESMAX,
}
FORMATION_DAYS_BY_ARM = {
    ANCHOR_ARM: 7,
    NEIGHBOUR_ARM: 30,
    CONTROL_ARM: 7,  # control inherits anchor formation/holding (freeze note)
}
HOLDING_DAYS_BY_ARM = {
    ANCHOR_ARM: 7,
    NEIGHBOUR_ARM: 7,
    CONTROL_ARM: 7,
}
#: Frozen book descriptions (verbatim spec `book` strings; the control book
#: sign is inverted by the engine, its declared book text stays spec-frozen).
BOOK_BY_ARM = {
    ANCHOR_ARM: "low-minus-high residual-MAX quintiles",
    NEIGHBOUR_ARM: "low-minus-high residual-skew quintiles",
    CONTROL_ARM: "sign-inverted (high-minus-low)",
}
#: Frozen feature descriptions (verbatim spec `feature` strings; the control
#: inherits the anchor feature text with the anchor's formation/holding).
FEATURE_BY_ARM = {
    ANCHOR_ARM: "7d max daily BTC-residualised return (90d rolling beta)",
    NEIGHBOUR_ARM: "30d rolling skew of residual dailies",
    CONTROL_ARM: "7d max daily BTC-residualised return (90d rolling beta)",
}
#: Frozen falsification clauses (empty string where the spec declares none).
FALSIFICATION_BY_ARM = {
    ANCHOR_ARM: "",
    NEIGHBOUR_ARM: "",
    CONTROL_ARM: "positive after-cost spread on inverted book destroys mechanism",
}
DECISION_CLOCK_FROZEN = (
    "Mondays 00:00:00Z; features from completed 15m bars + last COMPLETED OI 5m "
    "row strictly before stamp; one declared execution lag after availability"
)
COSTS_FROZEN = (
    "generic adapter fees/slippage; native funding while held; stress = fee "
    "x1.5, +2 ticks, +1 event delay"
)
#: Frozen stress cell (freeze `common.costs`): fee x1.5, +2 ticks on the
#: declared floor, +1 fill event delay.
FROZEN_STRESS_NAME = "stress_fee_x1_5_plus_2_ticks_plus_1_delay"
FROZEN_STRESS_FEE_MULTIPLIER = 1.5
FROZEN_STRESS_EXTRA_TICKS = 2
FROZEN_STRESS_EVENT_DELAY = 1

ARM_INVERTED = {arm: arm.endswith("-INV") for arm in ARM_IDS}


def frozen_identity(arm_id: str) -> StrategyIdentity:
    """The byte-frozen :class:`StrategyIdentity` of one arm.

    Reproduces exactly the payload the selection freeze digested (A1 D3
    generator): strategy_id ``{family}.v1``, ``arm_config_id`` = the spec
    role, direction ``long_short_beta_neutral``, the BTC benchmark
    exclusion, and the whole frozen config mapping (feature / book /
    formation_days / holding_days / decision_clock / costs / falsification).
    """
    if arm_id not in ARM_IDS:
        raise ContractViolation(f"unknown frozen arm {arm_id!r}")
    return StrategyIdentity(
        strategy_id=STRATEGY_ID,
        family_id=FAMILY_ID,
        arm_config_id=ROLE_BY_ARM[arm_id],
        direction=DIRECTION,
        window_start_iso=WINDOW_START_ISO,
        window_end_iso=WINDOW_END_ISO,
        benchmark_symbols_excluded=BENCHMARK_EXCLUDED,
        arm_id=arm_id,
        config={
            "feature": FEATURE_BY_ARM[arm_id],
            "book": BOOK_BY_ARM[arm_id],
            "formation_days": FORMATION_DAYS_BY_ARM[arm_id],
            "holding_days": HOLDING_DAYS_BY_ARM[arm_id],
            "decision_clock": DECISION_CLOCK_FROZEN,
            "costs": COSTS_FROZEN,
            "falsification": FALSIFICATION_BY_ARM[arm_id],
        },
    )


def frozen_stress() -> StressSpec:
    """The freeze's named stress cell: fee x1.5, +2 ticks, +1 event delay."""
    return StressSpec(
        name=FROZEN_STRESS_NAME,
        fee_multiplier=FROZEN_STRESS_FEE_MULTIPLIER,
        tick_slip_ticks=1 + FROZEN_STRESS_EXTRA_TICKS,
        event_delay_events=FROZEN_STRESS_EVENT_DELAY,
        drop_symbols=(),
        dropped_fold_index=None,
    )


# --------------------------------------------------------------------------- #
# Injected market inputs
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class BarEvent:
    """One completed 15m bar used for fills/marks (close-stamped)."""

    ts_event_ns: int
    open: float
    close: float


def bar_open_ns(bar: BarEvent) -> int:
    """Derived OPEN stamp of a close-stamped bar (repo PIT convention)."""
    return int(bar.ts_event_ns) - BAR_NS


@dataclass(frozen=True)
class MarketInputs:
    """Everything the plugin needs, injected (synthetic fixtures or the
    read-only staged snapshot loaded by :mod:`...lottery_max_skew.data`)."""

    daily_by_symbol: Mapping[str, DailyFrame]
    bars_by_symbol: Mapping[str, Sequence[BarEvent]]
    settlements_by_symbol: Mapping[str, Sequence[SettlementPoint]]
    tick_sizes: Mapping[str, float]
    symbols: Sequence[str]


# --------------------------------------------------------------------------- #
# The plugin
# --------------------------------------------------------------------------- #
class LotteryMaxSkewPlugin(GenericStrategyBase):
    """Adapter-facing view of ONE frozen arm of the LOT family."""

    def __init__(self, *, arm_id: str, inputs: MarketInputs) -> None:
        if arm_id not in ARM_IDS:
            raise ContractViolation(f"unknown frozen arm {arm_id!r}")
        if not inputs.symbols:
            raise ContractViolation("plugin needs a non-empty staged symbol cohort")
        if BENCHMARK_INSTRUMENT not in inputs.daily_by_symbol:
            raise ContractViolation("benchmark BTC daily frame must be injected")
        missing_ticks = sorted(
            sym for sym in inputs.symbols if inputs.tick_sizes.get(sym) is None
        )
        if missing_ticks:
            raise ContractViolation(f"missing tick sizes for {missing_ticks}")
        self._arm_id = str(arm_id)
        self._inputs = inputs
        self._bars = {
            str(sym): tuple(sorted(inputs.bars_by_symbol[str(sym)], key=lambda b: b.ts_event_ns))
            for sym in inputs.symbols
        }
        self._bar_closes = {
            sym: [bar.ts_event_ns for bar in bars] for sym, bars in self._bars.items()
        }
        cached = build_cached_schedule()
        self._instants = cached
        # Static cohort disclosure: staged symbols whose bars END before the
        # first decision stamp are PIT-ineligible at every stamp (no bar,
        # ever) and are excluded from the tradeable cohort AND the benchmark
        # context candidates; every other staged symbol stays in and is
        # filtered per stamp by the PIT eligibility rules.
        self._statically_excluded: tuple[str, ...] = tuple(
            sorted(
                sym
                for sym, bars in self._bars.items()
                if not bars or bars[-1].ts_event_ns < int(cached[0])
            )
        )
        self._tradeable = tuple(
            sorted(
                sym
                for sym in inputs.symbols
                if sym not in self._statically_excluded
                and sym != BENCHMARK_INSTRUMENT
            )
        )
        if len(self._tradeable) < 10:
            raise ContractViolation(
                f"tradeable cohort too small after static disclosure: {len(self._tradeable)}"
            )
        self._bars = {
            sym: self._bars[sym]
            for sym in sorted(set(self._tradeable) | {BENCHMARK_INSTRUMENT})
        }
        self._bar_closes = {
            sym: [bar.ts_event_ns for bar in bars] for sym, bars in self._bars.items()
        }
        self._engine = FeatureEngine(
            daily_by_symbol=dict(inputs.daily_by_symbol),
            benchmark_symbol=BENCHMARK_INSTRUMENT,
            formation_days_by_arm=dict(FORMATION_DAYS_BY_ARM),
            feature_kind_by_arm=dict(FEATURE_KIND_BY_ARM),
        )
        self._force_flat = fold_force_flat_instants(self._instants)
        self._arm_spec = _arm_spec(arm_id)

    # ------------------------------------------------------------------ #
    # Frozen identity / costs / stress
    # ------------------------------------------------------------------ #
    def identity(self) -> StrategyIdentity:
        return frozen_identity(self._arm_id)

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=float(TAKER_FEE_FLOOR_BPS_V10),
            adverse_tick_slip_floor=1,
            default_tick_sizes={
                str(sym): float(self._inputs.tick_sizes[str(sym)])
                for sym in sorted(self._inputs.symbols)
            },
        )

    def baseline_stress(self) -> StressSpec:
        return super().baseline_stress()

    def frozen_stress(self) -> StressSpec:
        return frozen_stress()

    # ------------------------------------------------------------------ #
    # Universe / benchmark
    # ------------------------------------------------------------------ #
    def tradeable_universe(self) -> tuple[str, ...]:
        return self._tradeable

    @property
    def statically_excluded(self) -> tuple[str, ...]:
        """Staged symbols PIT-ineligible at every stamp (disclosed in C1)."""
        return self._statically_excluded

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable cohort PLUS the pinned context-only BTC benchmark leg.

        The frozen identity excludes the base token ``BTCUSDT``; the plugin
        resolves that alias to the staged instrument id in marks/fills.
        """
        return tuple(sorted(set(self._tradeable) | set(BENCHMARK_EXCLUDED)))

    def _resolve_symbol(self, symbol: str) -> Optional[str]:
        """Instrument id for a cohort member or the BTC benchmark alias."""
        if symbol in self._bars:
            return str(symbol)
        if str(symbol) + "-PERP.BINANCE" in self._bars:
            return str(symbol) + "-PERP.BINANCE"
        return None

    # ------------------------------------------------------------------ #
    # Schedule / folds (frozen clock and pinned F0/F1/F2 ranges)
    # ------------------------------------------------------------------ #
    def schedule(self) -> ImmutableSchedule:
        return ImmutableSchedule(
            instants=self._instants,
            source="research.v11.families.lottery_max_skew.strategy.build_schedule_instants",
            clock=FILL_CLOCK_V10,
        )

    def folds(self, *, stress: StressSpec, instants: Sequence[int]) -> tuple[FoldSpec, ...]:
        """The freeze pins F0/F1/F2 by date range; no fold is ever dropped
        (the freeze declares no drop-one-fold scored cell; force-flat at
        boundaries replaces purge-gap carving)."""
        if stress.dropped_fold_index is not None:
            raise ContractViolation(
                "the frozen LOT family declares no dropped-fold stress cell"
            )
        by_fold: dict[str, list[int]] = {}
        for instant in sorted({int(v) for v in instants}):
            by_fold.setdefault(fold_of_instant(instant), []).append(instant)
        out: list[FoldSpec] = []
        for index, (label, _start, _end) in enumerate(FOLD_RANGES):
            members = by_fold.get(label, [])
            if not members:
                raise ContractViolation(f"frozen fold {label} has no schedule instants")
            out.append(
                FoldSpec(index=index, label=label, instants=tuple(members), purge_days=0)
            )
        return tuple(out)

    def fold_label(self, index: int) -> str:
        return FOLD_RANGES[index][0]

    def fold_count(self) -> int:
        return len(FOLD_RANGES)

    def purge_days(self) -> int:
        return 0  # force-flat at fold boundaries replaces purge carving

    # ------------------------------------------------------------------ #
    # Targets (PIT features -> quintile book; fold-boundary force-flat)
    # ------------------------------------------------------------------ #
    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        instant = int(instant_ns)
        last_completed = self._last_completed_bar_map(universe, instant)
        if instant in self._force_flat:
            terminal = instant == int(self._instants[-1])
            return {
                "status": STATUS_OK,
                "weights": [],
                "carried_forward": False,
                "reason_code": (
                    "terminal_force_flat" if terminal else "fold_boundary_force_flat"
                ),
                "diagnostics": {
                    "fold": fold_of_instant(instant),
                    "note": (
                        "terminal force-flat boundary"
                        if terminal
                        else "force-flat at frozen fold boundary"
                    ),
                },
            }
        stamp = self._engine.features_at(
            instant_ns=instant,
            arm=self._arm_id,
            symbols=sorted(set(universe)),
            last_completed_bar=last_completed,
        )
        decision = self._book(stamp)
        return {
            "status": decision.status,
            "weights": [[sym, w] for sym, w in decision.weights],
            "carried_forward": decision.carried_forward,
            "reason_code": decision.reason_code,
            "diagnostics": {
                "fold": fold_of_instant(instant),
                "role": ROLE_BY_ARM[self._arm_id],
                **decision.diagnostics,
            },
        }

    def _book(self, stamp: Any) -> BookDecision:
        benchmark_beta = self._engine_mean_benchmark_beta(stamp.instant_ns)
        return build_quintile_book(
            stamp=stamp,
            arm_spec=self._arm_spec,
            benchmark_beta_mean=benchmark_beta,
        )

    def _engine_mean_benchmark_beta(self, instant_ns: int) -> float:
        """Mean BTC beta context over the tradeable cohort (diagnostic only)."""
        day = day_index(int(instant_ns)) - 1
        values = []
        for symbol in self._tradeable:
            beta = self._engine._beta_at(symbol, day)  # noqa: SLF001 - own engine
            if beta is not None:
                values.append(beta)
        if not values:
            return 0.0
        return math.fsum(values) / len(values)

    def _last_completed_bar_map(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, int]:
        out: dict[str, int] = {}
        for sym in sorted(set(symbols)):
            closes = self._bar_closes.get(str(sym)) or ()
            idx = bisect.bisect_right(closes, int(instant_ns)) - 1
            if idx >= 0:
                out[str(sym)] = int(closes[idx])
        return out

    # ------------------------------------------------------------------ #
    # Fills / marks (repo strict-later fill clock)
    # ------------------------------------------------------------------ #
    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        delay = int(stress.event_delay_events)
        if delay < 0:
            raise ContractViolation("event_delay_events must be >= 0")
        out: list[FillRecord] = []
        for sym in sorted(set(symbols)):
            event = self._fill_event(str(sym), int(instant_ns), delay=delay)
            if event is None:
                out.append(FillRecord(symbol=str(sym), decision_ns=int(instant_ns)))
            else:
                out.append(
                    FillRecord(
                        symbol=str(sym),
                        decision_ns=int(instant_ns),
                        status=FillStatusVocabulary.APPLIED,
                        applied=True,
                        price=float(event[1]),
                        fill_open_ns=int(event[0]),
                        fill_bar_close_ns=int(event[2]),
                        event_offset=int(delay),
                    )
                )
        return tuple(out)

    def _fill_event(
        self, symbol: str, decision_ns: int, *, delay: int
    ) -> Optional[tuple[int, float, int]]:
        """Covering-bar fill event (repo fill clock ``next_allowed_event_
        after_signal_bar_close``): the bar with ``derived_open <= D < close``;
        ``delay`` walks exactly that many further allowed events; a data gap
        yields NO event -- never a shifted substitute."""
        bars = self._bars.get(symbol)
        if not bars:
            return None
        closes = self._bar_closes[symbol]
        idx = bisect.bisect_right(closes, int(decision_ns))
        if idx >= len(bars):
            return None
        covering = bars[idx]
        if not (bar_open_ns(covering) <= int(decision_ns) < covering.ts_event_ns):
            return None
        chosen_idx = idx + delay
        if chosen_idx >= len(bars):
            return None
        chosen = bars[chosen_idx]
        return (bar_open_ns(chosen), float(chosen.open), int(chosen.ts_event_ns))

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        out: dict[str, Optional[float]] = {}
        for sym in sorted(set(symbols)):
            resolved = self._resolve_symbol(str(sym))
            bars = self._bars.get(resolved or "") or ()
            marks: Optional[float] = None
            for bar in bars:
                if bar_open_ns(bar) <= int(instant_ns) < bar.ts_event_ns:
                    marks = float(bar.open)
                    break
            out[str(sym)] = marks
        return out

    # ------------------------------------------------------------------ #
    # Native funding settlements (injected from the staged snapshot)
    # ------------------------------------------------------------------ #
    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        resolved = self._resolve_symbol(str(symbol))
        if resolved is None:
            return ()
        return tuple(
            SettlementPoint(publish_ts_ns=int(p.publish_ts_ns), value=float(p.value))
            for p in self._inputs.settlements_by_symbol.get(resolved, ())
        )

    def funding_cashflows_for_spans(
        self, spans: Sequence[PositionSpan]
    ) -> list[dict[str, Any]]:
        return super().funding_cashflows_for_spans(spans)


# --------------------------------------------------------------------------- #
# Arm spec + cached schedule
# --------------------------------------------------------------------------- #
def _arm_spec(arm_id: str):
    from research.v11.families.lottery_max_skew.strategy import ArmSpec

    return ArmSpec(
        arm_id=arm_id,
        role=ROLE_BY_ARM[arm_id],
        formation_days=FORMATION_DAYS_BY_ARM[arm_id],
        inverted=bool(ARM_INVERTED[arm_id]),
    )


def build_cached_schedule() -> tuple[int, ...]:
    """The frozen schedule instants (module-level cache; deterministic)."""
    from research.v11.families.lottery_max_skew.strategy import build_schedule_instants

    return build_schedule_instants()


def build_arm_plugin(arm_id: str, inputs: MarketInputs) -> LotteryMaxSkewPlugin:
    """Factory: one frozen arm plugin over the injected market inputs."""
    return LotteryMaxSkewPlugin(arm_id=arm_id, inputs=inputs)


__all__ = [
    "ANCHOR_ARM",
    "ARM_IDS",
    "BarEvent",
    "BENCHMARK_EXCLUDED",
    "BENCHMARK_INSTRUMENT",
    "BookDecision",
    "CONTROL_ARM",
    "COSTS_FROZEN",
    "DECISION_CLOCK_FROZEN",
    "DIRECTION",
    "FAMILY_ID",
    "FALSIFICATION_BY_ARM",
    "FROZEN_STRESS_EXTRA_TICKS",
    "FROZEN_STRESS_EVENT_DELAY",
    "FROZEN_STRESS_FEE_MULTIPLIER",
    "FROZEN_STRESS_NAME",
    "FEATURE_KIND_BY_ARM",
    "FORMATION_DAYS_BY_ARM",
    "HOLDING_DAYS_BY_ARM",
    "MarketInputs",
    "NEIGHBOUR_ARM",
    "ROLE_BY_ARM",
    "STRATEGY_ID",
    "WINDOW_END_ISO",
    "WINDOW_START_ISO",
    "LotteryMaxSkewPlugin",
    "bar_open_ns",
    "build_arm_plugin",
    "build_cached_schedule",
    "frozen_identity",
    "frozen_stress",
]
