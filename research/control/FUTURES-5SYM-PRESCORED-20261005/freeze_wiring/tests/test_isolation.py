"""test_isolation — the sandbox never writes real governance/registry/GO/
ledger/lock surfaces. Session-scoped snapshot (conftest) vs after the whole
suite; heavy_runtime CONTENTS are excluded (canonical lock lifecycle of other
cycles — disclosed exclusion, same as the exec suite T16).
"""
from __future__ import annotations

from conftest import (REAL_GOV, REAL_REGISTRY, real_surface_snapshot,
                      sha256_path)


def test_real_governance_dir_exists_and_is_untouched(real_surface_before):
    assert REAL_GOV.is_dir(), "real governance dir missing (env drift)"
    after = real_surface_snapshot()
    if after != real_surface_before:
        drift = {k: (real_surface_before.get(k), after.get(k))
                 for k in set(after) | set(real_surface_before)
                 if after.get(k) != real_surface_before.get(k)}
        first = sorted(drift)[:3]
        raise AssertionError(
            f"REAL SURFACE DRIFT: the suite wrote outside the sandbox: {first}"
            f" ({len(drift)} files drifted)")


def test_real_registry_is_read_only_here(real_surface_before):
    # the real plans/CYCLE_REGISTRY.json must be byte-identical after the
    # suite (this lane registers nothing; registration is owner-only)
    assert sha256_path(REAL_REGISTRY) == \
        real_surface_before["__real_registry__"]
