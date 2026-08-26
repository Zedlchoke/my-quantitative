"""V8R launch wiring tests: weekly_reversal provenance generation maps to v8p.

A1 integration wiring (PLAN §6): real V8 launches run with
``PORTFOLIO_SIGNAL_FAMILY=weekly_reversal`` and ``V6P_ENFORCE_PROVENANCE=1``.
The generation map must resolve to the v8p audit root (fail-closed otherwise)
and the v8p baseline/attestation pair must be declared launch-exempt so the
hash-chained freeze files can be uncommitted at launch like every prior
generation.
"""

from pathlib import Path

from research.portfolio_runner import PROVENANCE_GENERATIONS, _provenance_paths_for
from research.provenance_v6p import (
    ATTESTATION_FILENAME,
    BASELINE_FILENAME,
    _provenance_exempt,
)


def test_weekly_reversal_maps_to_v8p_generation():
    selected = _provenance_paths_for("weekly_reversal")
    assert selected is not None, "weekly_reversal must map to a committed generation"
    base_dir, generation = selected
    assert base_dir == Path("research/audits/v8p")
    assert generation == "weekly_reversal"


def test_unknown_family_stays_undetermined():
    assert _provenance_paths_for("nonexistent_family") is None


def test_v8p_baseline_and_attestation_are_launch_exempt():
    exempt = _provenance_exempt(Path("."))
    assert str(Path("research/audits/v8p") / BASELINE_FILENAME) in exempt
    assert str(Path("research/audits/v8p") / ATTESTATION_FILENAME) in exempt
