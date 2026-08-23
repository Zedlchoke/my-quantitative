"""A3 validation protocol package: manifests, registry, canonical metrics,
hard gates, scorecard, reproduction harness.

All schemas/enums/thresholds/reason codes come from ``contracts.protocol``
(owner A1); nothing is redefined here.
"""

from __future__ import annotations

from research.protocol.manifest import (
    DEFAULT_REGISTRY_DIR,
    build_manifest,
    manifest_seed_reason,
    next_experiment_id,
    read_manifest,
    write_manifest,
)
from research.protocol.metrics import extract_canonical_metrics
from research.protocol.registry import append, load_all, verify_append_only

__all__ = [
    "DEFAULT_REGISTRY_DIR",
    "append",
    "build_manifest",
    "extract_canonical_metrics",
    "load_all",
    "manifest_seed_reason",
    "next_experiment_id",
    "read_manifest",
    "verify_append_only",
    "write_manifest",
]
