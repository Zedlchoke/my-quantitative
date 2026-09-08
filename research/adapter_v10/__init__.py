"""Generic V10 strategy-to-research adapter + finalizer lane (sprint V10P-R, G1).

Public surface (family-neutral):

* :mod:`.protocol`  -- frozen generic interface + identity/stress/fill types;
* :mod:`.base`      -- reusable plugin plumbing (cost floors, folds, funding);
* :mod:`.converters`-- BG2 target book -> fill/portfolio/scoring payload;
* :mod:`.metrics`   -- BG1 realized after-cost/funding fold metrics;
* :mod:`.stress`    -- BG4 named stress-matrix driver with unique roots;
* :mod:`.benchmarks`-- BG5 flat hard gate + context-only benchmark outputs;
* :mod:`.publish`   -- BG6 idempotent exactly-once ledger publication;
* :mod:`.runner`    -- orchestration + deterministic artifacts;
* :mod:`.m01_plugin`/  -- the two plugins proving reuse
* :mod:`.dummy_strategy`;
* :mod:`.facade`    -- frozen QA-contract surface (``ADAPTER_INTERFACE_VERSION``,
  ``GenericRunnerV10``, ``checked_funding_accrual``, ``cache_decision``,
  ``resource_cap_report``, ``validate_resource_cap_report``).
"""

from __future__ import annotations

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.converters import (
    build_portfolio_payload,
    fill_payload_row,
    normalise_target_book,
    summarise_books,
)
from research.adapter_v10.hashes import (
    atomic_write_json,
    canonical_text,
    file_sha256,
    payload_sha256,
)
from research.adapter_v10.protocol import (
    SCHEMA_VERSION,
    AdapterError,
    ContractViolation,
    CostModel,
    FillRecord,
    FillStatusVocabulary,
    FoldSpec,
    ImmutableSchedule,
    PositionSpan,
    SettlementPoint,
    StrategyIdentity,
    StressSpec,
    TargetBook,
)
from research.adapter_v10.facade import (
    ADAPTER_INTERFACE_VERSION,
    FORCE_FLAT_REASON as FACADE_FORCE_FLAT_REASON,
    FORCE_FLAT_STATUS as FACADE_FORCE_FLAT_STATUS,
    GenericRunnerV10,
    cache_decision,
    checked_funding_accrual,
    denominator as facade_denominator,
    resource_cap_report,
    validate_resource_cap_report,
)
from research.adapter_v10.publish import (
    evaluate_pre_score_gate,
    publish_trial,
    trial_denominator,
    trial_key,
)
from research.adapter_v10.runner import run_full_stress_matrix, run_strategy
from research.adapter_v10.stress import (
    BASELINE_NAME,
    STRESS_SURFACE_VARIANTS,
    build_stress_spec,
    stress_matrix_cells,
)

__all__ = [
    "ADAPTER_INTERFACE_VERSION",
    "BASELINE_NAME",
    "AdapterError",
    "ContractViolation",
    "CostModel",
    "FillRecord",
    "FillStatusVocabulary",
    "FoldSpec",
    "GenericRunnerV10",
    "GenericStrategyBase",
    "ImmutableSchedule",
    "PositionSpan",
    "SCHEMA_VERSION",
    "STRESS_SURFACE_VARIANTS",
    "SettlementPoint",
    "StrategyIdentity",
    "StressSpec",
    "TargetBook",
    "atomic_write_json",
    "build_portfolio_payload",
    "build_stress_spec",
    "cache_decision",
    "checked_funding_accrual",
    "canonical_text",
    "evaluate_pre_score_gate",
    "file_sha256",
    "fill_payload_row",
    "normalise_target_book",
    "payload_sha256",
    "publish_trial",
    "resource_cap_report",
    "run_full_stress_matrix",
    "run_strategy",
    "stress_matrix_cells",
    "summarise_books",
    "trial_denominator",
    "trial_key",
    "validate_resource_cap_report",
]
