"""Tiny deterministic strategy proving the adapter is reusable (G1).

The plugin participates through exactly the same
:class:`research.adapter_v10.protocol.ResearchStrategy` interface as any panel
family: static (never random) symbol selection, one simple cap-bounded
book per decision instant, a deterministic synthetic price grid and its own
native settlement series. Nothing here reads real data or scores anything.

Selection rule (fixed, no parameters): sort the universe, then take
``N_SELECT`` consecutive names starting at ``day_index % len(universe)`` --
books rotate day by day but are a pure function of the universe, the instant
and the config. Weights are the symmetric ±(gross/N) book clipped to the cap.
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
    ImmutableSchedule,
    SettlementPoint,
    StrategyIdentity,
    StressSpec,
)

DEFAULT_GROSS = 1.0


class DummyDeterministicStrategy(GenericStrategyBase):
    """Static-rule daily strategy used for adapter reuse proof tests."""

    def __init__(
        self,
        *,
        symbols: Sequence[str],
        instants_ns: Sequence[int],
        n_select: int = 4,
        gross: float = DEFAULT_GROSS,
        base_price: float = 100.0,
        daily_drift_by_symbol: Optional[Mapping[str, float]] = None,
        settle_offset_ns: int = 8 * 3600 * 1_000_000_000,
        settle_rate_by_day_index=None,
        taker_fee_bps: float = 5.0,
        adverse_tick_slip_floor: int = 1,
        tick_size: float = 0.01,
        window_start_iso: str = "2025-01-01T00:00:00Z",
        window_end_iso: str = "2025-01-05T00:00:00Z",
        strategy_id: str = "dummy_static_rotation",
        family_id: str = "DUMMY_DETERMINISTIC_ROTATION",
        arm_config_id: str = "dummy-baseline-arm",
        excluded_benchmark_symbol: str = "",
        purge_days: int = 1,
        fold_count: int = 2,
    ) -> None:
        if len(set(symbols)) != len(symbols):
            raise ContractViolation("dummy symbols must be unique")
        if int(n_select) < 1 or int(n_select) > len(symbols):
            raise ContractViolation("n_select must be within [1, len(symbols)]")
        ordered_instants = tuple(sorted(int(v) for v in instants_ns))
        if len(set(ordered_instants)) != len(ordered_instants) or len(ordered_instants) < 3:
            raise ContractViolation("dummy needs at least three unique decision instants")
        self._symbols = tuple(str(s) for s in sorted(symbols))
        self._instants = ordered_instants
        self._n_select = int(n_select)
        self._gross = float(gross)
        self._base_price = float(base_price)
        self._drift = {str(k): float(v) for k, v in (daily_drift_by_symbol or {}).items()}
        self._settle_offset_ns = int(settle_offset_ns)
        self._settle_rate = list(settle_rate_by_day_index or (0.0,))
        self._tick_size = float(tick_size)
        self._purge_days = int(purge_days)
        self._fold_count = int(fold_count)
        self._identity = StrategyIdentity(
            strategy_id=str(strategy_id),
            family_id=str(family_id),
            arm_config_id=str(arm_config_id),
            direction="BOTH_WITH_SIGN_SEMANTICS",
            window_start_iso=str(window_start_iso),
            window_end_iso=str(window_end_iso),
            benchmark_symbols_excluded=(
                (str(excluded_benchmark_symbol),) if excluded_benchmark_symbol else ()
            ),
            funding_sign_convention="LONG_PAYS_POSITIVE_RATE",
            config={
                "n_select": self._n_select,
                "gross": self._gross,
                "rule": "static_rotation_no_randomness",
            },
        )
        self._cost_model = CostModel(
            taker_fee_bps=float(taker_fee_bps),
            adverse_tick_slip_floor=int(adverse_tick_slip_floor),
            default_tick_sizes={sym: float(self._tick_size) for sym in self._symbols},
        )

    # ------------------------------------------------------------------ #
    # Interface surface
    # ------------------------------------------------------------------ #
    def identity(self) -> StrategyIdentity:
        return self._identity

    def cost_model(self) -> CostModel:
        return self._cost_model

    def tradeable_universe(self) -> tuple[str, ...]:
        return self._symbols

    def benchmark_context_symbols(self) -> tuple[str, ...]:
        """Tradeable names plus any declared context-only benchmark leg."""
        extra = self._identity.benchmark_symbols_excluded
        return tuple(sorted(set(self._symbols) | set(extra)))

    def minimum_tradeable_names(self) -> int:
        return max(2, self._n_select - 1)

    def schedule(self) -> ImmutableSchedule:
        return ImmutableSchedule(
            instants=self._instants,
            source=f"{self.__class__.__name__}.static_instants",
            clock="decision_instant_supplied_by_config_utc_grid",
        )

    def fold_count(self) -> int:
        return self._fold_count

    def purge_days(self) -> int:
        return self._purge_days

    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        chosen = self.select_symbols(int(instant_ns), list(universe))
        if not chosen:
            return {
                "status": "SKIP_NO_SELECTION",
                "weights": [],
                "carried_forward": True,
                "reason_code": "empty_static_selection",
                "diagnostics": {"gross_realised": 0.0, "net_exposure": 0.0},
            }
        from research.adapter_v10.protocol import DEFAULT_WEIGHT_CAP_MAX

        cap = DEFAULT_WEIGHT_CAP_MAX
        long_count = max(1, len(chosen) // 2)
        short_count = len(chosen) - long_count
        total_legs = long_count + short_count
        per_leg = min(self._gross / total_legs, cap)
        weights: dict[str, float] = {}
        for sym in chosen[:long_count]:
            weights[sym] = round(per_leg, 12)
        for sym in chosen[long_count:]:
            weights[sym] = round(-per_leg, 12)
        residual = round(self._gross - math.fsum(abs(w) for w in weights.values()), 12)
        headroom = round(cap - abs(weights[chosen[0]]), 12)
        if abs(residual) > 1e-12:
            if headroom < residual:
                raise ContractViolation(
                    f"dummy config cannot reach gross {self._gross} under cap {cap}"
                )
            weights[chosen[0]] = round(weights[chosen[0]] + residual, 12)
        ordered_weights = [[sym, weights[sym]] for sym in sorted(weights)]
        longs = [[s, w] for s, w in ordered_weights if w > 0]
        shorts = [[s, w] for s, w in ordered_weights if w < 0]
        return {
            "status": "OK",
            "weights": ordered_weights,
            "longs": longs,
            "shorts": shorts,
            "carried_forward": False,
            "diagnostics": {
                "gross_realised": round(math.fsum(abs(w) for _, w in ordered_weights), 12),
                "net_exposure": round(math.fsum(w for _, w in ordered_weights), 12),
                "n_long": len(longs),
                "n_short": len(shorts),
                "selection_start_index": self.schedule_position(int(instant_ns)) % len(list(universe)),
                "selection": list(chosen),
            },
        }

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        """Strict-later fills at ``instant + one bar`` with no missing slots."""
        del stress
        fill_open = int(instant_ns) + FILL_DELAY_NS
        return tuple(
            FillRecord(
                symbol=sym,
                decision_ns=int(instant_ns),
                status=FillStatusVocabulary.APPLIED,
                applied=True,
                price=self.mark_price(sym, fill_open),
                fill_open_ns=fill_open,
                fill_bar_close_ns=fill_open + FILL_DELAY_NS,
                event_offset=0,
            )
            for sym in sorted(set(symbols))
        )

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        return {sym: self.mark_price(sym, int(instant_ns)) for sym in sorted(set(symbols))}

    # ------------------------------------------------------------------ #
    # Deterministic internals
    # ------------------------------------------------------------------ #
    def select_symbols(self, instant_ns: int, universe: Sequence[str]) -> list[str]:
        pool = [str(s) for s in sorted(set(universe))]
        position = self.schedule_position(int(instant_ns))
        start = position % len(pool)
        chosen: list[str] = []
        for offset in range(len(pool)):
            candidate = pool[(start + offset) % len(pool)]
            chosen.append(candidate)
            if len(chosen) == self._n_select:
                break
        return chosen

    def schedule_position(self, instant_ns: int) -> int:
        """Index of the instant inside the immutable schedule (fallback: day no.)."""
        try:
            return self._instants.index(int(instant_ns))
        except ValueError:
            return int(instant_ns // DAY_NS_ANCHOR)

    def mark_price(self, symbol: str, ts_ns: int) -> float:
        """Deterministic synthetic grid anchored at the first decision instant."""
        anchor = min(self._instants)
        day_index = (int(ts_ns) - anchor) / DAY_NS_ANCHOR
        drift = self._drift.get(symbol, DEFAULT_DRIFT)
        price = self._base_price * (1.0 + drift * day_index)
        if not math.isfinite(price) or price <= 0.0:
            raise ContractViolation(f"dummy mark degenerated for {symbol} at {ts_ns}")
        return round(price, 10)

    def settlements(self, symbol: str) -> tuple[SettlementPoint, ...]:
        points = []
        for index, instant in enumerate(self._instants[:-1]):
            rate = float(self._settle_rate[index % len(self._settle_rate)])
            points.append(
                SettlementPoint(
                    publish_ts_ns=int(instant) + self._settle_offset_ns,
                    value=rate,
                )
            )
        seen: set[int] = set()
        for point in points:
            if point.publish_ts_ns in seen:
                raise ContractViolation("dummy settlement stamps must be unique")
            seen.add(point.publish_ts_ns)
        return tuple(points)


#: One synthetic "bar" between the decision instant and the strict-later fill.
FILL_DELAY_NS = 15 * 60 * 1_000_000_000
DAY_NS_ANCHOR = 86_400_000_000_000
DEFAULT_DRIFT = 0.001

__all__ = [
    "DEFAULT_DRIFT",
    "DEFAULT_GROSS",
    "DummyDeterministicStrategy",
    "FILL_DELAY_NS",
]
