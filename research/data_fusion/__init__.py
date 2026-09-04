"""Point-in-time, provenance-first data fusion primitives.

The package is deliberately independent from strategy and scoring code.  A
source being registered here does not authorize it for research.
"""

from .authority import AuthorityDecision, AuthorityEvidence, AuthorityStatus, evaluate_authority
from .conflicts import ConflictError, SourcePolicy, SourceRole, resolve_primary
from .identity import IdentityConflict, TemporalAlias, resolve_identity
from .manifest import RawFileEvidence, SourceManifest
from .models import NormalizedRecord
from .pit import AmbiguousVintageError, VintageSeries, asof_join, select_asof

__all__ = [
    "AmbiguousVintageError",
    "AuthorityDecision",
    "AuthorityEvidence",
    "AuthorityStatus",
    "ConflictError",
    "IdentityConflict",
    "NormalizedRecord",
    "RawFileEvidence",
    "SourceManifest",
    "SourcePolicy",
    "SourceRole",
    "TemporalAlias",
    "VintageSeries",
    "asof_join",
    "evaluate_authority",
    "resolve_identity",
    "resolve_primary",
    "select_asof",
]
