"""Asset-neutral contracts and interfaces (owner: A2, PLAN_stocks.md section 6).

Every new multi-asset manifest carries an explicit ``asset_class``, ``venue``,
``calendar_id`` and ``cost_model_id``.  There is deliberately NO default
asset class, NO default calendar (never a 24/7 fallback) and NO default cost
model anywhere in this package: every value is supplied by the caller and
validated, or construction fails.

Historical crypto behavior is adapted, never changed: see ``crypto_compat``.
"""

from __future__ import annotations

from research.assets.common.calendar import (
    TEST_ONLY_CALENDAR_PREFIX,
    TEST_ONLY_DummySolar24x7,
    Session,
    SessionCalendar,
    is_test_only_calendar_id,
    require_production_calendar_id,
)
from research.assets.common.carrying_cost import (
    CASHFLOW_KINDS,
    CarryingCostModel,
    CashflowLine,
    CryptoFundingCarry,
    EquityBorrowDividendCarry,
    FxRolloverCarry,
)
from research.assets.common.contracts import (
    CRYPTO_PERP,
    FX_SPOT,
    US_CASH_EQUITY,
    ASSET_CLASS_PATTERN,
    AssetExperimentContract,
    MetricReading,
    ScoredResultContract,
    canonical_json,
    canonical_payload,
    require_asset_class,
    require_digest_hex,
    require_token,
    sha256_text,
)
from research.assets.common.crypto_compat import (
    CRYPTO_PERP_ASSET_CLASS,
    CryptoCompatResult,
    derive_cost_model_id,
    legacy_payload,
    normalize_legacy_manifest,
    to_asset_contract,
    verify_roundtrip,
)
from research.assets.common.execution_cost import (
    CostModelId,
    ExecutionCostEstimate,
    ExecutionCostModel,
)
from research.assets.common.instrument import InstrumentSpec
from research.assets.common.ledger_policy import (
    GLOBAL_TRIAL_INDEX_FILENAME,
    LEDGER_ROOTS_BY_ASSET_CLASS,
    GlobalTrialIndex,
    global_trial_index_path,
    ledger_path_for,
    ledger_root_for,
)
from research.assets.common.trial_identity import (
    IDENTITY_SCHEMA_VERSION,
    ArmIdentity,
    TrialCounterBook,
    TrialCounters,
    assert_cross_asset_class_separation,
    canonical_identity_payload,
    check_counter_invariants,
    identity_digest,
    record_computation,
    record_idempotent_replay,
    record_publication_failure,
    record_publication_success,
)

__all__ = [
    # contracts
    "ASSET_CLASS_PATTERN",
    "AssetExperimentContract",
    "CRYPTO_PERP",
    "FX_SPOT",
    "US_CASH_EQUITY",
    "MetricReading",
    "ScoredResultContract",
    "canonical_json",
    "canonical_payload",
    "require_asset_class",
    "require_digest_hex",
    "require_token",
    "sha256_text",
    # calendar
    "TEST_ONLY_CALENDAR_PREFIX",
    "TEST_ONLY_DummySolar24x7",
    "Session",
    "SessionCalendar",
    "is_test_only_calendar_id",
    "require_production_calendar_id",
    # carrying cost
    "CASHFLOW_KINDS",
    "CarryingCostModel",
    "CashflowLine",
    "CryptoFundingCarry",
    "EquityBorrowDividendCarry",
    "FxRolloverCarry",
    # crypto compatibility
    "CRYPTO_PERP_ASSET_CLASS",
    "CryptoCompatResult",
    "derive_cost_model_id",
    "legacy_payload",
    "normalize_legacy_manifest",
    "to_asset_contract",
    "verify_roundtrip",
    # execution cost
    "CostModelId",
    "ExecutionCostEstimate",
    "ExecutionCostModel",
    # instrument
    "InstrumentSpec",
    # ledger placement
    "GLOBAL_TRIAL_INDEX_FILENAME",
    "LEDGER_ROOTS_BY_ASSET_CLASS",
    "GlobalTrialIndex",
    "global_trial_index_path",
    "ledger_path_for",
    "ledger_root_for",
    # trial identity + counters
    "IDENTITY_SCHEMA_VERSION",
    "ArmIdentity",
    "TrialCounterBook",
    "TrialCounters",
    "assert_cross_asset_class_separation",
    "canonical_identity_payload",
    "check_counter_invariants",
    "identity_digest",
    "record_computation",
    "record_idempotent_replay",
    "record_publication_failure",
    "record_publication_success",
]
