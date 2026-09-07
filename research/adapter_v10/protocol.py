"""Generic V10 strategy-to-research adapter protocol (sprint V10P-R, G1).

This module freezes the family-neutral interface required by PLAN.md section 6
("audit-only adapter contract"). Every shared/adapter type lives here and in
the sibling generic modules; a strategy joins the research pipeline ONLY by
implementing :class:`ResearchStrategy` (directly or through
:class:`research.adapter_v10.base.GenericStrategyBase`).

Contract items (PLAN section 6) and where they are encoded:

* strategy identity/config + immutable schedule provider  -> :class:`StrategyIdentity`,
  :class:`ImmutableSchedule`;
* universe, decision clock, strict-later fills, holding spans -> :class:`FillRecord`,
  :class:`PositionSpan`, :meth:`ResearchStrategy.universe`,
  :meth:`ResearchStrategy.fills_at`;
* chronological folds + purge/embargo + force-flat boundary ->
  :class:`FoldSpec`, :meth:`ResearchStrategy.folds`;
* per-symbol settlements + funding sign convention ->
  :class:`SettlementPoint`, ``identity.funding_sign_convention``;
* costs + named stress variants -> :class:`CostModel`, :class:`StressSpec`,
  :meth:`ResearchStrategy.baseline_stress`;
* baseline/context providers -> :mod:`research.adapter_v10.benchmarks`
  fed from :class:`MarkProvider`;
* deterministic artifacts/metrics/hashes -> :mod:`research.adapter_v10.metrics`,
  :mod:`research.adapter_v10.runner`;
* trial publication idempotency -> :mod:`research.adapter_v10.publish`.

No module inside this package may hard-code a family identifier, an arm
identifier or a fixed trial identifier; strategy-specific strings enter only
through plugin-supplied payloads (enforced by
``tests/test_adapter_v10_g1.py::test_generic_paths_free_of_family_tokens``).
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence, Tuple, runtime_checkable

#: Mark provider: ``(symbols, instant_ns) -> {symbol: price or None}``.
MarkProviderCallable = Callable[[Sequence[str], int], Mapping[str, Optional[float]]]

#: Package schema version (G1 lane deliverable).
SCHEMA_VERSION = "v10.adapter.g1.v1"

#: Default ceiling on the absolute single-symbol weight of any research book.
#: Strategies may pass a stricter cap; nothing here loosens one.
DEFAULT_WEIGHT_CAP_MAX = 0.30

#: Tolerance for float comparisons of weights / gross targets.
WEIGHT_TOL = 1e-9


class AdapterError(ValueError):
    """Base class for every fail-closed adapter condition."""


class ContractViolation(AdapterError):
    """A plugin/config payload contradicts the frozen generic contract."""


class DataUnavailable(AdapterError):
    """A required price/settlement/fill observation is missing -- fail closed."""


# --------------------------------------------------------------------------- #
# Identity / configuration
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StrategyIdentity:
    """Plugin-declared identity payload.

    Every field is supplied BY the strategy plugin: the shared code never
    derives, defaults to or compares against a concrete family/arm value.
    """

    strategy_id: str
    family_id: str
    arm_config_id: str
    direction: str
    window_start_iso: str
    window_end_iso: str
    #: Symbols kept OUT of the tradeable universe and used only as benchmark
    #: context inputs (context-only legs never appear as positions).
    benchmark_symbols_excluded: Tuple[str, ...] = ()
    #: Funding sign vocabulary declared by the strategy, e.g. the repo-wide
    #: "LONG_PAYS_POSITIVE_RATE" token carried verbatim from its own module.
    funding_sign_convention: str = "LONG_PAYS_POSITIVE_RATE"
    #: Optional cohort hint used ONLY at publication time for matrix-id naming.
    matrix_cohort_hint: str = ""
    config: Mapping[str, Any] = field(default_factory=dict)
    #: Explicit arm identifier (V11P lane A2).  Empty for legacy V10 identities;
    #: v2 publication keys refuse to key a trial without one (fail closed).
    #: The canonical score-affecting arm digest lives in
    #: :mod:`research.v11.publication_identity` so this frozen contract only
    #: carries the declaration.
    arm_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "strategy_id",
            "family_id",
            "arm_config_id",
            "direction",
            "window_start_iso",
            "window_end_iso",
        ):
            if not str(getattr(self, name)).strip():
                raise ContractViolation(f"identity.{name} must be non-empty")
        if not isinstance(self.config, Mapping):
            raise ContractViolation("identity.config must be a mapping")
        if str(self.arm_id) != str(self.arm_id).strip():
            raise ContractViolation("identity.arm_id must not be padded with whitespace")

    def public_payload(self) -> dict[str, Any]:
        """Hashable, JSON-safe view used inside deterministic artifacts."""
        return {
            "strategy_id": self.strategy_id,
            "family_id": self.family_id,
            "arm_config_id": self.arm_config_id,
            "direction": self.direction,
            "window_start_iso": self.window_start_iso,
            "window_end_iso": self.window_end_iso,
            "benchmark_symbols_excluded": list(self.benchmark_symbols_excluded),
            "funding_sign_convention": self.funding_sign_convention,
            "config": _json_safe(self.config),
        }


def _json_safe(value: Any) -> Any:
    """Recursively convert tuples/lists/mappings into plain JSON containers."""
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ContractViolation("non-finite float cannot be serialized")
        return value
    return str(value)


# --------------------------------------------------------------------------- #
# Stress surface
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StressSpec:
    """One named cell of the preregistered stress surface.

    The generic layer owns only the vocabulary below; the numbers come from
    each strategy's cost model so a stress cell stays a pure parameter change.
    """

    name: str
    fee_multiplier: float = 1.0
    tick_slip_ticks: int = 0
    event_delay_events: int = 0
    drop_symbols: Tuple[str, ...] = ()
    dropped_fold_index: Optional[int] = None

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise ContractViolation("stress.name must be non-empty")
        if float(self.fee_multiplier) <= 0.0:
            raise ContractViolation("stress.fee_multiplier must be positive")
        if int(self.tick_slip_ticks) < 0 or int(self.event_delay_events) < 0:
            raise ContractViolation(
                "stress tick/event delays must be non-negative integers"
            )

    @property
    def is_baseline(self) -> bool:
        return self.name == BASELINE_NAME

    @property
    def key(self) -> str:
        """Deterministic artifact/root slug derived from the variant name."""
        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-")
        slug = "".join(ch if ch in allowed else "_" for ch in self.name.strip().lower())
        if not slug or slug.startswith("-"):
            slug = f"cell_{slug}"
        return slug[:64]

    def signature(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fee_multiplier": float(self.fee_multiplier),
            "tick_slip_ticks": int(self.tick_slip_ticks),
            "event_delay_events": int(self.event_delay_events),
            "drop_symbols": sorted(str(s) for s in self.drop_symbols),
            "dropped_fold_index": (
                None if self.dropped_fold_index is None else int(self.dropped_fold_index)
            ),
        }


#: Name reserved for the unstressed reference cell (never a family token).
BASELINE_NAME = "baseline"


# --------------------------------------------------------------------------- #
# Costs / settlements / fills / folds
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CostModel:
    """Per-strategy transaction-cost declaration (floors, never invented)."""

    taker_fee_bps: float
    adverse_tick_slip_floor: int
    default_tick_sizes: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.taker_fee_bps)) or float(self.taker_fee_bps) < 0.0:
            raise ContractViolation("cost.taker_fee_bps must be finite non-negative")
        if int(self.adverse_tick_slip_floor) < 0:
            raise ContractViolation("cost.adverse_tick_slip_floor must be >= 0")


@dataclass(frozen=True)
class SettlementPoint:
    """One native settlement instant for ONE symbol."""

    publish_ts_ns: int
    value: float
    kind: str = "info"

    def __post_init__(self) -> None:
        if int(self.publish_ts_ns) <= 0:
            raise ContractViolation("settlement publish_ts_ns must be positive")
        if not math.isfinite(float(self.value)):
            raise ContractViolation("settlement rate must be finite")


class FillStatusVocabulary:
    """Repo-wide fill-status tokens (mirrors the panel module's sweep rows)."""

    APPLIED = "FILLED_NEXT_EVENT"
    NO_EVENT = "NO_EVENT_AT_BOUNDARY"


@dataclass(frozen=True)
class FillRecord:
    """One strict-later fill attempt at one decision instant."""

    symbol: str
    decision_ns: int
    status: str = FillStatusVocabulary.NO_EVENT
    applied: bool = False
    price: Optional[float] = None
    fill_open_ns: Optional[int] = None
    fill_bar_close_ns: Optional[int] = None
    event_offset: int = 0

    def __post_init__(self) -> None:
        if not str(self.symbol):
            raise ContractViolation("fill.symbol must be non-empty")
        if self.applied:
            if self.price is None or not math.isfinite(float(self.price)) or float(self.price) <= 0.0:
                raise ContractViolation(
                    f"applied fill for {self.symbol} needs a finite positive price"
                )
            if self.fill_open_ns is None or self.fill_bar_close_ns is None:
                raise ContractViolation(
                    f"applied fill for {self.symbol} needs open/close stamps"
                )
            if int(self.fill_open_ns) > int(self.fill_bar_close_ns):
                raise ContractViolation("fill open stamp after close stamp")

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "decision_ns": int(self.decision_ns),
            "status": self.status,
            "applied": bool(self.applied),
            "price": self.price,
            "fill_open_ns": self.fill_open_ns,
            "fill_bar_close_ns": self.fill_bar_close_ns,
            "event_offset": int(self.event_offset),
        }


@dataclass(frozen=True)
class TargetBook:
    """Normalised daily target book (signs single-sourced from ``weights``)."""

    decision_ns: int
    status: str
    weights: Tuple[Tuple[str, float], ...]
    longs: Tuple[Tuple[str, float], ...]
    shorts: Tuple[Tuple[str, float], ...]
    carried_forward: bool
    reason_code: Optional[str] = None
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    def as_mapping(self) -> dict[str, float]:
        return {sym: float(w) for sym, w in self.weights}


@dataclass(frozen=True)
class FoldSpec:
    """One chronological fold with its purge posture.

    ``dropped=True`` marks the fold removed by the ``drop_one_fold`` stress
    cell: its decision instants still carry the realized ledger forward but
    contribute to NO scored fold metric, so a dropped fold can never leak
    performance into a surviving one.
    """

    index: int
    label: str
    instants: Tuple[int, ...]
    purge_days: int
    dropped: bool = False

    def __post_init__(self) -> None:
        if int(self.index) < 0:
            raise ContractViolation("fold.index must be non-negative")
        ordered = tuple(int(v) for v in self.instants)
        if len(ordered) == 0:
            raise ContractViolation(f"fold {self.label!r} has no instants")
        if list(ordered) != sorted(set(ordered)):
            raise ContractViolation(f"fold {self.label!r} instants must be strictly increasing")

    @property
    def start_ns(self) -> int:
        return int(self.instants[0])

    @property
    def end_ns(self) -> int:
        return int(self.instants[-1])


@dataclass(frozen=True)
class ImmutableSchedule:
    """Immutable decision-instant provider (sorted UTC epoch nanoseconds)."""

    instants: Tuple[int, ...]
    source: str
    clock: str = ""

    def __post_init__(self) -> None:
        values = tuple(int(v) for v in self.instants)
        if len(values) < 2:
            raise ContractViolation(
                "schedule needs at least two instants (open + final force-flat)"
            )
        if list(values) != sorted(set(values)):
            raise ContractViolation("schedule instants must be strictly increasing")
        object.__setattr__(self, "instants", values)
        if not str(self.source).strip():
            raise ContractViolation("schedule.source must be named")

    @property
    def sha256(self) -> str:
        canonical = ",".join(str(v) for v in self.instants)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def __iter__(self):
        return iter(self.instants)

    def __len__(self) -> int:
        return len(self.instants)


@dataclass(frozen=True)
class PositionSpan:
    """Held signed weight over ``(start_ns, end_ns]`` — funding accrual input."""

    symbol: str
    signed_weight: float
    start_ns: int
    end_ns: int

    def __post_init__(self) -> None:
        if int(self.end_ns) < int(self.start_ns):
            raise ContractViolation(f"span end before start for {self.symbol}")


# --------------------------------------------------------------------------- #
# Strategy protocol
# --------------------------------------------------------------------------- #
@runtime_checkable
class ResearchStrategy(Protocol):
    """The only way a strategy enters the research pipeline.

    Implementations are expected to be immutable views over pre-loaded data;
    nothing in this protocol mutates shared production state.
    """

    def identity(self) -> StrategyIdentity: ...

    def cost_model(self) -> CostModel: ...

    def baseline_stress(self) -> StressSpec: ...

    def schedule(self) -> ImmutableSchedule: ...

    def universe(self, stress: StressSpec) -> Tuple[str, ...]: ...

    def benchmark_context_symbols(self) -> Tuple[str, ...]: ...

    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]: ...

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> Tuple[FillRecord, ...]: ...

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]: ...

    def folds(self, *, stress: StressSpec, instants: Sequence[int]) -> Tuple[FoldSpec, ...]: ...

    def settlements(self, symbol: str) -> Tuple[SettlementPoint, ...]: ...

    def funding_cashflows_for_spans(
        self, spans: Sequence[PositionSpan]
    ) -> list[dict[str, Any]]: ...

    def rebalance_cost_between(
        self,
        previous: Mapping[str, float],
        new: Mapping[str, float],
        *,
        prices: Mapping[str, float],
        stress: StressSpec,
    ) -> float: ...
