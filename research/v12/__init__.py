"""V12 factory helpers (P1 lanes A2/A3/A4, integrated by A1).

Modules (union resolution of the three lanes' package docfiles; pure
packaging, no logic added at integration):

* :mod:`research.v12.accounting`     -- zero-position publication guard,
  observed-once refusal accounting, replay idempotence and the
  family-contract cell guard over the portable V12 ledger package
  (``research/control/v12_run/ledger_package/schema.json``). [A2]
* :mod:`research.v12.ledger_transfer` -- portable ledger transfer: verify a
  ``transfer_manifest.json`` (recomputed sha256 per file, fail closed) and
  regenerate one from a ledger path for host migration. [A2]
* :mod:`research.v12.data_contract`  -- frozen windows, required symbol set,
  PIT inventory of local bars / funding / OI / instrument metadata, and the
  deterministic equal-twin staging-manifest generator. [A3]
* :mod:`research.v12.load_validation` -- fail-closed re-checks performed at
  load time (window bounds, completed-bar integrity, funding PIT
  applicability, manifest-hash match). [A3]
* :mod:`research.v12.feasibility`    -- the pre-score target-book validator
  (fail-closed, per-stamp reason codes) and schedule-only diagnostics. [A4]
* :mod:`research.v12.oilev_v2_book`  -- the fixed OILEV-V2 diversified book
  (>=9 eligible, 4 lowest / 4 highest, equal weight per leg, frozen BTC
  beta-hedge context semantics, uniform whole-book scale to the frozen 0.30
  adapter cap; the cap holds by construction). [A4]
* :mod:`research.v12.oilev_v2_spec`  -- the OILEV-V2 schedule/spec draft
  (PLAN_crypto.md section 8.2 identity; the ranking feature itself is
  injected and remains frozen by the A1 brief, not here). [A4]

No lane in this package computes PnL.
"""

from research.v12.data_contract import (  # noqa: F401  [A3]
    BAR_INTERVAL_NS,
    FUNDING_INTERVAL_NS,
    REQUIRED_SYMBOLS,
    S0R_WINDOW_END_ISO,
    S0R_WINDOW_START_ISO,
    V11_SCORED_WINDOW_END_ISO,
    V11_SCORED_WINDOW_START_ISO,
    windows_overlap,
)
from research.v12.load_validation import (  # noqa: F401  [A3]
    DataLoadError,
    validate_completed_bars,
    validate_funding_applicability,
    validate_manifest_hash,
    validate_window_bounds,
)
from research.v12.feasibility import (  # noqa: F401  [A4]
    REASON_DUPLICATE_SYMBOL,
    REASON_EMPTY_BOOK,
    REASON_LEG_COUNT_MISMATCH,
    REASON_OK,
    REASON_WEIGHT_ABOVE_CAP,
    REASON_WEIGHT_NOT_FINITE,
    schedule_diagnostics,
    validate_stamp_schedule,
    validate_target_book,
)
from research.v12.oilev_v2_book import (  # noqa: F401  [A4]
    BENCHMARK_SYMBOL,
    BETA_HEDGE_SEMANTICS,
    CAP_MAX,
    LEG_NAMES,
    MIN_ELIGIBLE,
    EligibilityShortfall,
    build_oilev_v2_book,
)
from research.v12.oilev_v2_spec import (  # noqa: F401  [A4]
    OILEV_V2_ARMS,
    oilev_v2_spec_payload,
    stamp_calendar,
)

__all__ = [
    "BAR_INTERVAL_NS",
    "BENCHMARK_SYMBOL",
    "BETA_HEDGE_SEMANTICS",
    "CAP_MAX",
    "EligibilityShortfall",
    "FUNDING_INTERVAL_NS",
    "LEG_NAMES",
    "MIN_ELIGIBLE",
    "OILEV_V2_ARMS",
    "REASON_DUPLICATE_SYMBOL",
    "REASON_EMPTY_BOOK",
    "REASON_LEG_COUNT_MISMATCH",
    "REASON_OK",
    "REASON_WEIGHT_ABOVE_CAP",
    "REASON_WEIGHT_NOT_FINITE",
    "REQUIRED_SYMBOLS",
    "S0R_WINDOW_END_ISO",
    "S0R_WINDOW_START_ISO",
    "V11_SCORED_WINDOW_END_ISO",
    "V11_SCORED_WINDOW_START_ISO",
    "DataLoadError",
    "build_oilev_v2_book",
    "oilev_v2_spec_payload",
    "schedule_diagnostics",
    "stamp_calendar",
    "validate_completed_bars",
    "validate_funding_applicability",
    "validate_manifest_hash",
    "validate_stamp_schedule",
    "validate_target_book",
    "validate_window_bounds",
    "windows_overlap",
]
