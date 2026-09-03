"""Adapter plugin joining A8-V11-ILLIQ-AMIHUD to the generic V10 adapter.

Thin :class:`research.adapter_v10.base.GenericStrategyBase` subclass; every
generic capability (baseline cell, drop-one-symbol universe filtering, cost
arithmetic, funding accrual shape) is inherited unchanged -- nothing in the
adapter is forked.  Bars and native funding settlements are INJECTED at
construction time (synthetic fixtures for tests/dry-run, or the read-only
staged catalog for schedule-only audits); this plugin never scores and never
writes data.

Frozen contract implemented here:

* schedule  -> Mondays 00:00:00Z inside the frozen window (final stamp is the
  terminal force-flat boundary; the generic runner owns that edge);
* folds     -> frozen F0/F1/F2 date ranges, force-flat at fold boundaries
  (the book at the last stamp of a fold is empty), purge 0 by construction;
* targets   -> quintile Amihud book (28d anchor / 56d neighbour / inverted
  control) with frozen 90d BTC beta hedge and per-stamp confound diagnostics;
* fills     -> ONE declared execution lag (``EXECUTION_LAG_DAYS``) after the
  decision stamp, then the strict-later covering 15m bar open; stress walks
  ``event_delay_events`` further completed events;
* marks     -> covering-bar open at the requested instant;
* identity  -> the FROZEN V11 identity (digest-pinned by the selection freeze).
"""

from __future__ import annotations

import math
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
from research.hyp_a8_m01 import normalize_settlements, funding_cashflows, HoldingSpan

from research.v11.families.illiq_amihud.strategy import (
    ADVERSE_TICK_SLIP_FLOOR,
    ARMS,
    BENCHMARK_SYMBOL_EXCLUDED,
    DAY_NS,
    DECISION_CLOCK_TEXT,
    EXECUTION_LAG_DAYS,
    FOLDS,
    MIN_ELIGIBLE,
    STATUS_OK,
    STATUS_SKIP,
    TAKER_FEE_FLOOR_BPS,
    WINDOW_END_ISO,
    WINDOW_START_ISO,
    build_frozen_identity,
    build_quintile_book,
    compute_stamp_features,
    fold_label_for_stamp,
    frozen_arm_ids,
    weekly_monday_stamps,
)

SCHEDULE_SOURCE = "research.v11.families.illiq_amihud.strategy.weekly_monday_stamps"
SCHEDULE_CLOCK = "monday_00z_utc_epoch_ns"


class IlliqAmihudPlugin(GenericStrategyBase):
    """Adapter-facing view of one frozen A8-V11-ILLIQ-AMIHUD arm."""

    def __init__(
        self,
        *,
        bars_by_symbol: Mapping[str, Sequence[Any]],
        arm_id: str,
        tick_sizes: Optional[Mapping[str, float]] = None,
        settle_points_by_symbol: Optional[Mapping[str, Sequence[Any]]] = None,
        window_start_iso: str = WINDOW_START_ISO,
        window_end_iso: str = WINDOW_END_ISO,
        benchmark_symbol: str = BENCHMARK_SYMBOL_EXCLUDED,
        execution_lag_days: int = EXECUTION_LAG_DAYS,
    ) -> None:
        if arm_id not in ARMS:
            raise ContractViolation(
                f"unknown arm {arm_id!r}; frozen arms are {frozen_arm_ids()}"
            )
        if not bars_by_symbol:
            raise ContractViolation("IlliqAmihudPlugin needs at least one symbol of bars")
        self._arm_id = str(arm_id)
        self._arm = ARMS[str(arm_id)]
        self._bars: dict[str, tuple[Any, ...]] = {
            str(sym): tuple(bars) for sym, bars in sorted(bars_by_symbol.items())
        }
        if str(benchmark_symbol) not in self._bars:
            raise ContractViolation(
                f"benchmark leg {benchmark_symbol!r} has no injected bars"
            )
        self._benchmark = str(benchmark_symbol)
        self._window_start_iso = str(window_start_iso)
        self._window_end_iso = str(window_end_iso)
        self._lag_ns = int(execution_lag_days) * DAY_NS
        if int(execution_lag_days) < 0:
            raise ContractViolation("execution_lag_days must be >= 0")
        self._tick_sizes = {
            str(k): float(v) for k, v in (tick_sizes or {}).items()
        }
        for sym, size in self._tick_sizes.items():
            if not math.isfinite(size) or size <= 0.0:
                raise ContractViolation(f"tick size for {sym} must be positive")
        self._settlements = {
            str(k): tuple(v) for k, v in (settle_points_by_symbol or {}).items()
        }
        self._stamps: tuple[int, ...] = weekly_monday_stamps(
            window_start_iso=self._window_start_iso,
            window_end_iso=self._window_end_iso,
        )

    # ------------------------------------------------------------------ #
    # Identity / costs / universe
    # ------------------------------------------------------------------ #
    def identity(self) -> StrategyIdentity:
        return build_frozen_identity(self._arm_id)

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=float(TAKER_FEE_FLOOR_BPS),
            adverse_tick_slip_floor=int(ADVERSE_TICK_SLIP_FLOOR),
            default_tick_sizes=dict(self._tick_sizes),
        )

    def tradeable_universe(self) -> tuple[str, ...]:
        return tuple(sorted(set(self._bars) - {self._benchmark}))

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.tradeable_universe()) | {self._benchmark}))

    def minimum_tradeable_names(self) -> int:
        """Both quintile legs must stay constructible after symbol drops."""
        return int(MIN_ELIGIBLE)

    # ------------------------------------------------------------------ #
    # Schedule / folds
    # ------------------------------------------------------------------ #
    def schedule(self) -> ImmutableSchedule:
        return ImmutableSchedule(
            instants=self._stamps,
            source=SCHEDULE_SOURCE,
            clock=SCHEDULE_CLOCK,
        )

    def folds(
        self, *, stress: StressSpec, instants: Sequence[int]
    ) -> tuple[FoldSpec, ...]:
        """Frozen F0/F1/F2 date folds; every instant belongs to exactly one."""
        buckets: dict[str, list[int]] = {}
        for stamp in sorted(int(v) for v in instants):
            label = fold_label_for_stamp(stamp)
            if label is None:
                raise ContractViolation(
                    f"decision stamp {stamp} outside every frozen fold"
                )
            buckets.setdefault(label, []).append(stamp)
        out: list[FoldSpec] = []
        for index, (label, _start_iso, _end_iso) in enumerate(FOLDS):
            members = tuple(buckets.get(label, ()))
            if not members:
                raise ContractViolation(f"frozen fold {label} has no decision stamps")
            dropped = (
                stress.dropped_fold_index is not None
                and index == int(stress.dropped_fold_index)
            )
            out.append(
                FoldSpec(
                    index=index,
                    label=label,
                    instants=members,
                    purge_days=0,
                    dropped=dropped,
                )
            )
        return tuple(out)

    def fold_instants(self) -> dict[str, tuple[int, ...]]:
        """Frozen fold membership of the schedule (plugin-side view)."""
        out: dict[str, list[int]] = {}
        for stamp in self._stamps:
            label = fold_label_for_stamp(stamp)
            if label is None:
                raise ContractViolation(f"stamp {stamp} outside every frozen fold")
            out.setdefault(label, []).append(int(stamp))
        return {label: tuple(v) for label, v in sorted(out.items())}

    # ------------------------------------------------------------------ #
    # Targets
    # ------------------------------------------------------------------ #
    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        fold = fold_label_for_stamp(int(instant_ns))
        if fold is None:
            raise ContractViolation(f"stamp {instant_ns} outside every frozen fold")
        members = self.fold_instants()[fold]
        # Force-flat at fold boundaries (frozen fold policy); the generic
        # runner force-flattens the final schedule instant itself.
        if int(instant_ns) == int(members[-1]) and int(instant_ns) != int(
            self.schedule().instants[-1]
        ):
            return {
                "status": STATUS_OK,
                "weights": {},
                "reason_code": "FOLD_BOUNDARY_FORCE_FLAT",
                "diagnostics": {"fold": fold, "force_flat": True},
            }
        stamp = compute_stamp_features(
            bars_by_symbol=self._bars,
            universe=universe,
            benchmark_symbol=self._benchmark,
            decision_ns=int(instant_ns),
            formation_days=int(self._arm["formation_days"]),
        )
        book = build_quintile_book(
            features=stamp.features,
            betas=stamp.betas,
            arm_sign=int(self._arm["sign"]),
        )
        diagnostics = dict(stamp.diagnostics)
        diagnostics.update({k: v for k, v in book.get("diagnostics", {}).items()})
        return {
            "status": str(book["status"]),
            "weights": dict(book["weights"]),
            "reason_code": book.get("reason_code"),
            "diagnostics": diagnostics,
        }

    # ------------------------------------------------------------------ #
    # Fills (one declared execution lag; strict-later event clock)
    # ------------------------------------------------------------------ #
    def _fill_event(self, symbol: str, decision_ns: int, delay_events: int):
        bars = sorted(
            self._bars.get(symbol) or (), key=lambda b: int(b.ts_event_ns)
        )
        target = int(decision_ns) + int(self._lag_ns)
        start_idx: Optional[int] = None
        for idx, bar in enumerate(bars):
            open_ns = int(bar.ts_event_ns) - self._bar_interval_hint(bars)
            if open_ns <= target < int(bar.ts_event_ns):
                start_idx = idx
                break
        if start_idx is None or start_idx + int(delay_events) >= len(bars):
            return None
        chosen = bars[start_idx + int(delay_events)]
        chosen_open = int(chosen.ts_event_ns) - self._bar_interval_hint(bars)
        return {
            "fill_open_ns": chosen_open,
            "fill_bar_close_ns": int(chosen.ts_event_ns),
            "price": float(chosen.open),
            "event_offset": int(delay_events),
        }

    @staticmethod
    def _bar_interval_hint(bars: Sequence[Any]) -> int:
        """Derived bar width from the closest pair of close stamps (data-driven)."""
        if len(bars) >= 2:
            gaps = [
                int(bars[i + 1].ts_event_ns) - int(bars[i].ts_event_ns)
                for i in range(min(8, len(bars) - 1))
                if int(bars[i + 1].ts_event_ns) > int(bars[i].ts_event_ns)
            ]
            if gaps:
                return min(gaps)
        return DAY_NS

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        out: list[FillRecord] = []
        for sym in sorted(set(symbols)):
            event = self._fill_event(sym, int(instant_ns), int(stress.event_delay_events))
            if event is None:
                out.append(FillRecord(symbol=sym, decision_ns=int(instant_ns)))
            else:
                out.append(
                    FillRecord(
                        symbol=sym,
                        decision_ns=int(instant_ns),
                        status=FillStatusVocabulary.APPLIED,
                        applied=True,
                        price=float(event["price"]),
                        fill_open_ns=int(event["fill_open_ns"]),
                        fill_bar_close_ns=int(event["fill_bar_close_ns"]),
                        event_offset=int(event["event_offset"]),
                    )
                )
        return tuple(out)

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        out: dict[str, Optional[float]] = {}
        for sym in sorted(set(symbols)):
            interval = self._bar_interval_hint(self._bars.get(sym) or ())
            mark: Optional[float] = None
            for bar in self._bars.get(sym) or ():
                open_ns = int(bar.ts_event_ns) - interval
                if open_ns <= int(instant_ns) < int(bar.ts_event_ns):
                    mark = float(bar.open)
                    break
            out[sym] = mark
        return out

    # ------------------------------------------------------------------ #
    # Native funding (settlements injected; LONG_PAYS_POSITIVE_RATE)
    # ------------------------------------------------------------------ #
    def _native_points(self, symbol: str):
        """Native settlement series normalised through the shared PIT hook."""
        raw = self._settlements.get(str(symbol), ())
        native = [
            point
            if isinstance(point, Mapping)
            else {
                "publish_ts_ns": int(point.publish_ts_ns),
                "value": float(point.value),
                "kind": str(getattr(point, "kind", "info")),
            }
            for point in raw
        ]
        return normalize_settlements(native)

    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        return tuple(
            SettlementPoint(publish_ts_ns=int(p.publish_ts_ns), value=float(p.value))
            for p in self._native_points(str(symbol))
        )

    def funding_cashflows_for_spans(
        self, spans: Sequence[PositionSpan]
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for symbol in sorted({span.symbol for span in spans}):
            legs = [
                HoldingSpan(
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
            flows = funding_cashflows(legs, self._native_points(symbol))
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


__all__ = ["IlliqAmihudPlugin", "SCHEDULE_CLOCK", "SCHEDULE_SOURCE"]
