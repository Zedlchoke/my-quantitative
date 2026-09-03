"""Incremental mechanism alpha and the falsification contract.

Owner: lane A3, STOCKS-FREE-V3 P1 (PLAN_stocks.md section 9 A3, deliverable
5: "Define incremental mechanism metrics separately from raw PnL. A family
cannot pass merely because long equity beta rose.").

Definition (frozen at P1)
-------------------------
For one scored fold ``f``:

    incremental_alpha(f) = R_strategy_after_cost(f) - R_benchmark(f)

where ``R_strategy_after_cost(f)`` is the family arm's own after-cost total
return over the fold window (produced by the family's frozen execution
accounting; this module only CONSUMES it and never scores real data) and
``R_benchmark(f)`` is the total return of the ``RISK_MATCHED_SPY_CONTEXT``
benchmark over the SAME fold window, built with the SAME arm-frozen
ex-ante gross/vol rule (:mod:`research.stocks_free_v3.benchmarks`).

Because the benchmark replicates the arm's chosen gross exposure to SPY ex
ante, the difference is isolated from long equity beta: an arm whose
returns are explained by beta alone yields incremental_alpha ≈ 0 regardless
of how large beta was.  A fold record is ``eligible_for_pass`` ONLY when it
compares against the risk-matched benchmark AND the alpha is strictly
positive.  Diagnostics against the other three benchmarks are representable
but are never pass-eligible (``beta_isolation = NONE``).

This module computes NO strategy return from real data.  Strategy returns
arrive as declared inputs with their own digest; the golden tests use
synthetic hand-computed fixtures.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

from research.assets.common.contracts import canonical_json, require_digest_hex, require_finite_float, require_token
from research.stocks_free_v3.benchmarks import (
    BENCHMARK_RISK_MATCHED_SPY,
    BenchmarkSeries,
)

CONTRACT_SCHEMA = "stocks_free_v3/incremental_alpha@1"

BETA_ISOLATION_RISK_MATCHED = "RISK_MATCHED_EX_ANTE"
BETA_ISOLATION_NONE = "NONE"

FALSIFICATION_NOTE = (
    "a family cannot pass merely because long equity beta rose: incremental "
    "alpha is measured against the RISK_MATCHED_SPY_CONTEXT benchmark built "
    "over the same fold window with the arm's frozen ex-ante gross/vol rule"
)


class IncrementalAlphaError(ValueError):
    """Raised when a fold-alpha record cannot be formed (fail closed)."""


@dataclass(frozen=True)
class FoldAlphaRecord:
    """One fold's incremental mechanism alpha with falsification fields."""

    family_id: str
    arm_id: str
    fold_id: str
    window_start: str
    window_end: str
    strategy_return_after_cost: float
    strategy_metric_digest: str
    benchmark_id: str
    benchmark_definition_digest: str
    benchmark_series_digest: str
    benchmark_return: float
    incremental_alpha: float
    beta_isolation: str
    ex_ante_rule_digest: str | None

    def __post_init__(self) -> None:
        require_token(self.family_id, "family_id")
        require_token(self.arm_id, "arm_id")
        require_token(self.fold_id, "fold_id")
        require_finite_float(self.strategy_return_after_cost, "strategy_return_after_cost")
        require_digest_hex(self.strategy_metric_digest, "strategy_metric_digest")
        require_token(self.benchmark_id, "benchmark_id")
        require_digest_hex(self.benchmark_definition_digest, "benchmark_definition_digest")
        require_digest_hex(self.benchmark_series_digest, "benchmark_series_digest")
        require_finite_float(self.benchmark_return, "benchmark_return")
        expected = self.strategy_return_after_cost - self.benchmark_return
        if abs(self.incremental_alpha - expected) > 1e-12:
            raise IncrementalAlphaError(
                f"incremental_alpha {self.incremental_alpha} != strategy - "
                f"benchmark ({expected})"
            )
        if self.beta_isolation not in (BETA_ISOLATION_RISK_MATCHED, BETA_ISOLATION_NONE):
            raise IncrementalAlphaError(f"unknown beta_isolation {self.beta_isolation!r}")
        if self.beta_isolation == BETA_ISOLATION_RISK_MATCHED:
            if self.benchmark_id != BENCHMARK_RISK_MATCHED_SPY:
                raise IncrementalAlphaError(
                    "RISK_MATCHED_EX_ANTE isolation requires the "
                    f"{BENCHMARK_RISK_MATCHED_SPY} benchmark, got {self.benchmark_id}"
                )
            if not self.ex_ante_rule_digest:
                raise IncrementalAlphaError(
                    "risk-matched isolation requires the frozen ex-ante rule digest"
                )
        if self.ex_ante_rule_digest is not None:
            require_digest_hex(self.ex_ante_rule_digest, "ex_ante_rule_digest")

    @property
    def eligible_for_pass(self) -> bool:
        """True only for strictly positive alpha against the risk-matched
        benchmark (beta isolated) — the falsification contract."""
        return (
            self.beta_isolation == BETA_ISOLATION_RISK_MATCHED
            and self.incremental_alpha > 0.0
        )

    def to_payload(self) -> dict:
        return {
            "schema": CONTRACT_SCHEMA,
            "family_id": self.family_id,
            "arm_id": self.arm_id,
            "fold_id": self.fold_id,
            "window": [self.window_start, self.window_end],
            "strategy_return_after_cost": self.strategy_return_after_cost,
            "strategy_metric_digest": self.strategy_metric_digest,
            "benchmark_id": self.benchmark_id,
            "benchmark_definition_digest": self.benchmark_definition_digest,
            "benchmark_series_digest": self.benchmark_series_digest,
            "benchmark_return": self.benchmark_return,
            "incremental_alpha": self.incremental_alpha,
            "beta_isolation": self.beta_isolation,
            "ex_ante_rule_digest": self.ex_ante_rule_digest,
            "eligible_for_pass": self.eligible_for_pass,
            "falsification_note": FALSIFICATION_NOTE,
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def compute_fold_alpha(
    *,
    family_id: str,
    arm_id: str,
    fold_id: str,
    strategy_return_after_cost: float,
    strategy_metric_digest: str,
    benchmark: BenchmarkSeries,
    require_beta_isolation: bool = True,
) -> FoldAlphaRecord:
    """Build one fold's incremental-alpha record against ``benchmark``.

    ``strategy_return_after_cost`` must already be after-cost and produced by
    the family's frozen accounting (this module never computes it).  With
    ``require_beta_isolation`` (default True) the benchmark MUST be the
    risk-matched SPY context; pass False only for diagnostic records, which
    are never pass-eligible.
    """
    beta_isolation = (
        BETA_ISOLATION_RISK_MATCHED
        if benchmark.benchmark_id == BENCHMARK_RISK_MATCHED_SPY
        else BETA_ISOLATION_NONE
    )
    if require_beta_isolation and beta_isolation != BETA_ISOLATION_RISK_MATCHED:
        raise IncrementalAlphaError(
            "fold alpha requires the risk-matched SPY benchmark; diagnostic "
            "records must pass require_beta_isolation=False explicitly"
        )
    benchmark_return = benchmark.total_return
    strategy = require_finite_float(strategy_return_after_cost, "strategy_return_after_cost")
    return FoldAlphaRecord(
        family_id=family_id,
        arm_id=arm_id,
        fold_id=fold_id,
        window_start=benchmark.window_start,
        window_end=benchmark.window_end,
        strategy_return_after_cost=strategy,
        strategy_metric_digest=strategy_metric_digest,
        benchmark_id=benchmark.benchmark_id,
        benchmark_definition_digest=benchmark.definition_digest,
        benchmark_series_digest=benchmark.series_digest(),
        benchmark_return=benchmark_return,
        incremental_alpha=strategy - benchmark_return,
        beta_isolation=beta_isolation,
        ex_ante_rule_digest=(benchmark.rule.digest if benchmark.rule is not None else None),
    )


@dataclass(frozen=True)
class FoldAlphaReport:
    """Fold-alpha records for one family arm, plus the frozen definitions."""

    family_id: str
    arm_id: str
    records: tuple[FoldAlphaRecord, ...]

    def __post_init__(self) -> None:
        require_token(self.family_id, "family_id")
        require_token(self.arm_id, "arm_id")
        if not self.records:
            raise IncrementalAlphaError("a fold-alpha report needs at least one record")
        seen = set()
        for record in self.records:
            if record.family_id != self.family_id or record.arm_id != self.arm_id:
                raise IncrementalAlphaError(
                    "report records must all belong to the same family/arm"
                )
            if record.fold_id in seen:
                raise IncrementalAlphaError(f"duplicate fold {record.fold_id}")
            seen.add(record.fold_id)

    @property
    def mean_incremental_alpha(self) -> float:
        return sum(r.incremental_alpha for r in self.records) / len(self.records)

    @property
    def pass_eligible_folds(self) -> tuple[str, ...]:
        return tuple(r.fold_id for r in self.records if r.eligible_for_pass)

    def to_payload(self) -> dict:
        return {
            "schema": CONTRACT_SCHEMA,
            "family_id": self.family_id,
            "arm_id": self.arm_id,
            "folds": [r.to_payload() for r in self.records],
            "mean_incremental_alpha": self.mean_incremental_alpha,
            "pass_eligible_folds": list(self.pass_eligible_folds),
            "falsification_note": FALSIFICATION_NOTE,
        }

    def canonical_json(self) -> str:
        return canonical_json(self.to_payload())

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


__all__ = [
    "BETA_ISOLATION_NONE",
    "BETA_ISOLATION_RISK_MATCHED",
    "CONTRACT_SCHEMA",
    "FALSIFICATION_NOTE",
    "FoldAlphaRecord",
    "FoldAlphaReport",
    "IncrementalAlphaError",
    "compute_fold_alpha",
]
