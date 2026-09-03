"""V12 data contract and fail-closed load validation (P1 A3).

Modules:
- :mod:`research.v12.data_contract` -- frozen windows, required symbol set,
  PIT inventory of local bars / funding / OI / instrument metadata, and the
  deterministic equal-twin staging-manifest generator.
- :mod:`research.v12.load_validation` -- fail-closed re-checks performed at
  load time (window bounds, completed-bar integrity, funding PIT
  applicability, manifest-hash match).
"""

from research.v12.data_contract import (  # noqa: F401
    BAR_INTERVAL_NS,
    FUNDING_INTERVAL_NS,
    REQUIRED_SYMBOLS,
    S0R_WINDOW_END_ISO,
    S0R_WINDOW_START_ISO,
    V11_SCORED_WINDOW_END_ISO,
    V11_SCORED_WINDOW_START_ISO,
    windows_overlap,
)
from research.v12.load_validation import (  # noqa: F401
    DataLoadError,
    validate_completed_bars,
    validate_funding_applicability,
    validate_manifest_hash,
    validate_window_bounds,
)

__all__ = [
    "BAR_INTERVAL_NS",
    "FUNDING_INTERVAL_NS",
    "REQUIRED_SYMBOLS",
    "S0R_WINDOW_END_ISO",
    "S0R_WINDOW_START_ISO",
    "V11_SCORED_WINDOW_END_ISO",
    "V11_SCORED_WINDOW_START_ISO",
    "DataLoadError",
    "validate_completed_bars",
    "validate_funding_applicability",
    "validate_manifest_hash",
    "validate_window_bounds",
    "windows_overlap",
]
