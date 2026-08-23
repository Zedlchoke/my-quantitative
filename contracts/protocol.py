"""Frozen sprint-24h interface contracts.

Owner: A1 (contract owner). A2/A3/A4 import from here; they must not redefine
schemas, reason codes, scorecard weights or budgets. Spec source: PLAN.md v3.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class CellStatus(str, Enum):
    COMPLETED = "COMPLETED"
    REUSED = "REUSED"
    CANDIDATE_FAIL = "CANDIDATE_FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    DATA_INCOMPLETE = "DATA_INCOMPLETE"
    PIPELINE_ERROR = "PIPELINE_ERROR"
    NOT_RUN_BUDGET = "NOT_RUN_BUDGET"


class GateId(str, Enum):
    G0_DATA = "G0_DATA"
    G1_LEAKAGE = "G1_LEAKAGE"
    G2_REPRODUCIBILITY = "G2_REPRODUCIBILITY"
    G3_STAGE_A = "G3_STAGE_A"
    G4_SURVIVOR_ROBUSTNESS = "G4_SURVIVOR_ROBUSTNESS"
    G5_PORTFOLIO = "G5_PORTFOLIO"


class GateVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NA"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    NOT_YET_TESTED = "NOT_YET_TESTED"


class SprintVerdict(str, Enum):
    PIPELINE_PASS_CANDIDATE_FAIL = "PIPELINE_PASS_CANDIDATE_FAIL"
    PIPELINE_PASS_CANDIDATE_INCONCLUSIVE = "PIPELINE_PASS_CANDIDATE_INCONCLUSIVE"
    PIPELINE_PASS_LOCK_FOR_FUTURE_OOS = "PIPELINE_PASS_LOCK_FOR_FUTURE_OOS"
    PIPELINE_FAIL = "PIPELINE_FAIL"


FORBIDDEN_VERDICTS = ("EDGE_CONFIRMED", "PRODUCTION_READY", "LIVE_READY")


class HypothesisState(str, Enum):
    IDEA = "IDEA"
    SPEC_DRAFT = "SPEC_DRAFT"
    SPEC_LOCKED = "SPEC_LOCKED"
    IMPLEMENTED = "IMPLEMENTED"
    TIER0_COMPATIBLE = "TIER0_COMPATIBLE"
    STAGE_A_SCREENED = "STAGE_A_SCREENED"
    SURVIVOR_VALIDATED = "SURVIVOR_VALIDATED"
    PORTFOLIO_TESTED = "PORTFOLIO_TESTED"
    LOCKED_FOR_FUTURE_OOS = "LOCKED_FOR_FUTURE_OOS"
    REJECTED = "REJECTED"


REASON_CODES: dict[str, str] = {
    # G0 data
    "duplicate_bars": "duplicate timestamps/bars in window",
    "unexplained_gap": "gap larger than bar interval without explanation",
    "funding_coverage_insufficient": "funding bundle missing or partial for closed positions",
    "missing_instrument_metadata": "instrument definition absent or unusable",
    "coverage_below_declared": "actual common intersection narrower than declared",
    "catalog_not_current": "expected newer closed bars exist but catalog stale",
    # G1 leakage/protocol
    "scored_fold_in_selection": "scored fold participated in parameter selection",
    "warmup_inside_window": "warmup overlaps scored window",
    "universe_not_frozen": "universe/config changed after results were seen",
    "split_policy_missing": "no declared split policy",
    "posthoc_regime_gate": "regime gate added after seeing fold results",
    # G2 reproducibility
    "manifest_missing_field": "required manifest field missing",
    "hash_mismatch": "config/data hash differs between manifest and rerun",
    "rerun_pnl_mismatch": "independent rerun canonical PnL mismatch beyond tolerance",
    "rerun_positions_mismatch": "rerun positions/fills differ from original",
    "seed_unavailable": "engine path is deterministic-input, seed recorded null with reason",
    # metrics
    "metric_missing_drawdown": "drawdown metric unavailable in engine stats",
    "metric_zero_default_suspect": "legacy extractor defaulted to 0.0 instead of null",
    "metric_not_computed": "metric could not be computed; null + this reason returned",
    # G3 stage A
    "exp_nonpositive": "after-cost expectancy <= 0",
    "pf_below_min": "aggregate position PF < 1.10",
    "positive_folds_ratio_low": "fewer than 2/3 folds positive after cost",
    "trades_below_min": "< 20 closed trades per symbol without pre-declared exception",
    "fold_pf_below_floor": "fold with >=5 trades and PF < 0.80",
    "fold_concentration_high": "one fold contributed > 50% of total PnL",
    "symbol_masked_by_average": "multi-symbol average hides a required negative symbol",
    # G4 survivor robustness
    "fee_stress_negative": "expectancy flips non-positive at +50% fee stress",
    "delay_stress_negative": "one-bar delayed entry flips sign",
    "slippage_stress_not_implemented": "two-tick fill model unsupported by engine",
    "neighborhood_spike": "parameter neighborhood shows isolated spike",
    "dropone_signflip": "drop-one-fold/symbol changes expectancy sign abnormally",
    # G5 portfolio
    "portfolio_pnl_nonpositive": "shared-capital canonical PnL <= 0",
    "portfolio_pf_below_min": "shared-capital PF < 1.10",
    "limit_violation": "gross/concurrency/cluster/daily-loss limit breached",
    "symbol_contribution_high": "one symbol > 40% portfolio PnL/risk contribution",
    # pipeline/cells
    "cell_failed_exception": "worker raised; cell isolated, matrix continued",
    "budget_exhausted": "trial budget consumed before cell ran",
}


def require_reason(code: str) -> str:
    if code not in REASON_CODES:
        raise ValueError(f"unknown reason code: {code}")
    return code


# Trial/resource budget (PLAN.md §7)
MAX_HYPOTHESES = 3
MAX_NEW_STRATEGIES = 2
MAX_PARAM_COMBOS_PER_HYPOTHESIS = 16
MAX_LOOP_ITERATIONS = 2

# Stage A thresholds (PLAN.md §10 G3)
STAGE_A_MIN_PF = 1.10
STAGE_A_MIN_POSITIVE_FOLD_RATIO = 2.0 / 3.0
STAGE_A_MIN_TRADES_PER_SYMBOL = 20
FOLD_PF_FLOOR = 0.80
FOLD_PF_FLOOR_MIN_TRADES = 5
MAX_SINGLE_FOLD_CONTRIBUTION = 0.50
# Portfolio (G5)
PORTFOLIO_MIN_PF = 1.10
MAX_SYMBOL_CONTRIBUTION = 0.40


SCORECARD_COMPONENTS: dict[str, int] = {
    "economic_rationale_simplicity": 10,
    "data_leakage_integrity": 15,
    "chronological_edge_quality": 25,
    "time_symbol_param_robustness": 15,
    "cost_execution_realism": 10,
    "risk_quality": 10,
    "portfolio_diversification": 5,
    "reproducibility_auditability": 10,
}
SCORECARD_TOTAL = sum(SCORECARD_COMPONENTS.values())
assert SCORECARD_TOTAL == 100


def scorecard_max_verdict(score: int) -> str:
    if score < 50:
        return "REJECT_REDESIGN"
    if score < 60:
        return "DIAGNOSTIC_ONLY"
    if score < 70:
        return "EXPLORATORY_STAGE_A_CANDIDATE"
    if score < 80:
        return "LOCK_FOR_FUTURE_OOS_IF_G0_G5_PASS"
    return "STRONG_RESEARCH_CANDIDATE_NOT_CONFIRMED_EDGE"


@dataclass(frozen=True)
class ManifestSpec:
    experiment_id: str
    hypothesis_id: str
    candidate_version: int
    strategy_type: str
    owner_agent: str
    validator_agent: str
    git_commit: str
    dirty_worktree: bool
    config_path: str
    config_sha256: str
    data_snapshot_id: str
    data_manifest_sha256: str
    universe_snapshot: str
    actual_start_utc: str
    actual_end_utc: str
    common_intersection: str
    split_policy: str
    warmup_bars: int
    purge_bars: int
    embargo_bars: int
    outer_folds: int
    parameter_combinations: int
    prior_family_trials: int
    fee_model: str
    slippage_model: str
    funding_mode: str
    random_seed: Optional[int]
    parameter_lock_utc: str
    command: str

    REQUIRED_FIELDS = frozenset(
        (
            "experiment_id", "hypothesis_id", "candidate_version", "strategy_type",
            "owner_agent", "validator_agent", "git_commit", "dirty_worktree",
            "config_path", "config_sha256", "data_snapshot_id",
            "data_manifest_sha256", "universe_snapshot", "actual_start_utc",
            "actual_end_utc", "common_intersection", "split_policy", "warmup_bars",
            "purge_bars", "embargo_bars", "outer_folds", "parameter_combinations",
            "prior_family_trials", "fee_model", "slippage_model", "funding_mode",
            "random_seed", "parameter_lock_utc", "command",
        )
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    NULLABLE_FIELDS = frozenset(("random_seed",))

    def validate(self) -> list[str]:
        missing = [
            name
            for name in self.REQUIRED_FIELDS
            if getattr(self, name) is None and name not in self.NULLABLE_FIELDS
        ]
        return [require_reason("manifest_missing_field") for _ in missing]


@dataclass(frozen=True)
class HypothesisSpec:
    hypothesis_id: str
    family: str
    state: HypothesisState
    candidate_version: int
    economic_mechanism: str
    expected_counterparty: str
    expected_regimes: tuple[str, ...]
    invalidating_evidence: tuple[str, ...]
    entry_exit_rules: str
    holding_horizon: str
    warmup_bars: int
    universe: tuple[str, ...]
    cost_assumptions: str
    trial_budget_combinations: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MetricValue:
    value: Optional[float]
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.value is None and self.reason is None:
            raise ValueError("null metric requires a reason code")
        if self.reason is not None:
            require_reason(self.reason)

    @classmethod
    def known(cls, value: float) -> "MetricValue":
        return cls(value=value, reason=None)

    @classmethod
    def missing(cls, reason: str) -> "MetricValue":
        return cls(value=None, reason=require_reason(reason))


@dataclass(frozen=True)
class CanonicalMetrics:
    trades: MetricValue
    net_canonical_pnl: MetricValue
    expectancy_usdt: MetricValue
    position_pf: MetricValue
    win_rate: MetricValue
    gross_pnl: MetricValue
    commission_cost: MetricValue
    slippage_cost: MetricValue
    funding_cost: MetricValue
    max_drawdown: MetricValue
    max_dd_duration_bars: MetricValue
    sharpe: MetricValue
    sortino: MetricValue
    exposure_pct: MetricValue
    turnover: MetricValue
    top_fold_contribution_pct: MetricValue

    def to_dict(self) -> dict[str, Any]:
        return {
            name: {"value": getattr(self, name).value, "reason": getattr(self, name).reason}
            for name in self.__dataclass_fields__
        }


@dataclass(frozen=True)
class MatrixCellResult:
    experiment_id: str
    strategy_type: str
    symbol: str
    status: CellStatus
    artifact_path: Optional[str]
    reason_codes: tuple[str, ...] = ()
    config_sha256: Optional[str] = None
    data_snapshot_id: Optional[str] = None
    split_policy: Optional[str] = None
    folds_completed: int = 0

    def __post_init__(self) -> None:
        for code in self.reason_codes:
            require_reason(code)
        if self.status == CellStatus.COMPLETED and self.artifact_path is None:
            raise ValueError("COMPLETED cell requires artifact_path")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass(frozen=True)
class GateResult:
    gate: GateId
    verdict: GateVerdict
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for code in self.reasons:
            require_reason(code)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate.value,
            "verdict": self.verdict.value,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class ScorecardResult:
    components: dict[str, int]
    total: int
    reasons: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        expected = set(SCORECARD_COMPONENTS)
        got = set(self.components)
        if got != expected:
            raise ValueError(f"scorecard components must be exactly {sorted(expected)}")
        for name, points in self.components.items():
            if not 0 <= points <= SCORECARD_COMPONENTS[name]:
                raise ValueError(f"{name}: {points} outside 0..{SCORECARD_COMPONENTS[name]}")
        if self.total != sum(self.components.values()):
            raise ValueError("total must equal component sum")

    def max_verdict(self) -> str:
        return scorecard_max_verdict(self.total)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
