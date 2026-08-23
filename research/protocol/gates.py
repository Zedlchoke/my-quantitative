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
    if section.fee_stress_positive is False:
        reasons.append("fee_stress_negative")
    elif section.fee_stress_positive is None:
        pending.append("fee_stress_negative")

    if section.delay_stress_positive is False:
        reasons.append("delay_stress_negative")
    elif section.delay_stress_supported and section.delay_stress_positive is None:
        pending.append("delay_stress_negative")

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
