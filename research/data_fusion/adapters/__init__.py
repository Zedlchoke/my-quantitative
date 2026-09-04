"""Source adapters for the first wave of free candidates.

``base.py`` is the A1-owned shared foundation: lane engineers (A2 stocks,
A3 macro, A4 forex) implement their own adapter modules against it and may
not modify it.  Adapter module imports are re-exported here by A1 at
integration time.

Every adapter here is DISCOVERY_ONLY.  A passing adapter proves nothing
about authority; see ``research.data_fusion.authority`` and the owner-run
source registry.
"""

from .base import (
    AdapterError,
    AdapterNote,
    AdapterOutput,
    AvailabilityBasis,
    RawCacheStore,
    RawResponse,
    RateLimitPolicy,
    ReleaseEvidence,
    RequestSpec,
    SourceAdapter,
    Timings,
    date_only_evidence,
    timings_from_evidence,
)

__all__ = [
    "AdapterError",
    "AdapterNote",
    "AdapterOutput",
    "AvailabilityBasis",
    "RawCacheStore",
    "RawResponse",
    "RateLimitPolicy",
    "ReleaseEvidence",
    "RequestSpec",
    "SourceAdapter",
    "Timings",
    "date_only_evidence",
    "timings_from_evidence",
]
