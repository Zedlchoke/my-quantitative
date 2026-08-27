"""BG4 -- preregistered stress-matrix driver (G1).

Builds the named stress surface from the repo-wide frozen vocabulary in
``research.contract_v10.STRESS_MATRIX_V10`` (five cells + baseline = six) and
maps every cell onto a :class:`research.adapter_v10.protocol.StressSpec`
supplied by the calling strategy. Each cell gets its own artifact file and its
own unique result/shard/log root; uniqueness is asserted, never assumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from research.adapter_v10.protocol import (
    AdapterError,
    ContractViolation,
    StressSpec,
)
from research.contract_v10 import STRESS_MATRIX_V10

#: The unstressed reference cell is always present and always first.
BASELINE_NAME = "baseline"

#: Fail-closed symbolic multipliers each named cell applies to a strategy's
#: own baseline cost model (baseline floors x factor; never invented numbers).
FEE_MULTIPLIER_FOR_CELL = {"fee_slippage_x1_5": 1.5}
EXTRA_TICKS_FOR_CELL = {"plus_2_ticks": 2}
EVENT_DELAY_FOR_CELL = {"plus_1_event_delay": 1}

STRESS_SURFACE_VARIANTS: tuple[str, ...] = tuple(STRESS_MATRIX_V10)


@dataclass(frozen=True)
class StressCell:
    """One named cell with the artifact/root names derived from it."""

    name: str
    spec: StressSpec
    artifact_name: str
    result_root: str
    shard_root: str
    log_root: str


def build_stress_spec(
    name: str,
    *,
    strategy_baseline: StressSpec,
    droppable_symbols: Sequence[str] = (),
) -> StressSpec:
    """Map one named cell onto a strategy's own cost floor declaration.

    ``droppable_symbols`` is the strategy's tradeable cohort: the
    ``drop_one_symbol`` cell removes the first sorted name deterministically.
    """
    if not isinstance(strategy_baseline, StressSpec):
        raise ContractViolation("strategy_baseline must be a StressSpec")
    if not strategy_baseline.is_baseline:
        raise ContractViolation(
            f"strategy_baseline must be named {BASELINE_NAME!r}, got {strategy_baseline.name!r}"
        )
    if name == BASELINE_NAME:
        return strategy_baseline
    known = set(FEE_MULTIPLIER_FOR_CELL) | set(EXTRA_TICKS_FOR_CELL) | set(EVENT_DELAY_FOR_CELL)
    known |= {"drop_one_symbol", "drop_one_fold"}
    if name not in STRESS_SURFACE_VARIANTS or name not in known:
        raise ContractViolation(f"unknown stress cell {name!r}; known: {sorted(known)}")
    symbol_to_drop = _single_symbol_for_cell(droppable_symbols, name)
    dropped_fold = 0 if name == "drop_one_fold" else None
    return StressSpec(
        name=name,
        fee_multiplier=strategy_baseline.fee_multiplier * FEE_MULTIPLIER_FOR_CELL.get(name, 1.0),
        tick_slip_ticks=(
            strategy_baseline.tick_slip_ticks + EXTRA_TICKS_FOR_CELL.get(name, 0)
        ),
        event_delay_events=strategy_baseline.event_delay_events + EVENT_DELAY_FOR_CELL.get(name, 0),
        drop_symbols=symbol_to_drop,
        dropped_fold_index=dropped_fold,
    )


def _single_symbol_for_cell(
    candidates: Sequence[str], cell: str
) -> tuple[str, ...]:
    """Deterministic drop-one-symbol target (first sorted candidate)."""
    if cell != "drop_one_symbol":
        return ()
    ordered = sorted(str(s) for s in candidates)
    if not ordered:
        raise ContractViolation(
            f"{cell} requires the strategy to declare at least one droppable symbol"
        )
    return (ordered[0],)


def stress_matrix_cells(
    *, strategy_baseline: StressSpec, droppable_symbols: Sequence[str] = ()
) -> tuple[StressCell, ...]:
    """The six-cell matrix: baseline plus every frozen variant, in order."""
    cells = [BASELINE_NAME, *STRESS_SURFACE_VARIANTS]
    out: list[StressCell] = []
    for name in cells:
        spec = build_stress_spec(
            name,
            strategy_baseline=strategy_baseline,
            droppable_symbols=droppable_symbols,
        )
        key = spec.key
        out.append(
            StressCell(
                name=name,
                spec=spec,
                artifact_name=f"{key}_artifact.json",
                result_root=f"results/{key}",
                shard_root=f"shards/{key}",
                log_root=f"logs/{key}.log",
            )
        )
    roots = [cell.result_root for cell in out]
    artifacts = [cell.artifact_name for cell in out]
    logs = [cell.log_root for cell in out]
    for label, values in (("result_roots", roots), ("artifacts", artifacts), ("logs", logs)):
        if len(set(values)) != len(values):
            raise ContractViolation(f"non-unique {label}: {values}")
    return tuple(out)


def assert_unique_roots(cells: Sequence[StressCell]) -> dict[str, int]:
    """Acceptance helper: uniqueness counts for root families."""
    mapping = {
        "unique_result_roots": len({c.result_root for c in cells}),
        "unique_shard_roots": len({c.shard_root for c in cells}),
        "unique_log_roots": len({c.log_root for c in cells}),
        "n_cells": len(cells),
    }
    if any(value != len(cells) for value in list(mapping.values())[:-1]):
        raise AdapterError(f"stress roots are not unique: {mapping}")
    return mapping


__all__ = [
    "BASELINE_NAME",
    "StressCell",
    "STRESS_SURFACE_VARIANTS",
    "assert_unique_roots",
    "build_stress_spec",
    "stress_matrix_cells",
]
