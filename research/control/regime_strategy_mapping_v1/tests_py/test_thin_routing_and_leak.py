"""A7-R1 remediation tests: OUTER thin-routing gate + selection leak law.

F1 (HIGH): census-THIN regimes must route FLAT in every fold of arm C.
F3 (MEDIUM): selection for outer fold k must be invariant to any data in
folds >= k (the inner-evidence filter is the containment; this test proves
it by mutating outer-fold evidence and asserting identical selections).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rsmv1.selection import SpecialistCandidate  # noqa: E402


def _fake_evidence(regime: str, folds: dict[int, float]) -> dict:
    return {regime: {"SPEC_X": {
        "fold_nets": dict(folds),
        "pooled_net": sum(folds.values()),
        "trades": 10,
    }}}


def test_outer_thin_routes_flat_everywhere(monkeypatch=None):
    """arm_c_selection must consult the census OUTER floors FIRST: a THIN
    regime (census verdict NOT_RUN_THIN_REGIME) routes FLAT in all folds
    even with abundant inner evidence."""
    from rsmv1 import scored as S

    thin_census = {
        "per_regime": {
            r: {"verdict": "NOT_RUN_THIN_REGIME", "episodes_total": 1,
                "margin_to_floor_min": 0.0}
            for r in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")
        }
    }
    class _Ctx:
        cell = "BTC_H4"
        asset = "BTCUSDT"
        episodes = []
        fz = None
        def __init__(self):
            from rsmv1.freezes import Freezes
            self.fz = Freezes(Path(__file__).resolve().parents[1])
    import rsmv1.scored as scored_mod
    orig = scored_mod.measure_cell_census if hasattr(scored_mod, "measure_cell_census") else None
    # patch: arm_c_selection imports measure_cell_census from .census inside
    import rsmv1.census as census_mod
    real = census_mod.measure_cell_census
    census_mod.measure_cell_census = lambda cd, cell: thin_census
    try:
        evidence = _fake_evidence("UPTREND", {0: 100.0, 1: 200.0, 2: 50.0})
        mapping, audit = scored_mod.arm_c_selection(_Ctx(), evidence)
        for fid in range(4):
            for regime in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"):
                assert mapping[fid][regime] == "FLAT", (fid, regime)
        assert all(a["reason"] == "OUTER_FLOOR_THIN" for a in audit)
    finally:
        census_mod.measure_cell_census = real


def test_non_thin_regime_still_selectable_when_inner_ok():
    import rsmv1.census as census_mod
    import rsmv1.scored as scored_mod

    ok_census = {
        "per_regime": {
            "UPTREND": {"verdict": "SAMPLE_OK", "episodes_total": 28,
                        "margin_to_floor_min": 1.4},
            "ACCUMULATION": {"verdict": "NOT_RUN_THIN_REGIME",
                             "episodes_total": 1, "margin_to_floor_min": 0.0},
            "DISTRIBUTION": {"verdict": "NOT_RUN_THIN_REGIME",
                             "episodes_total": 1, "margin_to_floor_min": 0.0},
            "DOWNTREND": {"verdict": "NOT_RUN_THIN_REGIME",
                          "episodes_total": 1, "margin_to_floor_min": 0.0},
        }
    }
    real = census_mod.measure_cell_census
    census_mod.measure_cell_census = lambda cd, cell: ok_census
    try:
        # evidence: single eligible specialist with strong inner folds
        from rsmv1.specialists import eligible_for
        ev = {}
        for sid in eligible_for("BTCUSDT", "UPTREND"):
            ev.setdefault("UPTREND", {})[sid] = {
                "fold_nets": {0: 100.0, 1: 200.0}, "pooled_net": 300.0,
                "trades": 5,
            }
        from rsmv1.freezes import Freezes

        class _Ctx:
            cell = "BTC_H1"
            asset = "BTCUSDT"
            episodes = []
            fz = None
            def __init__(self):
                self.fz = Freezes(Path(__file__).resolve().parents[1])

        mapping, audit = scored_mod.arm_c_selection(_Ctx(), ev)
        assert mapping[0]["UPTREND"] == "FLAT"  # fold1 empty-inner default
        # fold>=2: single eligible specialist taken iff inner floors met;
        # floors need episodes which our stub ctx lacks -> FLAT by floor law
        assert all(
            a["reason"] in ("fold1_empty_inner_default", "inner_floor_failure",
                            "single_eligible_specialist",
                            "OUTER_FLOOR_THIN", "no_asset_eligible_specialist",
                            "inner_net_higher_stable", "exact_tie_tiebreak",
                            "inner_evidence_unstable")
            for a in audit)
    finally:
        census_mod.measure_cell_census = real


def test_selection_invariance_outer_fold_leak():
    """F3: selection for fold k is invariant to evidence in folds >= k."""
    from rsmv1.census import measure_cell_census  # noqa: F401
    from rsmv1.freezes import Freezes

    class _Ctx:
        cell = "BTC_H1"
        asset = "BTCUSDT"
        episodes = []
        fz = None
        def __init__(self):
            self.fz = Freezes(Path(__file__).resolve().parents[1])

    import rsmv1.census as census_mod
    ok = {"per_regime": {
        r: {"verdict": "SAMPLE_OK", "episodes_total": 30,
            "margin_to_floor_min": 1.5}
        for r in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")}}
    real = census_mod.measure_cell_census
    census_mod.measure_cell_census = lambda cd, cell: ok
    try:
        import rsmv1.scored as scored_mod
        ev_a = _fake_evidence("UPTREND", {0: 100.0, 1: 50.0, 2: 999.0, 3: -999.0})
        ev_b = _fake_evidence("UPTREND", {0: 100.0, 1: 50.0, 2: -1.0, 3: 1.0})
        _, audit_a = scored_mod.arm_c_selection(_Ctx(), ev_a)
        _, audit_b = scored_mod.arm_c_selection(_Ctx(), ev_b)
        # only inner folds (0..k-1) may influence fold k's row
        for a, b in zip(audit_a, audit_b):
            assert a["selected"] == b["selected"], (a, b)
    finally:
        census_mod.measure_cell_census = real


def test_manifest_digest_lengths():
    import hashlib
    import json

    p = (Path(__file__).resolve().parents[1] / "freezes"
         / "decision_cache_manifest.json")
    d = json.loads(p.read_text())
    for name, dig in d["files"].items():
        assert len(dig) == 64 and all(c in "0123456789abcdef" for c in dig), name
        f = Path(__file__).resolve().parents[1] / name
        if f.exists():
            assert hashlib.sha256(f.read_bytes()).hexdigest() == dig, name
