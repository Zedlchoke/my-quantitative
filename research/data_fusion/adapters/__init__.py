"""Source adapters for the first wave of free candidates.

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
