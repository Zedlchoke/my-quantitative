"""Hard-gate evaluation (G0..G5) using only contract thresholds/reason codes.

Sprint V3 (PLAN sections 9-11):

* G1 REQUIRES runner-emitted :class:`contracts.protocol.LeakageEvidence`.
  There are NO hard-coded booleans in the scored path: missing/incomplete
  evidence => INCONCLUSIVE (``g1_evidence_missing``); a scored entry with
  ``fill_ts <= signal_ts`` => FAIL (``signal_fill_ordering_violation``).
* G2 is split into TWO separate rows:
  - ``G2A_ARTIFACT_INTEGRITY`` from :class:`ArtifactIntegrityResult`
    (hashes/schema/reconciliation of existing artifacts);
  - ``G2B_INDEPENDENT_REPRODUCIBILITY`` from
    :class:`IndependentReproductionResult` (a NEW backtest process launched
    from frozen inputs). No independent rerun => NOT_YET_TESTED.
  Promotion requires BOTH G2a and G2b PASS (:func:`g2_promotion_pass`).
* ``evaluate_gates`` emits seven fixed rows: G0, G1, G2A, G2B, G3, G4, G5.

Sprint V2 fail-closed rules retained (PLAN section 9):

* G0 requires a REAL coverage payload (dict from the data-contract artifact).
  A missing/malformed payload is ``INCONCLUSIVE`` +
  ``g0_coverage_not_evidenced`` -- never an automatic PASS.
* G3 with fewer than the minimum trades per symbol is ``INCONCLUSIVE``
  (``trades_below_min``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from contracts.protocol import (
    FOLD_PF_FLOOR,
    FOLD_PF_FLOOR_MIN_TRADES,
    MAX_SINGLE_FOLD_CONTRIBUTION,
    MAX_SYMBOL_CONTRIBUTION,
    PORTFOLIO_MIN_PF,
    REASON_CODES,
    STAGE_A_MIN_PF,
    STAGE_A_MIN_POSITIVE_FOLD_RATIO,
    STAGE_A_MIN_TRADES_PER_SYMBOL,
    ArtifactIntegrityResult,
    GateId,
    GateResult,
    GateVerdict,
    IndependentReproductionResult,
    LeakageEvidence,
    require_reason,
)


# --------------------------------------------------------------------------- #
# Sprint V4 XG gates (PLAN sections 23-24; owner A3).
#
# ``XG_GATE_IDS`` / portfolio constraint thresholds are frozen by A1 in
# ``contracts.protocol``; until that lands this module carries a verbatim
# PLAN-section-23 fallback and PREFERS the contract constants when present.
# New reason codes needed by the XG evaluators are registered into the shared
# contract registry at import time (additive; existing codes untouched).
# --------------------------------------------------------------------------- #
XG_REASON_CODES: dict[str, str] = {
    "sample_below_min": "fewer than 30 scored rebalances or 100 closed legs",
    "beta_exposure_fail": "abs realized BTC beta > 0.25 (PLAN section 23 XG5)",
    "parameter_spike_fail": "fewer than two adjacent lookbacks with positive expectancy",
    "slippage_stress_negative": "two-tick adverse fill stress expectancy-R non-positive",
    "mdd_lock_blocker": "max drawdown > 10% blocks S1 lock even when XG5 passes",
    "feature_lookahead_detected": "feature bars were not completed before the signal",
    "execution_bar_in_lookback": "execution-bar return included in ranking lookback",
    "membership_nondeterministic": "cross-sectional membership/tie handling nondeterministic",
}
REASON_CODES.update(XG_REASON_CODES)

# --------------------------------------------------------------------------- #
# Sprint V5 reason semantics (PLAN section 31.2 items 6-8; owner A3).
#
# F08 fix: ABSENCE of evidence is never a negative result.  A stress check
# that did NOT execute emits ``not_tested``; a metric that could not be
# computed emits ``metric_missing``; only an EXECUTED-and-negative stress may
# emit ``<name>_negative``.  Fail-closed verdicts are unchanged -- we only
# stop conflating "not tested" with "tested and failed".
# --------------------------------------------------------------------------- #
V5_REASON_CODES: dict[str, str] = {
    "not_tested": "check was not executed; absence of evidence is not a negative result",
    "metric_missing": "required metric absent from artifact (fail-closed)",
    "evidence_missing": "measured evidence rows absent from ledger (fail-closed)",
    "not_applicable_with_reason": "check not applicable to this experiment; explicit reason recorded",
    "median_fold_return_nonpositive": "median across per-fold returns is non-positive",
    "artifact_schema_invalid": "experiment artifact missing required schema fields",
    "artifact_hash_mismatch": "recomputed sha256 differs from artifact_hashes.json listing",
    "artifact_hashes_stale": "artifact_hashes.json is not the newest file; post-hash write detected",
    "unlisted_artifact_file": "file present on disk but absent from artifact_hashes.json listing",
}
REASON_CODES.update(V5_REASON_CODES)


class ReasonSemantics(str, Enum):
    """Enum-like reason codes distinguishing absence from negative results."""

    NOT_TESTED = "not_tested"
    METRIC_MISSING = "metric_missing"

    @staticmethod
    def stress_negative(stress_name: str) -> str:
        """Reason code for an EXECUTED-and-NEGATIVE stress (e.g. ``fee``)."""
        if not stress_name or not str(stress_name).strip():
            raise ValueError("stress name required for *_negative reason")
        return f"{str(stress_name).strip()}_negative"


#: Module-level aliases used across gate evaluators.
NOT_TESTED = ReasonSemantics.NOT_TESTED.value
METRIC_MISSING = ReasonSemantics.METRIC_MISSING.value


def STRESS_NEGATIVE(name: str) -> str:
    """Executed-negative stress reason ``<name>_negative`` (e.g. fee_stress_negative)."""
    return ReasonSemantics.stress_negative(name)

try:  # A1-owned frozen constants win when available.
    from contracts.protocol import XG_GATE_IDS as _CONTRACT_XG_GATE_IDS  # type: ignore
except ImportError:  # pragma: no cover - fallback until A1 contracts land
    _CONTRACT_XG_GATE_IDS = None


class XGateId(str, Enum):
    """Row identifiers emitted by :func:`evaluate_xgates` (V4 layout)."""

    XG0_DATA_UNIVERSE = "XG0_DATA_UNIVERSE"
    XG1_POINT_IN_TIME = "XG1_POINT_IN_TIME"
    XG2A_ARTIFACT_INTEGRITY = "XG2A_ARTIFACT_INTEGRITY"
    XG2B_INDEPENDENT_REPRODUCIBILITY = "XG2B_INDEPENDENT_REPRODUCIBILITY"
    XG3_STAGE_A_PORTFOLIO = "XG3_STAGE_A_PORTFOLIO"
    XG4_ROBUSTNESS_EXECUTION = "XG4_ROBUSTNESS_EXECUTION"
    XG5_SHARED_CAPITAL_RISK = "XG5_SHARED_CAPITAL_RISK"


#: Frozen gate-id strings for V4 (contract override or local enum values).
XG_GATE_IDS_LOCAL: tuple[str, ...] = tuple(g.value for g in XGateId)
XG_GATE_IDS: tuple[str, ...] = (
    tuple(_CONTRACT_XG_GATE_IDS) if _CONTRACT_XG_GATE_IDS else XG_GATE_IDS_LOCAL
)


def _portfolio_constraint(name: str, default: float) -> float:
    """Read an A1-frozen PORTFOLIO_CONSTRAINTS entry when it exists."""
    try:
        from contracts.protocol import PORTFOLIO_CONSTRAINTS as _PC  # type: ignore
    except ImportError:
        return default
    value = (_PC or {}).get(name)
    return float(value) if value is not None else default


class PortfolioConstraints:
    """Verbatim Sprint V4 thresholds (PLAN section 23; contract override wins)."""

    MIN_POSITION_PF = _portfolio_constraint("min_position_pf", PORTFOLIO_MIN_PF)  # 1.10
    MAX_GROSS_EXPOSURE = _portfolio_constraint("max_gross_exposure", 1.0)
    MAX_ABS_NET_EXPOSURE = _portfolio_constraint("max_abs_net_exposure", 0.10)
    MAX_ABS_WEIGHT_PER_SYMBOL = _portfolio_constraint(
        "max_abs_weight_per_symbol", 0.25
    )
    MAX_TOP_FOLD_CONTRIBUTION = _portfolio_constraint(
        "max_top_fold_contribution", 0.50
    )  # of positive-aggregate PnL
    MAX_TOP_SYMBOL_CONTRIBUTION = MAX_SYMBOL_CONTRIBUTION  # 0.40 positive-agg share
    MIN_SCORED_REBALANCES = int(_portfolio_constraint("min_scored_rebalances", 30))
    MIN_CLOSED_LEGS = int(_portfolio_constraint("min_closed_legs", 100))
    MIN_POSITIVE_FOLDS = int(_portfolio_constraint("min_positive_folds", 2))  # of 3
    MAX_ABS_BTC_BETA = _portfolio_constraint("max_abs_btc_beta", 0.25)
    MDD_LOCK_LIMIT = _portfolio_constraint("mdd_lock_limit", 0.10)  # lock-condition only
    OUTER_FOLDS = 3


class ProtocolGateId(str, Enum):
    """Row identifiers emitted by :func:`evaluate_gates` (V3 layout).

    ``contracts.protocol.GateId`` is frozen by A1 and still carries the
    legacy combined ``G2_REPRODUCIBILITY`` member; V3 replaces it with the
    explicit pair below (clean replacement per Sprint V3 brief).
    """

    G0_DATA = "G0_DATA"
    G1_LEAKAGE = "G1_LEAKAGE"
    G2A_ARTIFACT_INTEGRITY = "G2A_ARTIFACT_INTEGRITY"
    G2B_INDEPENDENT_REPRODUCIBILITY = "G2B_INDEPENDENT_REPRODUCIBILITY"
    G3_STAGE_A = "G3_STAGE_A"
    G4_SURVIVOR_ROBUSTNESS = "G4_SURVIVOR_ROBUSTNESS"
    G5_PORTFOLIO = "G5_PORTFOLIO"


EVALUATION_ORDER: tuple[ProtocolGateId, ...] = tuple(ProtocolGateId)

#: ``execution_ordering.evidence_class`` value meaning every scored entry
#: carried complete signal/submit/fill evidence with zero violations.
#: Canonical constants live here so runner and evaluator share one source.
EXECUTION_EVIDENCE_COMPLETE = "EXECUTION_EVIDENCE_COMPLETE"
EVIDENCE_MISSING = "EVIDENCE_MISSING"
ORDERING_VIOLATION_DETECTED = "ORDERING_VIOLATION_DETECTED"

#: Required keys of ``LeakageEvidence.warmup_boundaries`` / ``universe_freeze``
#: / ``execution_ordering`` for the evidence to count as complete.
WARMUP_BOUNDARY_KEYS = ("warmup_start", "scored_start", "scored_end")
UNIVERSE_FREEZE_KEYS = ("candidate_locked_at_utc", "universe_sha256", "launch_commit")

# ------------------------- G0 payload requirements -------------------------- #
#: Keys every per-symbol entry of a real G0 coverage payload must carry.
REQUIRED_COVERAGE_SYMBOL_KEYS = frozenset(
    ("bars", "instrument_metadata_present", "funding")
)
#: Keys the per-symbol ``bars`` block must carry.
REQUIRED_COVERAGE_BARS_KEYS = frozenset(
    ("duplicate_timestamps", "gaps_over_interval")
)
#: Keys the per-symbol ``funding`` block must carry.
REQUIRED_COVERAGE_FUNDING_KEYS = frozenset(
    ("bundle_present", "covers_declared_window")
)

#: Sprint V2 LEGACY G1 evidence keys (dict-shaped; v1/v2 evaluator paths only).
G1_REQUIRED_EVIDENCE_KEYS = frozenset(
    (
        "split_policy_declared",
        "warmup_outside_window",
        "transforms_fit_on_train",
        "universe_frozen_before_run",
        "execution_model_declared",
    )
)


@dataclass(frozen=True)
class DataGateInput:
    """G0 inputs: audited claim booleans + the real coverage payload.

    ``coverage_payload`` is the raw data-contract artifact dict (e.g.
    ``results/matrix/<audit>/coverage.json``).  When it is missing or lacks
    required keys G0 is INCONCLUSIVE (fail-closed); when present, duplicate /
    gap / funding / metadata reasons are derived FROM it.  Explicit boolean
    overrides remain available for auditors recording additional findings.
    """

    duplicates_present: bool = False
    unexplained_gaps: bool = False
    funding_coverage_complete: bool = True
    instrument_metadata_ok: bool = True
    catalog_current: bool = True
    coverage_ratio: float | None = None
    coverage_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class LeakageGateInput:
    """G1 inputs (V2 LEGACY shape): violation flags + mandatory evidence dict.

    ``evidence`` must carry every key of ``G1_REQUIRED_EVIDENCE_KEYS`` with a
    non-null value (booleans or proof dicts).  Missing/null keys yield
    INCONCLUSIVE + ``g1_evidence_missing`` (the fact is not evidenced).  A
    key present but explicitly ``False`` means the claim is contradicted and
    maps to the corresponding leakage FAIL reason where one exists.

    Sprint V3 scored paths MUST use :class:`RunnerLeakageGateInput` instead:
    gates no longer accept hand-built booleans for promotion decisions.
    """

    scored_fold_in_selection: bool = False
    warmup_inside_window: bool = False
    universe_not_frozen: bool = False
    posthoc_regime_gate: bool = False
    split_policy_declared: bool = True
    evidence: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RunnerLeakageGateInput:
    """G1 inputs (V3): REQUIRES runner-emitted LeakageEvidence.

    The evaluator never fabricates lock timestamps, warmup boundaries or
    execution-ordering counts; it only judges what the runner emitted.
    Additional auditor findings may still be recorded through the violation
    flags (each maps to its FAIL reason code).
    """

    evidence: LeakageEvidence | None = None
    scored_fold_in_selection: bool = False
    warmup_inside_window: bool = False
    universe_not_frozen: bool = False
    posthoc_regime_gate: bool = False


@dataclass(frozen=True)
class RerunComparison:
    performed: bool = False
    matches: bool | None = None
    reasons: tuple[str, ...] = ()
    config_hash_matches: bool | None = None


@dataclass(frozen=True)
class ReproGateInput:
    manifest_complete: bool
    rerun: RerunComparison = field(default_factory=RerunComparison)


@dataclass(frozen=True)
class ReproductionComparison:
    """Sprint V2 G2 comparison struct: frozen manifest vs independent rerun.

    Any hash pair mismatch is ALWAYS a FAIL (``hash_mismatch``) -- even when
    the canonical PnL coincidentally matches (no benign interpretation).
    Position-digest and canonical-PnL mismatches fail with their own reason
    codes; PnL comparison uses a relative tolerance.
    """

    config_sha256_expected: str | None = None
    config_sha256_actual: str | None = None
    candidate_sha256_expected: str | None = None
    candidate_sha256_actual: str | None = None
    data_manifest_sha256_expected: str | None = None
    data_manifest_sha256_actual: str | None = None
    positions_digest_original: str | None = None
    positions_digest_rerun: str | None = None
    canonical_pnl_original: float | None = None
    canonical_pnl_rerun: float | None = None
    pnl_rtol: float = 1e-6
    rerun_performed: bool = True

    def _hash_pairs(self) -> tuple[tuple[str, Any, Any], ...]:
        return (
            ("config", self.config_sha256_expected, self.config_sha256_actual),
            ("candidate", self.candidate_sha256_expected, self.candidate_sha256_actual),
            ("data_manifest", self.data_manifest_sha256_expected, self.data_manifest_sha256_actual),
        )

    def evaluate(self) -> GateResult:
        return evaluate_reproduction(self)


@dataclass(frozen=True)
class FoldRow:
    fold_id: str
    trades: int
    pnl_after_cost: float
    exp_after_cost: float | None = None
    pf_after_cost: float | None = None


@dataclass(frozen=True)
class SymbolRow:
    symbol: str
    trades: int
    pnl_after_cost: float
    exp_after_cost: float | None = None
    pf_after_cost: float | None = None


def _coerce_rows(rows: Iterable[dict], cls) -> list:
    coerced = []
    for row in rows:
        coerced.append(cls(**row) if isinstance(row, dict) else row)
    return coerced


@dataclass(frozen=True)
class StageAInput:
    exp_after_cost: float | None
    pf_after_cost: float | None
    total_trades: int | None = None
    folds: Sequence[FoldRow | dict] = ()
    symbols: Sequence[SymbolRow | dict] = ()
    top_fold_contribution_pct: float | None = None  # fraction or percent

    def __post_init__(self):
        object.__setattr__(
            self, "folds", tuple(_coerce_rows(self.folds, FoldRow))
        )
        object.__setattr__(
            self, "symbols", tuple(_coerce_rows(self.symbols, SymbolRow))
        )


@dataclass(frozen=True)
class SurvivorInput:
    """Each ``*_positive`` / ``*_detected`` check is tri-state:

    ``True``/``False`` = executed result, ``None`` = check not performed.
    G4 can only PASS when every check was executed and clean; the engine has
    no two-tick slippage model this sprint, so a clean run still carries the
    informational reason ``slippage_stress_not_implemented``.
    """

    fee_stress_positive: bool | None = None
    delay_stress_positive: bool | None = None
    delay_stress_supported: bool = False
    neighborhood_spike_detected: bool | None = None
    dropone_signflip_detected: bool | None = None


@dataclass(frozen=True)
class PortfolioInput:
    portfolio_pnl: float | None = None
    portfolio_pf: float | None = None
    limits_ok: bool = True
    max_symbol_contribution_pct: float | None = None  # fraction or percent


@dataclass(frozen=True)
class GateInputs:
    data: DataGateInput | None = None
    leakage: LeakageGateInput | RunnerLeakageGateInput | None = None
    artifact_integrity: ArtifactIntegrityResult | None = None
    independent_reproduction: IndependentReproductionResult | None = None
    reproducibility: ReproGateInput | None = None  # legacy (V2)
    reproduction: ReproductionComparison | None = None  # legacy (V2)
    stage_a: StageAInput | None = None
    survivor: SurvivorInput | None = None
    portfolio: PortfolioInput | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "GateInputs":
        mapping = {
            "data": DataGateInput,
            "leakage": None,  # dispatched below (legacy vs runner evidence)
            "reproducibility": ReproGateInput,
            "reproduction": ReproductionComparison,
            "stage_a": StageAInput,
            "survivor": SurvivorInput,
            "portfolio": PortfolioInput,
        }
        kwargs: dict[str, Any] = {}
        for key, sub_cls in mapping.items():
            value = payload.get(key)
            if value is None:
                continue
            if key == "leakage":
                kwargs[key] = _coerce_leakage(value)
                continue
            kwargs[key] = sub_cls(**value) if isinstance(value, dict) else value
        for key in ("artifact_integrity", "independent_reproduction"):
            value = payload.get(key)
            if value is not None:
                kwargs[key] = value
        return cls(**kwargs)


def _coerce_leakage(value: Any) -> LeakageGateInput | RunnerLeakageGateInput:
    """Accept a runner LeakageEvidence, a plain dict, or a ready input."""
    if isinstance(value, RunnerLeakageGateInput):
        return value
    if isinstance(value, LeakageEvidence):
        return RunnerLeakageGateInput(evidence=value)
    if isinstance(value, Mapping):
        if isinstance(value.get("evidence"), LeakageEvidence):
            return RunnerLeakageGateInput(
                evidence=value["evidence"],
                scored_fold_in_selection=bool(value.get("scored_fold_in_selection")),
                warmup_inside_window=bool(value.get("warmup_inside_window")),
                universe_not_frozen=bool(value.get("universe_not_frozen")),
                posthoc_regime_gate=bool(value.get("posthoc_regime_gate")),
            )
        return LeakageGateInput(**value)
    raise TypeError(f"unsupported leakage input: {type(value)!r}")


def _normalize_fraction(value: float | None) -> float | None:
    """Accept both fraction (0.5) and percent (50.0) notations."""
    if value is None:
        return None
    return value / 100.0 if value > 1.0 else value


def _g0_payload_problem(section: DataGateInput) -> str | None:
    """Return the reason a coverage payload is not real evidence, else None."""
    payload = section.coverage_payload
    if not isinstance(payload, Mapping):
        return "missing"
    symbols = payload.get("symbols")
    if not isinstance(symbols, Mapping) or not symbols:
        return "empty"
    for symbol, entry in symbols.items():
        if not isinstance(entry, Mapping):
            return f"symbol:{symbol}"
        missing = REQUIRED_COVERAGE_SYMBOL_KEYS.difference(entry)
        if missing:
            return f"symbol:{symbol}:{sorted(missing)}"
        bars = entry.get("bars")
        if not isinstance(bars, Mapping) or REQUIRED_COVERAGE_BARS_KEYS.difference(bars):
            return f"symbol:{symbol}:bars"
        funding = entry.get("funding")
        if not isinstance(funding, Mapping) or REQUIRED_COVERAGE_FUNDING_KEYS.difference(funding):
            return f"symbol:{symbol}:funding"
    return None


def _g0_payload_reasons(payload: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    symbols = payload["symbols"]
    if any(
        int(entry["bars"].get("duplicate_timestamps") or 0) > 0
        for entry in symbols.values()
    ):
        reasons.append("duplicate_bars")
    if any(
        int(entry["bars"].get("gaps_over_interval") or 0) > 0
        for entry in symbols.values()
    ):
        reasons.append("unexplained_gap")
    if any(
        entry["funding"].get("bundle_present") is not True
        or entry["funding"].get("covers_declared_window") is not True
        for entry in symbols.values()
    ):
        reasons.append("funding_coverage_insufficient")
    # NOTE: per-symbol ``coverage_ratio`` decimals (e.g. 0.9995 from bundle
    # edge rounding) are informational; completeness is asserted by
    # ``covers_declared_window``. Auditors can still force a
    # ``coverage_below_declared`` via ``DataGateInput.coverage_ratio``.
    if any(entry.get("instrument_metadata_present") is not True for entry in symbols.values()):
        reasons.append("missing_instrument_metadata")
    return reasons


def _evaluate_g0(section: DataGateInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G0_DATA, GateVerdict.NOT_APPLICABLE)

    # Fail-closed: no REAL coverage artifact => INCONCLUSIVE, never PASS.
    problem = _g0_payload_problem(section)
    if problem is not None:
        return GateResult(
            GateId.G0_DATA,
            GateVerdict.INCONCLUSIVE,
            ("g0_coverage_not_evidenced",),
        )

    reasons = _g0_payload_reasons(section.coverage_payload)

    # Explicit auditor overrides / additional findings.
    if section.duplicates_present and "duplicate_bars" not in reasons:
        reasons.append("duplicate_bars")
    if section.unexplained_gaps and "unexplained_gap" not in reasons:
        reasons.append("unexplained_gap")
    if section.coverage_ratio is not None and section.coverage_ratio < 1.0 and (
        "coverage_below_declared" not in reasons
    ):
        reasons.append("coverage_below_declared")
    if not section.funding_coverage_complete and "funding_coverage_insufficient" not in reasons:
        reasons.append("funding_coverage_insufficient")
    if not section.instrument_metadata_ok and "missing_instrument_metadata" not in reasons:
        reasons.append("missing_instrument_metadata")
    if not section.catalog_current:
        reasons.append("catalog_not_current")

    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return GateResult(GateId.G0_DATA, verdict, tuple(dict.fromkeys(reasons)))


def _evaluate_g1(
    section: LeakageGateInput | RunnerLeakageGateInput | None,
) -> GateResult:
    if section is None:
        return GateResult(ProtocolGateId.G1_LEAKAGE, GateVerdict.NOT_APPLICABLE)

    violation_reasons = [
        code
        for attr, code in (
            ("scored_fold_in_selection", "scored_fold_in_selection"),
            ("warmup_inside_window", "warmup_inside_window"),
            ("universe_not_frozen", "universe_not_frozen"),
            ("posthoc_regime_gate", "posthoc_regime_gate"),
        )
        if getattr(section, attr)
    ]

    if isinstance(section, RunnerLeakageGateInput):
        return _evaluate_g1_runner_evidence(section, violation_reasons)
    return _evaluate_g1_legacy_evidence(section, violation_reasons)


def _missing_subkey(block: Any, keys: Sequence[str]) -> bool:
    return not isinstance(block, Mapping) or any(
        block.get(key) is None for key in keys
    )


def _g1_runner_missing(evidence: LeakageEvidence) -> list[str]:
    """Reason codes for every incomplete piece of runner G1 evidence."""
    problems: list[str] = []
    missing = evidence.missing_keys()
    if missing:
        problems.append("g1_evidence_missing")
    if evidence.split_policy_declared is None:
        problems.append("g1_evidence_missing")
    warmup = evidence.warmup_boundaries
    if _missing_subkey(warmup, WARMUP_BOUNDARY_KEYS):
        problems.append("g1_evidence_missing")
    transform = evidence.transform_evidence
    # Never a bare boolean: learned transforms need fit proof; stateless
    # indicator pipelines need an explicit NOT_APPLICABLE + reason.
    if (
        not isinstance(transform, Mapping)
        or "status" not in transform
        or transform.get("status") == "NOT_APPLICABLE"
        and not transform.get("reason")
    ):
        problems.append("g1_evidence_missing")
    if _missing_subkey(evidence.universe_freeze, UNIVERSE_FREEZE_KEYS):
        problems.append("g1_evidence_missing")
    ordering = evidence.execution_ordering
    if not isinstance(ordering, Mapping) or not ordering.get("evidence_class"):
        problems.append("g1_evidence_missing")
    elif ordering.get("evidence_class") != EXECUTION_EVIDENCE_COMPLETE:
        problems.append("g1_evidence_missing")
    return sorted(set(problems))


def _evaluate_g1_runner_evidence(
    section: RunnerLeakageGateInput, violation_reasons: list[str]
) -> GateResult:
    evidence = section.evidence
    if evidence is None:
        return GateResult(
            ProtocolGateId.G1_LEAKAGE,
            GateVerdict.INCONCLUSIVE,
            (require_reason("g1_evidence_missing"),),
        )
    reasons = list(violation_reasons)

    missing = _g1_runner_missing(evidence)
    ordering = (
        evidence.execution_ordering
        if isinstance(evidence.execution_ordering, Mapping)
        else {}
    )
    violations = int(ordering.get("violations") or 0)
    if violations > 0:
        reasons.append(require_reason("signal_fill_ordering_violation"))
    reasons.extend(code for code in missing if code not in reasons)
    # An explicitly DECLARED-FALSE split policy is a hard FAIL; a null/absent
    # one is merely missing evidence (handled by _g1_runner_missing).
    if evidence.split_policy_declared is False and "split_policy_missing" not in reasons:
        reasons.append("split_policy_missing")

    if violations > 0 or any(code != "g1_evidence_missing" for code in reasons):
        return GateResult(
            ProtocolGateId.G1_LEAKAGE, GateVerdict.FAIL, tuple(dict.fromkeys(reasons))
        )
    if reasons:  # only g1_evidence_missing left
        return GateResult(
            ProtocolGateId.G1_LEAKAGE, GateVerdict.INCONCLUSIVE, tuple(reasons)
        )
    return GateResult(ProtocolGateId.G1_LEAKAGE, GateVerdict.PASS)


def _evaluate_g1_legacy_evidence(
    section: LeakageGateInput, violation_reasons: list[str]
) -> GateResult:
    evidence = section.evidence
    # Fail-closed: protocol claims without an explicit evidence dict are
    # INCONCLUSIVE (never auto-PASS from defaults).
    if not isinstance(evidence, Mapping) or G1_REQUIRED_EVIDENCE_KEYS.difference(evidence) or any(
        evidence.get(key) is None for key in G1_REQUIRED_EVIDENCE_KEYS
    ):
        return GateResult(
            ProtocolGateId.G1_LEAKAGE,
            GateVerdict.INCONCLUSIVE,
            tuple(dict.fromkeys((*violation_reasons, require_reason("g1_evidence_missing")))),
        )

    reasons = list(violation_reasons)

    # Contradicted evidence claims map to their leakage FAIL codes.
    contradicted = {
        "split_policy_declared": "split_policy_missing",
        "warmup_outside_window": "warmup_inside_window",
        "universe_frozen_before_run": "universe_not_frozen",
    }
    for key, code in contradicted.items():
        if evidence.get(key) is False and code not in reasons:
            reasons.append(code)

    if not section.split_policy_declared and "split_policy_missing" not in reasons:
        reasons.append("split_policy_missing")

    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return GateResult(ProtocolGateId.G1_LEAKAGE, verdict, tuple(dict.fromkeys(reasons)))


def evaluate_reproduction(comparison: ReproductionComparison) -> GateResult:
    """Sprint V2 G2 verdict from a frozen-vs-rerun comparison struct.

    Precedence (all fail-closed):

    1. rerun not performed          -> NOT_YET_TESTED
    2. missing expected/actual hash -> FAIL ``manifest_missing_field``
    3. ANY hash mismatch            -> FAIL ``hash_mismatch`` (ALWAYS, even if
                                       PnL matches -- no benign interpretation)
    4. positions digest mismatch    -> FAIL ``positions_digest_mismatch``
    5. canonical PnL beyond rtol    -> FAIL ``rerun_pnl_mismatch``
    6. otherwise                    -> PASS
    """
    if not comparison.rerun_performed:
        return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.NOT_YET_TESTED)

    reasons: list[str] = []
    for name, expected, actual in comparison._hash_pairs():
        if not expected or not actual:
            reasons.append("manifest_missing_field")
        elif str(expected) != str(actual):
            reasons.append("hash_mismatch")

    digests = (
        comparison.positions_digest_original,
        comparison.positions_digest_rerun,
    )
    if all(digests) and str(digests[0]) != str(digests[1]):
        reasons.append(require_reason("positions_digest_mismatch"))

    pnls = (comparison.canonical_pnl_original, comparison.canonical_pnl_rerun)
    if all(value is not None for value in pnls):
        original, rerun = float(pnls[0]), float(pnls[1])
        scale = max(1.0, abs(original), abs(rerun))
        if abs(original - rerun) > comparison.pnl_rtol * scale:
            reasons.append("rerun_pnl_mismatch")

    if reasons:
        return GateResult(
            GateId.G2_REPRODUCIBILITY, GateVerdict.FAIL, tuple(dict.fromkeys(reasons))
        )
    return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.PASS)


def _evaluate_g2a(section: ArtifactIntegrityResult | None) -> GateResult:
    """G2A row: artifact integrity (hashes/schema/reconciliation)."""
    if section is None:
        return GateResult(
            ProtocolGateId.G2A_ARTIFACT_INTEGRITY, GateVerdict.NOT_APPLICABLE
        )
    return GateResult(
        ProtocolGateId.G2A_ARTIFACT_INTEGRITY, section.verdict(), tuple(section.reasons)
    )


def _evaluate_g2b(section: IndependentReproductionResult | None) -> GateResult:
    """G2B row: independent reproducibility (new process from frozen inputs).

    No independent rerun => NOT_YET_TESTED; promotion then stays blocked.
    """
    if section is None:
        return GateResult(
            ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY, GateVerdict.NOT_APPLICABLE
        )
    return GateResult(
        ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY,
        section.verdict(),
        tuple(section.reasons),
    )


def g2_promotion_pass(g2a: GateResult, g2b: GateResult) -> bool:
    """Promotion requires BOTH G2a AND G2b PASS (PLAN section 9 G2)."""
    return (
        g2a.gate == ProtocolGateId.G2A_ARTIFACT_INTEGRITY
        and g2b.gate == ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY
        and g2a.verdict is GateVerdict.PASS
        and g2b.verdict is GateVerdict.PASS
    )


def _evaluate_g3(section: StageAInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G3_STAGE_A, GateVerdict.NOT_APPLICABLE)
    reasons: list[str] = []

    if section.exp_after_cost is None or section.pf_after_cost is None:
        return GateResult(GateId.G3_STAGE_A, GateVerdict.NOT_YET_TESTED, ("metric_not_computed",))

    if section.exp_after_cost <= 0:
        reasons.append("exp_nonpositive")
    if section.pf_after_cost < STAGE_A_MIN_PF:
        reasons.append("pf_below_min")

    folds = list(section.folds)
    positive = [f for f in folds if (f.pnl_after_cost or 0) > 0]
    if folds and len(positive) / len(folds) < STAGE_A_MIN_POSITIVE_FOLD_RATIO:
        reasons.append("positive_folds_ratio_low")

    for fold in folds:
        if (
            fold.trades >= FOLD_PF_FLOOR_MIN_TRADES
            and fold.pf_after_cost is not None
            and fold.pf_after_cost < FOLD_PF_FLOOR
        ):
            reasons.append("fold_pf_below_floor")
            break

    contribution = _normalize_fraction(section.top_fold_contribution_pct)
    if contribution is None and folds:
        total = sum((f.pnl_after_cost or 0) for f in folds)
        if total > 0:
            contribution = max(abs(f.pnl_after_cost) for f in folds) / total
    if contribution is not None and contribution > MAX_SINGLE_FOLD_CONTRIBUTION:
        reasons.append("fold_concentration_high")

    symbols = list(section.symbols)
    if symbols:
        weak_symbols = [
            s
            for s in symbols
            if s.exp_after_cost is not None and s.exp_after_cost <= 0
        ]
        if weak_symbols and section.exp_after_cost > 0:
            reasons.append("symbol_masked_by_average")
        min_symbol_trades = min(s.trades for s in symbols)
    else:
        min_symbol_trades = section.total_trades or 0

    trade_shortfall = min_symbol_trades < STAGE_A_MIN_TRADES_PER_SYMBOL

    hard_fail_codes = {
        "exp_nonpositive",
        "pf_below_min",
        "positive_folds_ratio_low",
        "fold_pf_below_floor",
        "fold_concentration_high",
        "symbol_masked_by_average",
    }
    if hard_fail_codes.intersection(reasons):
        return GateResult(GateId.G3_STAGE_A, GateVerdict.FAIL, tuple(dict.fromkeys(reasons)))
    if trade_shortfall:
        # Sprint V2 PLAN section 9 G3: "<20 trades per required symbol =>
        # INCONCLUSIVE" (fail-closed; never an automatic PASS).
        return GateResult(
            GateId.G3_STAGE_A, GateVerdict.INCONCLUSIVE, ("trades_below_min",)
        )
    return GateResult(GateId.G3_STAGE_A, GateVerdict.PASS)


def _evaluate_g4(section: SurvivorInput | None) -> GateResult:
    if section is None:
        return GateResult(
            GateId.G4_SURVIVOR_ROBUSTNESS,
            GateVerdict.NOT_IMPLEMENTED,
            ("slippage_stress_not_implemented",),
        )
    reasons: list[str] = []
    pending: list[str] = []
    # V5 semantics (F08): an UNEXECUTED stress is "not_tested"; only an
    # executed-and-negative stress earns its *_negative FAIL reason.
    if section.fee_stress_positive is False:
        reasons.append(STRESS_NEGATIVE("fee_stress"))
    elif section.fee_stress_positive is None:
        pending.append(NOT_TESTED)

    if section.delay_stress_positive is False:
        reasons.append(STRESS_NEGATIVE("delay_stress"))
    elif section.delay_stress_supported and section.delay_stress_positive is None:
        pending.append(NOT_TESTED)

    if section.neighborhood_spike_detected is True:
        reasons.append("neighborhood_spike")
    elif section.neighborhood_spike_detected is None:
        pending.append("neighborhood_spike")

    if section.dropone_signflip_detected is True:
        reasons.append("dropone_signflip")
    elif section.dropone_signflip_detected is None:
        pending.append("dropone_signflip")

    if reasons:
        return GateResult(GateId.G4_SURVIVOR_ROBUSTNESS, GateVerdict.FAIL, tuple(reasons))
    if pending:
        return GateResult(
            GateId.G4_SURVIVOR_ROBUSTNESS,
            GateVerdict.NOT_IMPLEMENTED,
            tuple(dict.fromkeys(pending)),
        )
    extra = () if section.delay_stress_supported else ("slippage_stress_not_implemented",)
    return GateResult(GateId.G4_SURVIVOR_ROBUSTNESS, GateVerdict.PASS, extra)


def _evaluate_g5(section: PortfolioInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G5_PORTFOLIO, GateVerdict.NOT_APPLICABLE)
    if section.portfolio_pnl is None and section.portfolio_pf is None:
        return GateResult(GateId.G5_PORTFOLIO, GateVerdict.NOT_APPLICABLE)
    reasons: list[str] = []
    if section.portfolio_pnl is not None and section.portfolio_pnl <= 0:
        reasons.append("portfolio_pnl_nonpositive")
    if section.portfolio_pf is not None and section.portfolio_pf < PORTFOLIO_MIN_PF:
        reasons.append("portfolio_pf_below_min")
    if not section.limits_ok:
        reasons.append("limit_violation")
    contribution = _normalize_fraction(section.max_symbol_contribution_pct)
    if contribution is not None and contribution > MAX_SYMBOL_CONTRIBUTION:
        reasons.append("symbol_contribution_high")
    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return GateResult(GateId.G5_PORTFOLIO, verdict, tuple(reasons))


def evaluate_gates(inputs: GateInputs | dict) -> list[GateResult]:
    """Evaluate every hard gate in fixed V3 order.

    Seven rows: G0, G1, G2A, G2B, G3, G4, G5.  The legacy combined
    ``G2_REPRODUCIBILITY`` row is replaced by the separate
    ``G2A_ARTIFACT_INTEGRITY`` / ``G2B_INDEPENDENT_REPRODUCIBILITY`` pair;
    promotion requires BOTH to PASS (:func:`g2_promotion_pass`).

    ``inputs.artifact_integrity`` / ``inputs.independent_reproduction`` take
    the contract result dataclasses directly.  The legacy Sprint V2
    ``reproducibility`` / ``reproduction`` sections are still accepted and
    mapped onto the two new rows (v1/v2 evaluator compatibility): legacy G2
    hash/manifest findings feed G2a, rerun findings feed G2b.
    """
    if isinstance(inputs, dict):
        inputs = GateInputs.from_dict(inputs)

    if inputs.artifact_integrity is not None:
        g2a = _evaluate_g2a(inputs.artifact_integrity)
    elif inputs.reproducibility is not None or inputs.reproduction is not None:
        # Legacy mapping: manifest/hash completeness -> artifact integrity.
        reasons: list[str] = []
        hashes_ok = True
        if inputs.reproduction is not None:
            comparison = inputs.reproduction
            for _name, expected, actual in comparison._hash_pairs():
                if not expected or not actual:
                    reasons.append("manifest_missing_field")
                    hashes_ok = False
                elif str(expected) != str(actual):
                    reasons.append("hash_mismatch")
                    hashes_ok = False
        if inputs.reproducibility is not None:
            if not inputs.reproducibility.manifest_complete:
                reasons.append("manifest_missing_field")
                hashes_ok = False
            if inputs.reproducibility.rerun.config_hash_matches is False:
                reasons.append("hash_mismatch")
                hashes_ok = False
        verdict = GateVerdict.FAIL if not hashes_ok else GateVerdict.PASS
        g2a = GateResult(
            ProtocolGateId.G2A_ARTIFACT_INTEGRITY,
            verdict,
            tuple(dict.fromkeys(reasons)),
        )
    else:
        g2a = GateResult(
            ProtocolGateId.G2A_ARTIFACT_INTEGRITY, GateVerdict.NOT_APPLICABLE
        )

    if inputs.independent_reproduction is not None:
        g2b = _evaluate_g2b(inputs.independent_reproduction)
    elif inputs.reproduction is not None:
        # Legacy V2 comparison struct -> independent-rerun verdict mapping.
        cmp = inputs.reproduction
        if not cmp.rerun_performed:
            g2b = GateResult(
                ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY,
                GateVerdict.NOT_YET_TESTED,
            )
        else:
            hashes_equal = all(
                expected and actual and str(expected) == str(actual)
                for _n, expected, actual in cmp._hash_pairs()
            )
            digests = (cmp.positions_digest_original, cmp.positions_digest_rerun)
            digest_match = bool(
                all(digests) and str(digests[0]) == str(digests[1])
            ) if all(digests) else False
            pnls = (cmp.canonical_pnl_original, cmp.canonical_pnl_rerun)
            pnl_match = False
            if all(value is not None for value in pnls):
                original, rerun = float(pnls[0]), float(pnls[1])
                scale = max(1.0, abs(original), abs(rerun))
                pnl_match = abs(original - rerun) <= cmp.pnl_rtol * scale
            g2b = GateResult(
                ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY,
                (
                    GateVerdict.PASS
                    if hashes_equal and digest_match and pnl_match
                    else GateVerdict.FAIL
                ),
                ()
                if hashes_equal and digest_match and pnl_match
                else ("hash_mismatch",) if not hashes_equal
                else ("positions_digest_mismatch",) if not digest_match
                else ("rerun_pnl_mismatch",),
            )
    else:
        g2b = GateResult(
            ProtocolGateId.G2B_INDEPENDENT_REPRODUCIBILITY,
            GateVerdict.NOT_APPLICABLE,
        )

    return [
        _evaluate_g0(inputs.data),
        _evaluate_g1(inputs.leakage),
        g2a,
        g2b,
        _evaluate_g3(inputs.stage_a),
        _evaluate_g4(inputs.survivor),
        _evaluate_g5(inputs.portfolio),
    ]


# --------------------------------------------------------------------------- #
# Sprint V4 XG gate evaluators (PLAN section 23; owner A3).
# Fail-closed everywhere: missing evidence is INCONCLUSIVE, never PASS.
# --------------------------------------------------------------------------- #

#: Keys every per-symbol entry of the XG0 panel-coverage payload must carry.
XG0_TRADED_SYMBOL_KEYS = frozenset(("days_present",))
#: Optional per-symbol bar-quality counters (when present, zero is required).
XG0_OPTIONAL_BAR_COUNTERS = ("duplicate_bars", "gap_bars")
#: Required keys of the XG0 benchmark (BTC) block.
XG0_BENCHMARK_KEYS = frozenset(("symbol", "days_present", "clean"))
#: XG1 point-in-time evidence struct keys (PLAN section 23 XG1).
XG1_EVIDENCE_KEYS = frozenset(
    (
        "features_completed_before_signal",
        "signal_before_every_fill",
        "membership_tie_deterministic",
        "execution_bar_excluded",
        "warmup_boundaries",
    )
)


@dataclass(frozen=True)
class XStageAInput:
    """XG3 inputs: portfolio Stage-A edge metrics.

    Sprint V5 (PLAN 31.4 / F07 fix): the gate uses ONLY measured family
    metrics -- after-cost total pnl, position PF, MEDIAN FOLD RETURN and the
    positive-folds ratio.  ``expectancy_r`` is accepted for artifact
    compatibility but is DEPRECATED and never gated on: a stop-less shared
    capital portfolio has no R normalization, so any portfolio-level R would
    be fabricated.
    """

    pnl: float | None = None
    pf: float | None = None
    pf_reason: str | None = None
    expectancy_r: float | None = None  # deprecated; ignored by V5 gate logic
    fold_returns: Sequence[float] | None = None
    folds: Sequence[Mapping[str, Any]] | Sequence[object] = ()  # {fold_id,pnl}
    rebalances_scored: int | None = None
    legs_closed: int | None = None
    top_fold_contribution: float | None = None  # fraction or percent
    top_symbol_contribution: float | None = None  # fraction or percent


@dataclass(frozen=True)
class XRobustnessInput:
    """XG4 inputs; ``None`` means the check was NOT executed (tri-state)."""

    fee50_exp_r: float | None = None
    twotick_exp_r: float | None = None
    extradelay_exp_r: float | None = None
    dropone_symbol_clean: bool | None = None
    dropone_fold_clean: bool | None = None
    turnover_budget_exceeded: bool | None = None


@dataclass(frozen=True)
class XRiskInput:
    """XG5 inputs: shared-capital risk constraints (PLAN section 23)."""

    gross_max: float | None = None
    net_abs_max: float | None = None
    max_abs_weight: float | None = None
    margin_breach_rows: int | None = None
    top_symbol_contribution: float | None = None  # fraction or percent
    realized_beta: float | None = None
    mdd_fraction: float | None = None


@dataclass(frozen=True)
class XGateInputs:
    """All evaluator sections; a missing section yields NOT_APPLICABLE.

    V5 measured-evidence fields (F16): when ``execution_ledger_rows`` is
    provided, XG1 is evaluated by COUNTING violations from those artifact
    rows (:func:`evaluate_xg1_measured`) instead of trusting the legacy
    ``pit_evidence`` boolean struct.  ``transform_registry`` carries the
    actual transform fit registry (empty -> not_applicable_with_reason).
    """

    coverage: Mapping[str, Any] | None = None
    declared_symbols: Sequence[str] | None = None
    pit_evidence: Mapping[str, Any] | None = None
    execution_ledger_rows: Iterable[Mapping[str, Any]] | None = None
    transform_registry: Mapping[str, Any] | None = None
    warmup_boundaries: Mapping[str, Any] | None = None
    artifact_integrity: ArtifactIntegrityResult | None = None
    independent_reproduction: IndependentReproductionResult | None = None
    stage_a: XStageAInput | None = None
    robustness: XRobustnessInput | None = None
    risk: XRiskInput | None = None

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "XGateInputs":
        known = set(cls.__dataclass_fields__)
        kwargs = dict(payload)
        for key in ("stage_a", "robustness", "risk"):
            if isinstance(kwargs.get(key), Mapping):
                sub_cls = {"stage_a": XStageAInput, "robustness": XRobustnessInput,
                           "risk": XRiskInput}[key]
                kwargs[key] = sub_cls(**kwargs[key])
        for key in ("artifact_integrity", "independent_reproduction"):
            value = kwargs.get(key)
            if isinstance(value, Mapping):
                sub_cls = (ArtifactIntegrityResult if key == "artifact_integrity"
                           else IndependentReproductionResult)
                kwargs[key] = sub_cls(**value)
        return cls(**{k: v for k, v in kwargs.items() if k in known})


def _xg_result(gate: XGateId, verdict: GateVerdict, reasons: Sequence[str] = ()) -> GateResult:
    return GateResult(gate, verdict, tuple(dict.fromkeys(reasons)))


def _evaluate_xg0(section: XGateInputs) -> GateResult:
    payload = section.coverage
    problem: str | None = None
    if not isinstance(payload, Mapping):
        problem = "missing"
    else:
        symbols = payload.get("traded_symbols")
        required_days = payload.get("required_days")
        benchmark = payload.get("benchmark")
        if not isinstance(symbols, Mapping) or not symbols:
            problem = "empty_symbols"
        elif not isinstance(required_days, (int, float)) or required_days <= 0:
            problem = "required_days"
        elif not isinstance(benchmark, Mapping) or XG0_BENCHMARK_KEYS.difference(benchmark):
            problem = "benchmark"
        else:
            for symbol, entry in symbols.items():
                if not isinstance(entry, Mapping) or XG0_TRADED_SYMBOL_KEYS.difference(entry):
                    problem = f"symbol:{symbol}"
                    break
    if problem is not None:
        return _xg_result(
            XGateId.XG0_DATA_UNIVERSE,
            GateVerdict.INCONCLUSIVE,
            (require_reason("g0_coverage_not_evidenced"),),
        )

    reasons: list[str] = []
    required_days_num = float(payload["required_days"])
    symbols_block: Mapping[str, Any] = payload["traded_symbols"]
    for symbol, entry in sorted(symbols_block.items()):
        days = float(entry.get("days_present") or 0)
        if days < required_days_num:
            reasons.append("coverage_below_declared")
        for counter in XG0_OPTIONAL_BAR_COUNTERS:
            if counter in entry and int(entry[counter] or 0) > 0:
                reasons.append(
                    "duplicate_bars" if counter == "duplicate_bars" else "unexplained_gap"
                )
    benchmark = payload["benchmark"]
    if benchmark.get("clean") is not True or float(benchmark.get("days_present") or 0) <= 0:
        # BTC clean coverage missing => diagnostic-only context (section 19.3).
        reasons.append("funding_coverage_insufficient")
    if section.declared_symbols is not None:
        declared = {str(s) for s in section.declared_symbols}
        if declared != set(map(str, symbols_block)):
            reasons.append("coverage_below_declared")
    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return _xg_result(XGateId.XG0_DATA_UNIVERSE, verdict, reasons)


def _evaluate_xg1(evidence: Mapping[str, Any] | None) -> GateResult:
    """LEGACY XG1 path (V4 boolean struct; retained for V4 runner compat).

    Sprint V5 scored paths MUST use :func:`evaluate_xg1_measured`, which
    counts violations from real execution-ledger rows instead of trusting
    hand-built booleans (F16).
    """
    if not isinstance(evidence, Mapping) or XG1_EVIDENCE_KEYS.difference(evidence) or any(
        evidence.get(key) is None for key in XG1_EVIDENCE_KEYS
    ):
        return _xg_result(
            XGateId.XG1_POINT_IN_TIME,
            GateVerdict.INCONCLUSIVE,
            (require_reason("g1_evidence_missing"),),
        )
    warmup = evidence.get("warmup_boundaries")
    if _missing_subkey(warmup, WARMUP_BOUNDARY_KEYS):
        return _xg_result(
            XGateId.XG1_POINT_IN_TIME,
            GateVerdict.INCONCLUSIVE,
            (require_reason("g1_evidence_missing"),),
        )
    reasons: list[str] = []
    contradiction_map = {
        "features_completed_before_signal": "feature_lookahead_detected",
        "execution_bar_excluded": "execution_bar_in_lookback",
        "membership_tie_deterministic": "membership_nondeterministic",
    }
    for key, code in contradiction_map.items():
        if evidence.get(key) is False:
            reasons.append(code)
    if evidence.get("signal_before_every_fill") is False:
        reasons.append(require_reason("signal_fill_ordering_violation"))
    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return _xg_result(XGateId.XG1_POINT_IN_TIME, verdict, reasons)


# --------------------------------------------------------------------------- #
# Sprint V5 MEASURED XG1 (PLAN 31.2 item 8 / F16 fix): evidence is COUNTED
# from artifact execution-ledger rows -- never accepted as booleans.
# --------------------------------------------------------------------------- #
#: Accepted timestamp field names inside an execution ledger row.
XG1_SIGNAL_TS_KEYS = ("signal_ts", "signal_ts_utc", "signal_ts_ns")
XG1_FILL_TS_KEYS = ("fill_ts", "fill_ts_utc", "fill_ts_ns")


@dataclass(frozen=True)
class ExecutionEvidenceCounters:
    """Counts recomputed FROM artifact rows (never runner-declared)."""

    entries: int
    violations: int
    missing_ts: int

    def to_dict(self) -> dict[str, int]:
        return {
            "entries": self.entries,
            "violations": self.violations,
            "missing_ts": self.missing_ts,
        }


def _first_present(row: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def count_execution_evidence(
    rows: Iterable[Mapping[str, Any]] | None,
) -> ExecutionEvidenceCounters:
    """Count entries/ordering-violations/missing-timestamps from REAL rows.

    A row counts as a violation when ``fill_ts <= signal_ts`` (scored entry
    filled before or at its signal); a row missing either timestamp counts
    toward ``missing_ts`` and can never be judged a violation.
    """
    entries = violations = missing_ts = 0
    for row in rows or ():
        if not isinstance(row, Mapping):
            raise TypeError(f"execution ledger row must be a mapping: {row!r}")
        entries += 1
        signal_ts = _first_present(row, XG1_SIGNAL_TS_KEYS)
        fill_ts = _first_present(row, XG1_FILL_TS_KEYS)
        if signal_ts is None or fill_ts is None:
            missing_ts += 1
        elif float(fill_ts) <= float(signal_ts):
            violations += 1
    return ExecutionEvidenceCounters(
        entries=entries, violations=violations, missing_ts=missing_ts
    )


def evaluate_xg1_measured(
    execution_ledger_rows: Iterable[Mapping[str, Any]] | None,
    *,
    transform_registry: Mapping[str, Any] | None = None,
    warmup_boundaries: Mapping[str, Any] | None = None,
) -> GateResult:
    """Measured XG1: ordering evidence counted from artifact rows.

    Fail-closed semantics:

    * rows absent/None/empty      -> INCONCLUSIVE ``evidence_missing`` (F16:
                                     no constant-True PASS without a ledger);
    * any violation (fill<=signal)-> FAIL ``signal_fill_ordering_violation``;
    * any missing timestamps      -> INCONCLUSIVE ``g1_evidence_missing``;
    * otherwise                   -> PASS.

    Transform leakage evidence comes ONLY from the actual transform registry
    passed by the caller: an empty/absent registry is recorded as
    ``not_applicable_with_reason`` (a stateless pipeline has nothing to fit)
    instead of fabricating fit proof.
    """
    if execution_ledger_rows is None:
        return _xg_result(
            XGateId.XG1_POINT_IN_TIME,
            GateVerdict.INCONCLUSIVE,
            (require_reason("evidence_missing"),),
        )
    counters = count_execution_evidence(execution_ledger_rows)
    if counters.entries == 0:
        return _xg_result(
            XGateId.XG1_POINT_IN_TIME,
            GateVerdict.INCONCLUSIVE,
            (require_reason("evidence_missing"),),
        )
    reasons: list[str] = []
    if counters.violations > 0:
        reasons.append(require_reason("signal_fill_ordering_violation"))
    if counters.missing_ts > 0:
        reasons.append(require_reason("g1_evidence_missing"))

    # Transform leakage evidence ONLY from the actual transform registry.
    if not isinstance(transform_registry, Mapping) or not transform_registry:
        reasons.append(require_reason("not_applicable_with_reason"))
    else:
        for name, entry in sorted(transform_registry.items()):
            if not isinstance(entry, Mapping) or (
                entry.get("status") is None and entry.get("fit_on") is None
            ):
                reasons.append(require_reason("g1_evidence_missing"))
                break

    if _missing_subkey(warmup_boundaries, WARMUP_BOUNDARY_KEYS):
        reasons.append(require_reason("g1_evidence_missing"))

    if "signal_fill_ordering_violation" in reasons:
        return _xg_result(XGateId.XG1_POINT_IN_TIME, GateVerdict.FAIL, reasons)
    if any(code != "not_applicable_with_reason" for code in reasons):
        return _xg_result(
            XGateId.XG1_POINT_IN_TIME, GateVerdict.INCONCLUSIVE, reasons
        )
    return _xg_result(XGateId.XG1_POINT_IN_TIME, GateVerdict.PASS, tuple(reasons))


def _fold_pnl(row: Any) -> float | None:
    pnl = getattr(row, "pnl_after_cost", None)
    if pnl is None and hasattr(row, "get"):
        pnl = row.get("pnl")  # type: ignore[attr-defined]
        if pnl is None:
            pnl = row.get("pnl_after_cost")  # type: ignore[attr-defined]
    try:
        return None if pnl is None else float(pnl)
    except (TypeError, ValueError):
        return None


def _evaluate_xg3(section: XStageAInput | None) -> GateResult:
    """Family-aware portfolio gate (V5; PLAN section 31.4, F07 fix).

    Check list -- NO expectancy-R anywhere:

    1. after-cost total pnl > 0;
    2. position PF >= MIN_POSITION_PF (undefined PF blocks with its reason);
    3. median fold RETURN > 0 (``fold_returns`` are required measured
       evidence; absence is INCONCLUSIVE ``metric_missing``, never guessed
       from fold PnL);
    4. positive-folds ratio over fold PnL >= 2/3.
    """
    if section is None:
        return _xg_result(XGateId.XG3_STAGE_A_PORTFOLIO, GateVerdict.NOT_APPLICABLE)

    sample_short = (
        section.rebalances_scored is None
        or section.legs_closed is None
        or int(section.rebalances_scored) < PortfolioConstraints.MIN_SCORED_REBALANCES
        or int(section.legs_closed) < PortfolioConstraints.MIN_CLOSED_LEGS
    )

    reasons: list[str] = []

    if section.pnl is None:
        return _xg_result(
            XGateId.XG3_STAGE_A_PORTFOLIO,
            GateVerdict.INCONCLUSIVE,
            (require_reason("metric_not_computed"),),
        )

    if section.pf is None:
        # Undefined PF (no trades / no losing positions) blocks PASS always.
        reasons.append(require_reason(section.pf_reason or "no_trades"))
    elif section.pf < PortfolioConstraints.MIN_POSITION_PF:
        reasons.append("pf_below_min")

    if section.pnl <= 0:
        reasons.append("portfolio_pnl_nonpositive")

    from research.portfolio_metrics import median_fold_return as _median

    median_return = _median(section.fold_returns or ())
    if median_return is None:
        # Fold returns are required measured evidence; a FAIL already on the
        # books keeps precedence, otherwise this is INCONCLUSIVE.
        if reasons:
            return _xg_result(
                XGateId.XG3_STAGE_A_PORTFOLIO, GateVerdict.FAIL, reasons
            )
        return _xg_result(
            XGateId.XG3_STAGE_A_PORTFOLIO,
            GateVerdict.INCONCLUSIVE,
            (METRIC_MISSING,),
        )
    if median_return <= 0:
        reasons.append("median_fold_return_nonpositive")

    folds = [row for row in (section.folds or [])]
    fold_pnls = [_fold_pnl(row) for row in folds]
    positive_folds = sum(1 for value in fold_pnls if value is not None and value > 0)
    measurable_folds = [v for v in fold_pnls if v is not None]
    if len(measurable_folds) >= PortfolioConstraints.OUTER_FOLDS and (
        positive_folds < PortfolioConstraints.MIN_POSITIVE_FOLDS
    ):
        reasons.append("positive_folds_ratio_low")

    contribution = _normalize_fraction(section.top_fold_contribution)
    if contribution is None and measurable_folds:
        aggregates: dict[str, float] = {}
        for row in folds:
            fold_id = getattr(row, "fold_id", None)
            pnl = getattr(row, "pnl_after_cost", None)
            if pnl is None and hasattr(row, "get"):
                fold_id = row.get("fold_id")  # type: ignore[attr-defined]
                pnl = row.get("pnl")  # type: ignore[attr-defined]
            aggregates[str(fold_id)] = float(pnl or 0.0)
        from research.portfolio_metrics import fold_contribution as _fc

        _top, share = _fc(aggregates)
        contribution = share
    if contribution is not None and contribution > PortfolioConstraints.MAX_TOP_FOLD_CONTRIBUTION:
        reasons.append("fold_concentration_high")

    symbol_share = _normalize_fraction(section.top_symbol_contribution)
    if symbol_share is not None and symbol_share > PortfolioConstraints.MAX_TOP_SYMBOL_CONTRIBUTION:
        reasons.append("symbol_contribution_high")

    if reasons:
        return _xg_result(XGateId.XG3_STAGE_A_PORTFOLIO, GateVerdict.FAIL, reasons)
    if sample_short:
        return _xg_result(XGateId.XG3_STAGE_A_PORTFOLIO, GateVerdict.INCONCLUSIVE,
                          (require_reason("sample_below_min"),))
    return _xg_result(XGateId.XG3_STAGE_A_PORTFOLIO, GateVerdict.PASS)


def evaluate_parameter_spike(
    lookback_expectancy_positive: Mapping[int, bool | None],
) -> GateResult:
    """Adjacent-lookback rule over {3,7,14} (PLAN section 22 H41-H45).

    At least one adjacent pair ``(3,7)`` / ``(7,14)`` must have BOTH members
    with positive after-cost portfolio expectancy; otherwise the surviving
    lookback is an isolated spike => FAIL ``parameter_spike_fail``.  Unknown
    (None / missing) entries make the neighborhood incomplete => INCONCLUSIVE.
    """
    values: dict[int, bool | None] = {}
    for key, value in lookback_expectancy_positive.items():
        values[int(key)] = None if value is None else bool(value)
    for lookback in (3, 7, 14):
        if values.get(lookback) is None:
            return _xg_result(
                XGateId.XG4_ROBUSTNESS_EXECUTION,
                GateVerdict.INCONCLUSIVE,
                (require_reason("metric_not_computed"),),
            )
    adjacent_pairs = ((3, 7), (7, 14))
    if any(values[a] and values[b] for a, b in adjacent_pairs):
        return _xg_result(XGateId.XG4_ROBUSTNESS_EXECUTION, GateVerdict.PASS)
    return _xg_result(
        XGateId.XG4_ROBUSTNESS_EXECUTION,
        GateVerdict.FAIL,
        (require_reason("parameter_spike_fail"),),
    )


def _evaluate_xg4(section: XRobustnessInput | None) -> GateResult:
    if section is None:
        return _xg_result(XGateId.XG4_ROBUSTNESS_EXECUTION, GateVerdict.NOT_APPLICABLE)
    fail_reasons: list[str] = []
    pending: list[str] = []
    # V5 semantics (F08): unexecuted => not_tested; executed-negative only
    # then earns fee_stress_negative / slippage_stress_negative /
    # delay_stress_negative.
    stress_rows = (
        ("fee50_exp_r", STRESS_NEGATIVE("fee_stress")),
        ("twotick_exp_r", STRESS_NEGATIVE("slippage_stress")),
        ("extradelay_exp_r", STRESS_NEGATIVE("delay_stress")),
    )
    for attr, code in stress_rows:
        value = getattr(section, attr)
        if value is None:
            pending.append(NOT_TESTED)
        elif float(value) <= 0:
            fail_reasons.append(code)
    for attr, code in (
        ("dropone_symbol_clean", "dropone_signflip"),
        ("dropone_fold_clean", "dropone_signflip"),
    ):
        value = getattr(section, attr)
        if value is None:
            pending.append(code)
        elif value is False:
            fail_reasons.append(code)
    turnover_flag = section.turnover_budget_exceeded
    if turnover_flag is None:
        pending.append("limit_violation")
    elif turnover_flag is True:
        fail_reasons.append("limit_violation")

    if fail_reasons:
        return _xg_result(XGateId.XG4_ROBUSTNESS_EXECUTION, GateVerdict.FAIL, fail_reasons)
    if pending:
        return _xg_result(XGateId.XG4_ROBUSTNESS_EXECUTION, GateVerdict.INCONCLUSIVE, pending)
    return _xg_result(XGateId.XG4_ROBUSTNESS_EXECUTION, GateVerdict.PASS)


def evaluate_xg5(section: XRiskInput | None) -> tuple[GateResult, dict]:
    """Shared-capital risk gate + lock-condition extras.

    Returns ``(gate_result, details)`` where ``details['mdd_lock_blocker']``
    is True when MDD > 10% (verdict stays PASS with the informational reason
    ``mdd_lock_blocker`` -- drawdown only blocks S1 LOCK, never the row).
    Missing core metrics are INCONCLUSIVE (fail-closed).
    """
    details: dict[str, object] = {"mdd_lock_blocker": None}
    if section is None:
        return _xg_result(XGateId.XG5_SHARED_CAPITAL_RISK, GateVerdict.NOT_APPLICABLE), details
    core_missing = (
        section.gross_max is None
        or section.net_abs_max is None
        or section.max_abs_weight is None
        or section.margin_breach_rows is None
        or section.realized_beta is None
        or section.mdd_fraction is None
        or section.top_symbol_contribution is None
    )
    if core_missing:
        return _xg_result(
            XGateId.XG5_SHARED_CAPITAL_RISK,
            GateVerdict.INCONCLUSIVE,
            (require_reason("metric_not_computed"),),
        ), details

    reasons: list[str] = []
    if float(section.gross_max) > PortfolioConstraints.MAX_GROSS_EXPOSURE:
        reasons.append("limit_violation")
    if abs(float(section.net_abs_max)) > PortfolioConstraints.MAX_ABS_NET_EXPOSURE:
        reasons.append("limit_violation")
    if abs(float(section.max_abs_weight)) > PortfolioConstraints.MAX_ABS_WEIGHT_PER_SYMBOL:
        reasons.append("limit_violation")
    if int(section.margin_breach_rows or 0) > 0:
        reasons.append("limit_violation")
    symbol_share = _normalize_fraction(section.top_symbol_contribution)
    if symbol_share is not None and symbol_share > PortfolioConstraints.MAX_TOP_SYMBOL_CONTRIBUTION:
        reasons.append("symbol_contribution_high")
    beta = float(section.realized_beta)
    if abs(beta) > PortfolioConstraints.MAX_ABS_BTC_BETA:
        reasons.append(require_reason("beta_exposure_fail"))

    mdd = float(section.mdd_fraction)
    if mdd > PortfolioConstraints.MDD_LOCK_LIMIT:
        details["mdd_lock_blocker"] = True
        reasons.append(require_reason("mdd_lock_blocker"))  # informational on PASS
    else:
        details["mdd_lock_blocker"] = False

    verdict = GateVerdict.FAIL if [
        r for r in reasons if r != require_reason("mdd_lock_blocker")
    ] else GateVerdict.PASS
    return _xg_result(XGateId.XG5_SHARED_CAPITAL_RISK, verdict, reasons), details


def evaluate_xgates(inputs: XGateInputs | Mapping[str, Any]) -> list[GateResult]:
    """Evaluate all seven V4 rows in fixed order: XG0..XG5.

    V5: XG1 uses the MEASURED evaluator whenever ``execution_ledger_rows``
    are supplied; the legacy boolean struct path only runs for callers that
    have not migrated (and can never PASS a scored promotion on its own).
    """
    if isinstance(inputs, Mapping):
        inputs = XGateInputs.from_dict(inputs)
    if inputs.execution_ledger_rows is not None:
        xg1 = evaluate_xg1_measured(
            inputs.execution_ledger_rows,
            transform_registry=inputs.transform_registry,
            warmup_boundaries=inputs.warmup_boundaries,
        )
    else:
        xg1 = _evaluate_xg1(inputs.pit_evidence)
    xg2a = (
        _evaluate_g2a(inputs.artifact_integrity)
        if inputs.artifact_integrity is not None
        else GateResult(XGateId.XG2A_ARTIFACT_INTEGRITY, GateVerdict.NOT_APPLICABLE)
    )
    xg2a = GateResult(XGateId.XG2A_ARTIFACT_INTEGRITY, xg2a.verdict, xg2a.reasons)
    xg2b = (
        _evaluate_g2b(inputs.independent_reproduction)
        if inputs.independent_reproduction is not None
        else GateResult(XGateId.XG2B_INDEPENDENT_REPRODUCIBILITY, GateVerdict.NOT_YET_TESTED)
    )
    xg2b = GateResult(XGateId.XG2B_INDEPENDENT_REPRODUCIBILITY, xg2b.verdict, xg2b.reasons)
    return [
        _evaluate_xg0(inputs),
        xg1,
        xg2a,
        xg2b,
        _evaluate_xg3(inputs.stage_a),
        _evaluate_xg4(inputs.robustness),
        evaluate_xg5(inputs.risk)[0],
    ]
