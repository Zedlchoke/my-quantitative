"""Specialist registry engine — V2 math with pluggable strategy specs.

The V2 engine (forked, untouched) dispatches entries/exits/stops by strategy
NAME. This module adds a registry (name -> StrategySpec) without changing
any fill/cost/fold/funding law: SpecialistEngine subclasses Engine and
overrides ONLY the three dispatch points (entry signal, exit signal,
open-position stop/direction). The run loop is the V2 loop with the two
dispatch calls swapped; every helper (_close_position, _apply_fill_costs,
_charge_funding_until, _assemble, fold laws) is inherited verbatim.

EQUIVALENCE GATE (mandatory, pre-outcome): registering the three V2
strategies as specs and running arms A1/A2/B must reproduce the V2 stored
tier-1 totals to <1e-6 on every cell before ANY candidate outcome exists
(plan §9). That gate is the proof the registry did not drift the math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from . import engine as _engine_mod
from .data import Bars
from .engine import (
    BUY_HOLD,
    Engine,
    EngineResult,
    Position,
    Trade,
    _entry_signal,
    _exit_signal,
    stop_hit,
)
from .strategies import (
    FLAT,
    MR_LONG,
    MR_MAX_HOLD_BARS,
    MR_STOP_ATR_MULT,
    TREND_LONG,
    TREND_SHORT,
    TREND_STOP_ATR_MULT,
    ExecIndicators,
    mr_long_entry,
    mr_long_exit,
    trend_long_entry,
    trend_long_exit,
    trend_short_entry,
    trend_short_exit,
)


@dataclass(frozen=True)
class StrategySpec:
    name: str
    direction: int  # +1 long, -1 short
    entry: Callable[[int, Bars, ExecIndicators], bool]
    exit_: Callable[[int, Bars, ExecIndicators, int], bool]
    stop_atr_mult: float  # entry -/+ mult*ATR14; NaN disables until ATR
    max_hold_exec_bars: int | None  # optional hard cap (checked in exit_)
    tie_break_class: str = "LONG_CAPABLE"
    economic_mechanism: str = ""
    failure_mode: str = ""


def _v2_specs() -> dict[str, StrategySpec]:
    """The three V2 frozen strategies expressed as specs (equivalence gate)."""
    return {
        TREND_LONG: StrategySpec(
            name=TREND_LONG,
            direction=1,
            entry=lambda i, b, x: trend_long_entry(i, b, x),
            exit_=lambda i, b, x, h: trend_long_exit(i, b, x),
            stop_atr_mult=TREND_STOP_ATR_MULT,
            max_hold_exec_bars=None,
            economic_mechanism="V2 frozen anchor (equivalence reference)",
        ),
        TREND_SHORT: StrategySpec(
            name=TREND_SHORT,
            direction=-1,
            entry=lambda i, b, x: trend_short_entry(i, b, x),
            exit_=lambda i, b, x, h: trend_short_exit(i, b, x),
            stop_atr_mult=TREND_STOP_ATR_MULT,
            max_hold_exec_bars=None,
            tie_break_class="BTC_ONLY_SHORT",
            economic_mechanism="V2 frozen anchor (equivalence reference)",
        ),
        MR_LONG: StrategySpec(
            name=MR_LONG,
            direction=1,
            entry=lambda i, b, x: mr_long_entry(i, b, x),
            exit_=lambda i, b, x, h: mr_long_exit(i, b, x, h),
            stop_atr_mult=MR_STOP_ATR_MULT,
            max_hold_exec_bars=MR_MAX_HOLD_BARS,
            economic_mechanism="V2 frozen anchor (equivalence reference)",
        ),
    }


class SpecialistEngine(Engine):
    """Engine with a strategy-spec registry; V2 laws inherited unchanged."""

    def __init__(self, bars, targets, folds, costs, specs: dict[str, StrategySpec],
                 initial_equity: float = 100_000.0, ind: ExecIndicators | None = None):
        missing = [s for s in {t for t in targets if t not in (None, FLAT, BUY_HOLD)}
                   if s not in specs]
        if missing:
            raise ValueError(f"targets reference unregistered strategies: {missing}")
        super().__init__(bars, targets, folds, costs, initial_equity, ind)
        self.specs = specs

    # -- dispatch points (the ONLY behavioral overrides) -------------------

    def _spec_entry(self, strategy: str, i: int) -> bool:
        if strategy in self.specs:
            return bool(self.specs[strategy].entry(i, self.bars, self.x))
        return bool(_entry_signal(strategy, i, self.bars, self.x))

    def _spec_exit(self, strategy: str, i: int, held: int) -> bool:
        spec = self.specs.get(strategy)
        if spec is None:
            return bool(_exit_signal(strategy, i, self.bars, self.x, held))
        if spec.max_hold_exec_bars is not None and held >= spec.max_hold_exec_bars:
            return True
        return bool(spec.exit_(i, self.bars, self.x, held))

    def _open_position(self, strategy, i, ts, px, cash):  # noqa: ANN001
        spec = self.specs.get(strategy)
        qty = round(cash / px, 8)
        a = float(self.x.atr14[i - 1]) if i > 0 else float("nan")
        if not np.isfinite(a):
            a = float(self.x.atr14[i])
        if spec is not None:
            direction = spec.direction
            stop = (px - spec.direction * spec.stop_atr_mult * a
                    if np.isfinite(a) and a > 0 else float("nan"))
        else:  # V2 path (equivalence)
            from .strategies import stop_price
            direction = -1 if strategy == TREND_SHORT else 1
            stop = stop_price(strategy, px, a)
        pos = Position(
            strategy=strategy,
            direction=direction,
            qty=qty,
            entry_px=px,
            entry_ts=ts,
            entry_bar=i,
            stop=stop,
            funding_up_to=ts,
        )
        self._apply_fill_costs(pos, px, qty)
        pos.entry_costs = pos.fees + pos.slip
        return pos

    # -- run loop: V2 verbatim except the two dispatch calls ----------------

    def run(self) -> EngineResult:  # noqa: C901
        bars = self.bars
        N = len(bars.ts_close)
        cash = self.initial_equity
        equity = np.full(N, np.nan)
        invested = np.zeros(N)
        trades: list[Trade] = []
        pos: Position | None = None
        pending_entry: str | None = None
        pending_exit: str | None = None
        for i in range(N):
            o = float(bars.open[i])
            c = float(bars.close[i])
            ts_o = int(bars.ts_open[i])
            ts_c = int(bars.ts_close[i])
            if pos is not None and pending_exit is not None:
                cash = self._close_position(pos, i, ts_o, o, pending_exit, cash, trades)
                pos = None
                pending_exit = None
            elif pos is None and pending_entry is not None:
                tgt = self.targets[i]
                if (tgt == pending_entry or tgt == BUY_HOLD) and self.fold_id[i] >= 0:
                    pos = self._open_position(pending_entry, i, ts_o, o, cash)
                    cash -= pos.direction * pos.qty * o + pos.fees + pos.slip
                pending_entry = None
            if pos is not None:
                tgt = self.targets[i]
                if tgt == BUY_HOLD:
                    pass
                elif tgt is None or tgt == FLAT or tgt != pos.strategy:
                    cash = self._close_position(pos, i, ts_o, o, "regime_off", cash, trades)
                    pos = None
            if pos is not None and i > pos.entry_bar and np.isfinite(pos.stop):
                if stop_hit(pos.strategy, float(bars.high[i]), float(bars.low[i]), pos.stop):
                    cash = self._close_position(
                        pos, i, ts_o, o, "stop", cash, trades, px_override=pos.stop
                    )
                    pos = None
            if pos is not None:
                self._charge_funding_until(pos, ts_c, c)
            if pos is not None and i in self._fold_ends:
                cash = self._close_position(pos, i, ts_c, c, "fold_flat", cash, trades)
                pos = None
            assert pos is None or self.fold_id[i] >= 0, (
                f"fold law violated: position open on unassigned exec bar {i}"
            )
            equity[i] = cash + (pos.direction * pos.qty * c if pos is not None else 0.0)
            invested[i] = 1.0 if pos is not None else 0.0
            pending_exit = None
            if pos is None:
                pending_entry = None
                tgt = self.targets[i]
                if tgt == BUY_HOLD:
                    if i in self._fold_starts:
                        pending_entry = TREND_LONG
                elif (
                    tgt is not None
                    and tgt != FLAT
                    and self.fold_id[i] >= 0
                    and self._spec_entry(tgt, i)          # <-- registry
                ):
                    pending_entry = tgt
            else:
                held = i - pos.entry_bar + 1
                if self._spec_exit(pos.strategy, i, held):  # <-- registry
                    pending_exit = "strategy_exit"
        result = self._assemble(equity, invested, trades)
        _engine_mod._assert_engine_invariants(result, self.folds)
        return result


def v2_equivalence_specs() -> dict[str, StrategySpec]:
    return _v2_specs()
