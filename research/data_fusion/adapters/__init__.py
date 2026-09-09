"""Source adapters for the first wave of free candidates.

``base.py`` is the A1-owned shared foundation; lane implementations were
authored by A2 (sec, finra), A3 (ecb, bis, fred) and A4 (truefx) in their
own worktrees and integrated here by A1.  Nothing in this package raises a
source's authority: every adapter is DISCOVERY_ONLY and authority stays
with ``research.data_fusion.authority`` and the owner-run registry.
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
from .bis import BisAdapter
from .ecb import EcbAdapter
from .finra import FinraAdapter
from .fred import FredAdapter
from .sec import SecAdapter
from .truefx import TruefxAdapter

__all__ = [
    "AdapterError",
    "AdapterNote",
    "AdapterOutput",
    "AvailabilityBasis",
    "BisAdapter",
    "EcbAdapter",
    "FinraAdapter",
    "FredAdapter",
    "RawCacheStore",
    "RawResponse",
    "RateLimitPolicy",
    "ReleaseEvidence",
    "RequestSpec",
    "SecAdapter",
    "SourceAdapter",
    "Timings",
    "TruefxAdapter",
    "date_only_evidence",
    "timings_from_evidence",
]
