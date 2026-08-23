"""Hard-gate evaluation (G0..G5) using only contract thresholds/reason codes.

``evaluate_gates`` consumes a :class:`GateInputs` (or an equivalent plain
dict) and returns one :class:`contracts.protocol.GateResult` per gate in
fixed order.  Sections left as ``None`` mean "no evidence supplied":

* G4 -> ``NOT_IMPLEMENTED`` (stress harness absent this sprint)
* G5 -> ``NA``
* G0/G1/G2/G3 -> ``NA``

Sprint V2 fail-closed rules (PLAN section 9):

* G0 requires a REAL coverage payload (dict from the data-contract artifact).
  A missing/malformed payload is ``INCONCLUSIVE`` +
  ``g0_coverage_not_evidenced`` -- never an automatic PASS.
* G1 requires an explicit ``evidence`` dict; any missing key is
  ``INCONCLUSIVE`` + ``g1_evidence_missing``.
* G2 hash mismatches are ALWAYS ``FAIL`` (no benign interpretation), even if
  the canonical PnL happens to match; use :func:`evaluate_reproduction` with
  a :class:`ReproductionComparison` struct for hash/digest/PnL comparison.
* G3 with fewer than the minimum trades per symbol is ``INCONCLUSIVE``
  (``trades_below_min``) per PLAN section 9 G3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    GateId,
    GateResult,
    GateVerdict,
    require_reason,
)

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

#: Sprint V2 G1 evidence keys (all must be present and non-null).
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
    """G1 inputs: violation flags + mandatory evidence dict.

    ``evidence`` must carry every key of ``G1_REQUIRED_EVIDENCE_KEYS`` with a
    non-null value (booleans or proof dicts).  Missing/null keys yield
    INCONCLUSIVE + ``g1_evidence_missing`` (the fact is not evidenced).  A
    key present but explicitly ``False`` means the claim is contradicted and
    maps to the corresponding leakage FAIL reason where one exists.
    Violations may additionally be recorded through the boolean vectors.
    """

    scored_fold_in_selection: bool = False
    warmup_inside_window: bool = False
    universe_not_frozen: bool = False
    posthoc_regime_gate: bool = False
    split_policy_declared: bool = True
    evidence: Mapping[str, Any] | None = None


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
    leakage: LeakageGateInput | None = None
    reproducibility: ReproGateInput | None = None
    reproduction: ReproductionComparison | None = None
    stage_a: StageAInput | None = None
    survivor: SurvivorInput | None = None
    portfolio: PortfolioInput | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "GateInputs":
        mapping = {
            "data": DataGateInput,
            "leakage": LeakageGateInput,
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
            kwargs[key] = sub_cls(**value) if isinstance(value, dict) else value
        return cls(**kwargs)


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


def _evaluate_g1(section: LeakageGateInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G1_LEAKAGE, GateVerdict.NOT_APPLICABLE)

    evidence = section.evidence
    # Fail-closed: protocol claims without an explicit evidence dict are
    # INCONCLUSIVE (never auto-PASS from defaults).
    if not isinstance(evidence, Mapping) or G1_REQUIRED_EVIDENCE_KEYS.difference(evidence) or any(
        evidence.get(key) is None for key in G1_REQUIRED_EVIDENCE_KEYS
    ):
        return GateResult(GateId.G1_LEAKAGE, GateVerdict.INCONCLUSIVE, ("g1_evidence_missing",))

    reasons = [code for attr, code in (
        ("scored_fold_in_selection", "scored_fold_in_selection"),
        ("warmup_inside_window", "warmup_inside_window"),
        ("universe_not_frozen", "universe_not_frozen"),
        ("posthoc_regime_gate", "posthoc_regime_gate"),
    ) if getattr(section, attr)]

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
    return GateResult(GateId.G1_LEAKAGE, verdict, tuple(dict.fromkeys(reasons)))


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


def _evaluate_g2(section: ReproGateInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.NOT_APPLICABLE)
    reasons: list[str] = []
    if not section.manifest_complete:
        reasons.append("manifest_missing_field")
    if section.rerun.config_hash_matches is False:
        reasons.append("hash_mismatch")
    if reasons:
        return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.FAIL, tuple(reasons))
    rerun = section.rerun
    if not rerun.performed:
        return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.NOT_YET_TESTED)
    if rerun.matches:
        return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.PASS)
    failure_reasons = tuple(rerun.reasons) or ("rerun_pnl_mismatch",)
    return GateResult(GateId.G2_REPRODUCIBILITY, GateVerdict.FAIL, failure_reasons)


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
    """Evaluate every hard gate in fixed order G0..G5.

    When ``inputs.reproduction`` is supplied (Sprint V2 comparison struct) it
    takes precedence over the legacy ``reproducibility`` section for G2.
    """
    if isinstance(inputs, dict):
        inputs = GateInputs.from_dict(inputs)
    g2 = (
        evaluate_reproduction(inputs.reproduction)
        if inputs.reproduction is not None
        else _evaluate_g2(inputs.reproducibility)
    )
    return [
        _evaluate_g0(inputs.data),
        _evaluate_g1(inputs.leakage),
        g2,
        _evaluate_g3(inputs.stage_a),
        _evaluate_g4(inputs.survivor),
        _evaluate_g5(inputs.portfolio),
    ]
