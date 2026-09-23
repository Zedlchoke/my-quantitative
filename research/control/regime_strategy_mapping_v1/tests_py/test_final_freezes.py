"""Final freeze integrity: digests, pins, and code<->freeze constant equality."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FZ = Path(__file__).resolve().parents[1] / "freezes"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_manifest_lists_and_matches_every_frozen_file():
    m = json.loads((FZ / "rsmv1_freeze_manifest.json").read_text())
    for name, digest in m["files"].items():
        assert _sha(FZ / name) == digest, f"freeze digest mismatch: {name}"


def test_specialist_library_pinned_and_bounded():
    w = json.loads((FZ / "specialist_library_freeze.json").read_text())
    prop = json.loads((FZ / "specialist_library_proposal.json").read_text())
    assert w["status"] == "FROZEN"
    assert w["parameter_source_of_truth"]["sha256"] == _sha(
        FZ / "specialist_library_proposal.json")
    assert w["bounds"]["total_specialists"] == 6
    assert w["bounds"]["max_specialists_per_regime"] == 2
    per_regime = {r: len(v["specialists"]) for r, v in prop["regimes"].items()}
    assert all(n <= 2 for n in per_regime.values())
    assert "TRANSITION_UNKNOWN" not in prop["regimes"]


def test_arms_freeze_pins_match_v2_and_budget_21():
    a = json.loads((FZ / "rsmv1_arms_freeze.json").read_text())
    assert a["status"] == "FROZEN"
    assert a["trial_budget"]["scored_cells"] == 21
    assert a["trial_budget"]["scored_arm_instance_ids"] == [
        "A1", "A2", "B", "C", "D", "E", "F"]
    pins = a["v2_reference_pins"]["b_engine_equivalence_v2_jev_only_tier1_totals_per_cell"]
    assert round(pins["BTC_H1"]["net"], 2) == -88140.39
    assert round(pins["BTC_H4"]["net"], 2) == -85274.07
    assert round(pins["SPY_D1"]["net"], 2) == -51623.26
    assert pins["BTC_H1"]["trades"] == 978
    assert pins["BTC_H4"]["trades"] == 1060
    assert pins["SPY_D1"]["trades"] == 343
    assert a["v2_reference_pins"]["v2_trade_count_pins"] == {
        "BTC_H1": 978, "BTC_H4": 1060, "SPY_D1": 343}


def test_code_constants_equal_frozen_laws():
    from rsmv1.selection import INNER_DECISION_FLOOR, INNER_EPISODE_FLOOR
    from rsmv1.turnover import BUFFER_REGIME_BARS, v2_jev_only_trade_cap
    sel = json.loads((FZ / "rsmv1_selection_freeze.proposal.json").read_text())
    assert INNER_EPISODE_FLOOR == 5 and INNER_DECISION_FLOOR == 150
    assert BUFFER_REGIME_BARS == 1
    assert v2_jev_only_trade_cap("BTC_H1") == 978
    assert v2_jev_only_trade_cap("BTC_H4") == 1060
    assert v2_jev_only_trade_cap("SPY_D1") == 343


def test_evaluation_vocabulary_exact():
    e = json.loads((FZ / "rsmv1_evaluation_freeze.proposal.json").read_text())
    vocab = e["verdict_vocabulary"]["allowed_values_exactly"]
    assert set(vocab) == {
        "DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION",
        "NO_REGIME_STRATEGY_INCREMENTAL_VALUE",
        "BLOCKED_THIN_REGIME_SAMPLE",
        "BLOCKED_COST_OR_CONTROL_AUTHORITY",
        "TECHABORT",
    }


def test_go_quarantine_phrase_matches_registry():
    import subprocess

    out = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1]
                             / "tools" / "cmd_scored.py"), "--check"],
        capture_output=True, text=True, check=True)
    st = json.loads(out.stdout)
    assert st["go_phrase_sha256_expected"] == hashlib.sha256(
        "GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST".encode()).hexdigest()
    assert st["authorized"] is False  # no token pre-GO
