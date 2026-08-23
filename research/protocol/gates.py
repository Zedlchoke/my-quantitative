"""Hard-gate evaluation (G0..G5) using only contract thresholds/reason codes.

``evaluate_gates`` consumes a :class:`GateInputs` (or an equivalent plain
dict) and returns one :class:`contracts.protocol.GateResult` per gate in
fixed order.  Sections left as ``None`` mean "no evidence supplied":

* G4 -> ``NOT_IMPLEMENTED`` (stress harness absent this sprint)
* G5 -> ``NA``
* G0/G1/G2/G3 -> ``NA``

G3 mapping note: PLAN §10 says "<20 trades/symbol => INCONCLUSIVE"; the gate
verdict enum has no INCONCLUSIVE, so that case maps to ``NOT_YET_TESTED``
while any hard-fail reason still yields ``FAIL``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

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
)


@dataclass(frozen=True)
class DataGateInput:
    duplicates_present: bool = False
    unexplained_gaps: bool = False
    funding_coverage_complete: bool = True
    instrument_metadata_ok: bool = True
    catalog_current: bool = True
    coverage_ratio: float | None = None


@dataclass(frozen=True)
class LeakageGateInput:
    scored_fold_in_selection: bool = False
    warmup_inside_window: bool = False
    universe_not_frozen: bool = False
    posthoc_regime_gate: bool = False
    split_policy_declared: bool = True


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
    stage_a: StageAInput | None = None
    survivor: SurvivorInput | None = None
    portfolio: PortfolioInput | None = None

    @classmethod
    def from_dict(cls, payload: dict) -> "GateInputs":
        mapping = {
            "data": DataGateInput,
            "leakage": LeakageGateInput,
            "reproducibility": ReproGateInput,
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


def _evaluate_g0(section: DataGateInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G0_DATA, GateVerdict.NOT_APPLICABLE)
    reasons: list[str] = []
    if section.duplicates_present:
        reasons.append("duplicate_bars")
    if section.unexplained_gaps:
        reasons.append("unexplained_gap")
    if section.coverage_ratio is not None and section.coverage_ratio < 1.0:
        reasons.append("coverage_below_declared")
    if not section.funding_coverage_complete:
        reasons.append("funding_coverage_insufficient")
    if not section.instrument_metadata_ok:
        reasons.append("missing_instrument_metadata")
    if not section.catalog_current:
        reasons.append("catalog_not_current")
    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return GateResult(GateId.G0_DATA, verdict, tuple(reasons))


def _evaluate_g1(section: LeakageGateInput | None) -> GateResult:
    if section is None:
        return GateResult(GateId.G1_LEAKAGE, GateVerdict.NOT_APPLICABLE)
    flag_reasons = (
        ("scored_fold_in_selection", "scored_fold_in_selection"),
        ("warmup_inside_window", "warmup_inside_window"),
        ("universe_not_frozen", "universe_not_frozen"),
        ("posthoc_regime_gate", "posthoc_regime_gate"),
    )
    reasons = [code for attr, code in flag_reasons if getattr(section, attr)]
    if not section.split_policy_declared:
        reasons.append("split_policy_missing")
    verdict = GateVerdict.FAIL if reasons else GateVerdict.PASS
    return GateResult(GateId.G1_LEAKAGE, verdict, tuple(reasons))


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
    positive = [f for f in folds if f.pnl_after_cost > 0]
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
        total = sum(f.pnl_after_cost for f in folds)
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
        return GateResult(
            GateId.G3_STAGE_A, GateVerdict.NOT_YET_TESTED, ("trades_below_min",)
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
    """Evaluate every hard gate in fixed order G0..G5."""
    if isinstance(inputs, dict):
        inputs = GateInputs.from_dict(inputs)
    return [
        _evaluate_g0(inputs.data),
        _evaluate_g1(inputs.leakage),
        _evaluate_g2(inputs.reproducibility),
        _evaluate_g3(inputs.stage_a),
        _evaluate_g4(inputs.survivor),
        _evaluate_g5(inputs.portfolio),
    ]
