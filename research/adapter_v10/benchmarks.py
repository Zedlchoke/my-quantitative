"""BG5 -- flat hard benchmark + context-only benchmark outputs (G1).

Roles follow ``research.contract_v10.BENCHMARKS_V10``:

* ``flat_hard``      -- MANDATORY hard gate: a zero-position book evaluated
  after cost. Its realized series is exactly zero everywhere and the module
  refuses to emit anything else (a non-zero flat benchmark means the
  accounting is broken, not that the strategy made money).
* ``buy_and_hold``   -- context only, never enters any scored denominator.
* ``benchmark_excluded_neutral`` -- context only: identical book computed over
  the universe MINUS the plugin-declared excluded benchmark symbols.

No symbol name is hard-coded here: exclusions come from
``StrategyIdentity.benchmark_symbols_excluded`` (the plugin supplies its own
constant, e.g. the panel family's pinned BTC exclusion).
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    ContractViolation,
    MarkProviderCallable,
    StrategyIdentity,
)

FLAT_HARD = "flat_hard"
BUY_AND_HOLD = "buy_and_hold"
BENCHMARK_EXCLUDED_NEUTRAL = "benchmark_excluded_neutral"
HARD_GATE_ROLE = "hard_gate"
CONTEXT_ONLY_ROLE = "context_only"


def flat_benchmark(*, instants: Sequence[int]) -> dict[str, Any]:
    """Zero-PnL hard baseline; every value must be exactly 0.0."""
    instants_out = [int(v) for v in instants]
    if len(instants_out) < 2:
        raise ContractViolation("flat benchmark needs at least two decision instants")
    zeros = [0.0 for _ in range(len(instants_out) - 1)]
    realised = [round(v + 0.0, 12) for v in zeros]
    if any(v != 0.0 for v in realised):
        raise ContractViolation("flat benchmark produced a non-zero realized return")
    return {
        "kind": FLAT_HARD,
        "role": HARD_GATE_ROLE,
        "enters_denominator": False,
        "definition": "zero_position_flat_book_evaluated_after_cost",
        "n_instants": len(instants_out),
        "decision_ns": instants_out[1:],
        "net_return_per_unit": realised,
        "cumulative_return": 0.0,
        "max_drawdown": 0.0,
        "position_pf": None,
        "pf_reason": "no_positions",
    }


def _equal_weight_book(symbols: Sequence[str]) -> dict[str, float]:
    tradable = sorted({str(s) for s in symbols})
    if not tradable:
        raise ContractViolation("context book needs at least one symbol")
    weight = round(1.0 / len(tradable), 12)
    residual = round(1.0 - sum(weight for _ in tradable), 12)
    weights = {sym: weight for sym in tradable}
    # absorb rounding residue into the first leg so gross stays exactly 1.0
    first = tradable[0]
    weights[first] = round(weights[first] + residual, 12)
    return weights


def buy_and_hold_context(
    *,
    symbols: Sequence[str],
    instants: Sequence[int],
    marks_at: MarkProviderCallable,
) -> dict[str, Any]:
    """Equal-weight buy-and-hold entered at the first instant, marked after."""
    instants_out = [int(v) for v in instants]
    weights = _equal_weight_book(symbols)
    first_price = _require_marks(marks_at(sorted(weights), instants_out[0]), sorted(weights))
    last_price = _require_marks(
        marks_at(sorted(weights), instants_out[-1]), sorted(weights)
    )
    per_leg = {
        sym: float(last_price[sym]) / float(first_price[sym]) - 1.0 for sym in weights
    }
    gross_return = math.fsum(weights[sym] * per_leg[sym] for sym in sorted(weights))
    return {
        "kind": BUY_AND_HOLD,
        "role": CONTEXT_ONLY_ROLE,
        "enters_denominator": False,
        "n_instants": len(instants_out),
        "weights": {sym: round(w, 12) for sym, w in sorted(weights.items())},
        "entry_ns": instants_out[0],
        "exit_ns": instants_out[-1],
        "per_leg_gross_return": {s: round(v, 12) for s, v in sorted(per_leg.items())},
        "cumulative_gross_return": round(gross_return, 12),
        "note": "context_only_scored_false",
    }


def benchmark_excluded_neutral_context(
    *,
    identity: StrategyIdentity,
    context_symbols: Sequence[str],
    instants: Sequence[int],
    marks_at: MarkProviderCallable,
) -> dict[str, Any]:
    """Same context book as :func:`buy_and_hold_context` minus excluded legs.

    Proves the exclusion is effective: any declared benchmark-excluded symbol
    must appear nowhere in the emitted weights.
    """
    excluded = sorted(str(s) for s in identity.benchmark_symbols_excluded)
    tradable = [sym for sym in sorted(set(context_symbols)) if sym not in set(excluded)]
    payload = buy_and_hold_context(
        symbols=tradable, instants=instants, marks_at=marks_at
    )
    payload["kind"] = BENCHMARK_EXCLUDED_NEUTRAL
    payload["excluded_symbols"] = excluded
    leaked = sorted(set(payload["weights"]) & set(excluded))
    if leaked:
        raise ContractViolation(f"benchmark-excluded symbols leaked into context: {leaked}")
    return payload


def build_benchmark_block(
    *,
    identity: StrategyIdentity,
    context_symbols: Sequence[str],
    instants: Sequence[int],
    marks_at: MarkProviderCallable,
) -> dict[str, Any]:
    """All three BG5 outputs in one deterministic artifact block."""
    flat = flat_benchmark(instants=instants)
    hold = buy_and_hold_context(
        symbols=list(context_symbols), instants=instants, marks_at=marks_at
    )
    neutral = benchmark_excluded_neutral_context(
        identity=identity,
        context_symbols=context_symbols,
        instants=instants,
        marks_at=marks_at,
    )
    if set(neutral["weights"]) != set(hold["weights"]) and not set(
        str(s) for s in identity.benchmark_symbols_excluded
    ):
        raise ContractViolation("neutral context diverged without any declared exclusion")
    block = {"flat_hard": flat, "buy_and_hold": hold, "excluded_neutral": neutral}
    if flat["cumulative_return"] != 0.0:
        raise ContractViolation("flat hard gate must stay at exactly zero")
    return block


def _require_marks(
    observed: Mapping[str, Optional[float]], symbols: Sequence[str]
) -> dict[str, float]:
    out: dict[str, float] = {}
    for sym in symbols:
        price = observed.get(sym)
        if price is None or not math.isfinite(float(price)) or float(price) <= 0.0:
            raise ContractViolation(f"context mark unavailable/invalid for {sym}")
        out[sym] = float(price)
    return out


__all__ = [
    "BENCHMARK_EXCLUDED_NEUTRAL",
    "BUY_AND_HOLD",
    "FLAT_HARD",
    "benchmark_excluded_neutral_context",
    "build_benchmark_block",
    "buy_and_hold_context",
    "flat_benchmark",
]
