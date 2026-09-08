"""STOCKS_FREEZE_PASS gate contract (PLAN_stocks.md section 15).

Validates the S2->S3 selection freeze: exactly two selected families, six
unique arm keys, immutable spec hashes matching on-disk bytes, budget 0/6,
A7 eligibility for both selections, and the explicit blocked-data verdict.
A1 owns this file; A7 verifies independently.
"""
import hashlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
FREEZE = REPO / "research/control/stocks_run/selection_freeze.json"
A7_VERDICTS = REPO / "research/audits/stocks/s3_a7/verdict_summary.json"

EXPECTED_FAMILIES = {
    "EQ_S2_A3_F1_PIT_RECON_FLOW",
    "A5-S2-F1-LENDING-CONSTRAINT-PREMIUM",
}


def _load(path):
    with open(path) as f:
        return json.load(f)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_freeze_file_exists_and_is_valid_json():
    assert FREEZE.is_file()
    assert isinstance(_load(FREEZE), dict)


def test_exactly_two_selected_families():
    families = _load(FREEZE)["selected_families"]
    assert len(families) == 2
    assert {f["family_id"] for f in families} == EXPECTED_FAMILIES


def test_six_unique_arm_keys_three_per_family():
    families = _load(FREEZE)["selected_families"]
    keys = []
    for fam in families:
        assert fam["arm_keys"] == ["anchor", "neighbour", "control"]
        assert fam["max_trials"] == 3
        keys.extend(f"{fam['family_id']}::{arm}" for arm in fam["arm_keys"])
    assert len(keys) == 6
    assert len(set(keys)) == 6


def test_proposal_spec_hashes_match_on_disk_bytes():
    for fam in _load(FREEZE)["selected_families"]:
        spec = REPO / fam["proposal_spec"]
        assert spec.is_file(), fam["proposal_spec"]
        assert _sha256(spec) == fam["proposal_spec_sha256"], fam["family_id"]


def test_budget_is_zero_six_and_counters_zero():
    budget = _load(FREEZE)["budget"]
    assert budget["planned_cells"] == 6
    assert budget["computed"] == 0
    assert budget["published"] == 0
    assert budget["observed"] == 0


def test_multiasset_core_sha_frozen():
    hashes = _load(FREEZE)["immutable_hashes"]
    assert hashes["MULTIASSET_CORE_SHA"] == (
        "83103666fea21a569d04bef2239ec0bda7784beb")


def test_a7_eligible_for_both_selected():
    verdicts = _load(A7_VERDICTS)
    entries = verdicts.get("proposals") or verdicts.get("families") or verdicts
    by_id = {}
    if isinstance(entries, dict):
        by_id = entries
    else:  # list of records
        for rec in entries:
            fid = rec.get("family_id") or rec.get("proposal_id") or rec.get("id")
            by_id[fid] = rec
    for fid in EXPECTED_FAMILIES:
        assert fid in by_id, fid
        rec = by_id[fid]
        verdict = json.dumps(rec).lower()
        assert "eligible" in verdict and "ineligible" not in verdict.replace(
            "ineligible: no", "eligible: no"), fid


def test_scored_research_blockingly_unavailable_and_declared():
    blocked = _load(FREEZE)["blocked"]
    assert blocked["scored_research"] == "STOCKS_BLOCKED_DATA_AUTHORITY"
    assert blocked["reason"]


def test_window_policy_honestly_not_frozen():
    wp = _load(FREEZE)["window_policy"]
    assert wp["status"] == "NOT_FROZEN_NO_REAL_DATA"
    assert wp["rule"]


def test_every_non_selected_family_has_recorded_reason():
    reasons = {r["family_id"]: r["reason"] for r in _load(FREEZE)["not_selected"]}
    assert len(reasons) == 4
    assert all(reasons.values())


@pytest.mark.parametrize("arm", ["anchor", "neighbour", "control"])
def test_both_families_declare_each_arm_role(arm):
    for fam in _load(FREEZE)["selected_families"]:
        assert arm in fam["arm_keys"], (fam["family_id"], arm)
