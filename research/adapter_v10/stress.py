"""BG4 -- preregistered stress-matrix driver (G1).

Builds the named stress surface from the repo-wide frozen vocabulary in
``research.contract_v10.STRESS_MATRIX_V10`` (five cells + baseline = six) and
maps every cell onto a :class:`research.adapter_v10.protocol.StressSpec`
supplied by the calling strategy. Each cell gets its own artifact file and its
own unique result/shard/log root; uniqueness is asserted, never assumed.

V12P A4 repairs (lessons_register.json, read-only reference):

* ``L-V11-1`` -- the generic six-cell surface is a SUPERSET of what frozen
  family ``folds()`` contracts accept (LOT refuses any dropped fold).  The
  per-family cell list is now DERIVED from that frozen contract
  (:func:`probe_family_dropped_fold_support` +
  :func:`derive_family_stress_matrix`); unsupported cells are excluded AND
  recorded.  The legacy full-superset behaviour is preserved unchanged for
  callers that do not declare the family contract (the frozen V10/V11
  drivers), so existing contracts and tests stay reproducible.
* ``L-V11-7`` -- the ``drop_one_symbol`` diagnostic previously dropped the
  lexicographically-first candidate, which could be an UNHELD symbol and made
  the cell vacuous.  When the realized book is supplied
  (``realized_weights=``), the dropped symbol is now the HELD symbol with the
  LARGEST absolute realized weight, tie-broken by the lexicographically
  smallest symbol id among exact ties; an unheld symbol can never be chosen.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    AdapterError,
    ContractViolation,
    StressSpec,
    WEIGHT_TOL,
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

#: Minimum realized ``|weight|`` for a symbol to count as HELD by the
#: drop-one-symbol diagnostic.  Mirrors the adapter's own zero-flush
#: tolerance in :func:`research.adapter_v10.converters.normalise_target_book`,
#: so "held" here means exactly "the normalised book carries a position".
HELD_WEIGHT_TOL = WEIGHT_TOL


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
    realized_weights: Optional[Mapping[str, float]] = None,
    supported_cells: Optional[Sequence[str]] = None,
) -> StressSpec:
    """Map one named cell onto a strategy's own cost floor declaration.

    ``droppable_symbols`` is the strategy's tradeable cohort.  For the
    ``drop_one_symbol`` cell the dropped symbol comes from
    :func:`select_drop_one_symbol`: with ``realized_weights`` supplied it is
    the largest-|weight| HELD symbol (L-V11-7); without them the frozen
    legacy sorted-first fallback applies (callers holding a book MUST pass
    ``realized_weights``).

    ``supported_cells`` is the family-declared cell vocabulary (derived from
    the frozen ``folds()`` contract, L-V11-1).  Requesting a cell outside it
    fails closed instead of silently launching an unsupported cell; the
    baseline reference cell is always accepted.
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
    if supported_cells is not None:
        supported = {str(cell) for cell in supported_cells}
        if name not in supported:
            raise ContractViolation(
                f"stress cell {name!r} is not in the family-declared supported cells "
                f"{sorted(supported)}; the generic superset must not launch unsupported cells"
            )
    symbol_to_drop = _single_symbol_for_cell(
        droppable_symbols, name, realized_weights=realized_weights
    )
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


def select_drop_one_symbol(
    *,
    droppable_symbols: Sequence[str],
    realized_weights: Optional[Mapping[str, float]] = None,
) -> tuple[str, ...]:
    """Deterministic drop-one-symbol target (L-V11-7 repair).

    With ``realized_weights`` (the realized book at the cell's decision
    stamp): the HELD symbol with the LARGEST absolute realized weight is
    dropped; exact ties are broken by the lexicographically smallest symbol
    id.  A symbol that is unheld (absent from the book, or ``|w|`` within the
    adapter's zero-flush tolerance) can never be selected; a weight that
    references a symbol outside the declared droppable cohort fails closed.

    Without ``realized_weights`` the frozen legacy V10/V11 driver fallback
    applies (first sorted candidate) -- there is no realized book in that
    frozen call signature, so that path is unchanged for reproducibility.
    """
    if realized_weights is None:
        ordered = sorted(str(s) for s in droppable_symbols)
        if not ordered:
            raise ContractViolation(
                "drop_one_symbol requires the strategy to declare at least one droppable symbol"
            )
        return (ordered[0],)
    cohort = {str(s) for s in droppable_symbols}
    weights: dict[str, float] = {}
    for sym, weight in dict(realized_weights).items():
        weights[str(sym)] = float(weight)
    unknown = sorted(set(weights) - cohort)
    if unknown:
        raise ContractViolation(
            f"realized weights reference symbols outside the droppable cohort: {unknown}"
        )
    held = {sym: abs(w) for sym, w in weights.items() if abs(w) > HELD_WEIGHT_TOL}
    if not held:
        raise ContractViolation(
            "drop_one_symbol found no held symbol (|w| > HELD_WEIGHT_TOL); "
            "refusing to select an unheld symbol (L-V11-7)"
        )
    largest = max(held.values())
    tied = sorted(sym for sym, value in held.items() if value == largest)
    return (tied[0],)


def _single_symbol_for_cell(
    candidates: Sequence[str], cell: str, *, realized_weights: Optional[Mapping[str, float]] = None
) -> tuple[str, ...]:
    """Deterministic drop-one-symbol target for one cell (see
    :func:`select_drop_one_symbol`)."""
    if cell != "drop_one_symbol":
        return ()
    return select_drop_one_symbol(
        droppable_symbols=candidates, realized_weights=realized_weights
    )


def probe_family_dropped_fold_support(
    *,
    baseline_stress: StressSpec,
    folds,
    instants: Sequence[int],
) -> bool:
    """Probe the family's FROZEN ``folds()`` contract for the drop_one_fold cell.

    Frozen V11 driver semantics preserved exactly: the baseline spec is
    re-labelled ``drop_one_fold`` with ``dropped_fold_index=0`` and fed to the
    family ``folds()``; ANY exception means the contract refuses the cell.
    A baseline that cannot be re-labelled (``TypeError``) is reported as
    supported.  ``instants`` must be the family's own schedule instants so a
    false refusal (an unrelated empty-schedule violation) cannot occur.
    """
    if not list(instants):
        raise ContractViolation(
            "probe_family_dropped_fold_support needs the family schedule instants"
        )
    try:
        probe = dataclasses.replace(
            baseline_stress, name="drop_one_fold", dropped_fold_index=0
        )
    except TypeError:
        return True
    try:
        folds(stress=probe, instants=list(instants))
    except Exception:
        return False
    return True


def stress_matrix_cells(
    *,
    strategy_baseline: StressSpec,
    droppable_symbols: Sequence[str] = (),
    realized_weights: Optional[Mapping[str, float]] = None,
    supported_cells: Optional[Sequence[str]] = None,
    exclusion_record: Optional[dict] = None,
) -> tuple[StressCell, ...]:
    """The stress matrix: baseline plus every frozen variant, in order.

    Default (``supported_cells=None``) reproduces the frozen six-cell
    superset unchanged.  With ``supported_cells`` (the family-declared
    vocabulary, L-V11-1) unsupported frozen variants are EXCLUDED and
    recorded into ``exclusion_record`` (caller-embeddable preflight payload)
    instead of silently launching.
    """
    excluded: dict[str, str] = {}
    if supported_cells is None:
        cells = [BASELINE_NAME, *STRESS_SURFACE_VARIANTS]
    else:
        supported = {str(cell) for cell in supported_cells}
        cells = [BASELINE_NAME] + [name for name in STRESS_SURFACE_VARIANTS if name in supported]
        excluded = {
            name: "NOT_IN_FAMILY_DECLARED_SUPPORTED_CELLS"
            for name in STRESS_SURFACE_VARIANTS
            if name not in supported
        }
    out: list[StressCell] = []
    for name in cells:
        spec = build_stress_spec(
            name,
            strategy_baseline=strategy_baseline,
            droppable_symbols=droppable_symbols,
            realized_weights=realized_weights,
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
    if exclusion_record is not None and excluded:
        exclusion_record.update(excluded)
    return tuple(out)


@dataclass(frozen=True)
class StressMatrixDerivation:
    """Per-family stress matrix plus its preflight-embeddable record."""

    cells: tuple[StressCell, ...]
    record: dict


def derive_family_stress_matrix(
    *,
    strategy_baseline: StressSpec,
    droppable_symbols: Sequence[str] = (),
    realized_weights: Optional[Mapping[str, float]] = None,
    folds=None,
    instants: Sequence[int] = (),
    supported_cells: Optional[Sequence[str]] = None,
) -> StressMatrixDerivation:
    """L-V11-1: derive the per-family cell list FROM the frozen family contract.

    Either probe the family ``folds()`` contract directly (``folds`` +
    ``instants``; the frozen LOT/ILLIQ/OILEV plugins) or accept an explicit
    ``supported_cells`` declaration -- never both.  The generic six-cell
    superset is the universe; cells the family contract does not accept are
    excluded from the matrix AND recorded in the returned record (embed it in
    preflight).  The baseline reference cell is always present and first.
    """
    probe_accepted: Optional[bool] = None
    if folds is not None:
        if supported_cells is not None:
            raise ContractViolation(
                "derive_family_stress_matrix accepts either folds+instants or "
                "supported_cells, never both"
            )
        probe_accepted = probe_family_dropped_fold_support(
            baseline_stress=strategy_baseline, folds=folds, instants=instants
        )
        supported_cells = (
            STRESS_SURFACE_VARIANTS
            if probe_accepted
            else tuple(name for name in STRESS_SURFACE_VARIANTS if name != "drop_one_fold")
        )
    if supported_cells is None:
        raise ContractViolation(
            "derive_family_stress_matrix needs the frozen family folds() contract "
            "(folds + instants) or an explicit supported_cells declaration"
        )
    exclusion_record: dict = {}
    cells = stress_matrix_cells(
        strategy_baseline=strategy_baseline,
        droppable_symbols=droppable_symbols,
        realized_weights=realized_weights,
        supported_cells=supported_cells,
        exclusion_record=exclusion_record,
    )
    record = {
        "schema": "v12.stress_matrix_derivation.v1",
        "generic_superset_cells": [BASELINE_NAME, *STRESS_SURFACE_VARIANTS],
        "derived_matrix_cells": [cell.name for cell in cells],
        "excluded_cells": dict(exclusion_record),
        "folds_contract_probe_accepts_drop_one_fold": probe_accepted,
        "drop_one_symbol_uses_realized_weights": realized_weights is not None,
    }
    return StressMatrixDerivation(cells=cells, record=record)


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
    "HELD_WEIGHT_TOL",
    "StressCell",
    "StressMatrixDerivation",
    "STRESS_SURFACE_VARIANTS",
    "assert_unique_roots",
    "build_stress_spec",
    "derive_family_stress_matrix",
    "probe_family_dropped_fold_support",
    "select_drop_one_symbol",
    "stress_matrix_cells",
]
