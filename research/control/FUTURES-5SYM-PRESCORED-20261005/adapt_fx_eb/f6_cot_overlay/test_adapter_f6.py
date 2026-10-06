"""F6 overlay tests — machinery-only: strata split (>=80/<=20/mid negative), 6B
falsifier posture, no-own-signal law, evidence refusal, PB2 refusal."""
import copy

from fx_common import RefusedPendingEvidence, RefusedPendingOwnerDecision
from conftest import load_fixture
from f6_cot_overlay import adapter as f6

import pytest


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_fixture("f6_cot_overlay", f"panel_{sym}.json")
              for sym in ("6E", "6B")}
    series = {sym: load_fixture("f6_cot_overlay", f"series_{sym}.json")["series"]
              for sym in ("6E", "6B")}
    expected = load_fixture("f6_cot_overlay", "EXPECTED_MANIFEST.json")["expected"]
    return panels, series, expected


def test_strata_split_boundaries(ctx):
    panels, series, expected = ctx
    obs = f6.build_observables(panels["6E"], {}, "6E", series["6E"])
    for dt, want in expected["strata"].items():
        assert obs["strata"][dt]["stratum"] == want, dt
    # boundary law: 80 is HIGH (>=80), 20 is LOW (<=20), 50 mid = negative
    assert obs["strata"]["2026-04-10"]["stratum"] == "HIGH"    # 80
    assert obs["strata"]["2026-04-03"]["stratum"] == "LOW"     # 20
    assert obs["strata"]["2026-03-20"]["stratum"] == "MID_NEGATIVE"
    assert obs["standalone_identities"] == 0


def test_6b_is_measured_falsifier_not_a_leg(ctx):
    panels, series, expected = ctx
    obs = f6.build_observables(panels["6B"], {}, "6B", series["6B"])
    assert obs["falsifier"] == expected["falsifier_6B"]
    assert obs["conditioning_value"].startswith("NONE")
    sig = f6.signal(obs, "2026-03-06", {}, "6B", {}, panels["6B"])
    assert sig["status"] == "NO_TRADE"
    assert sig["blocking"] == ["OVERLAY_NO_OWN_SIGNAL"]


def test_no_own_signal_and_ancestry_fence(ctx):
    panels, series, _ = ctx
    obs = f6.build_observables(panels["6E"], {}, "6E", series["6E"])
    sig = f6.signal(obs, "2026-03-06", {}, "6E", {}, panels["6E"])
    assert sig["status"] == "NO_TRADE"
    assert sig["host_stratum"] == "HIGH"
    assert "107-109" in sig["ancestry_fence"]


def test_evidence_gate_refusal():
    with pytest.raises(RefusedPendingEvidence) as ei:
        f6.require_f6_evidence()
    assert ei.value.item == "F6_INTRADAY_TRANSFER_NOT_RUN"
    assert "meas_fx/meas_fx_m2_transfer_harness.py" in ei.value.detail


def test_pb2_refusal_real_data_path(ctx):
    panels, series, _ = ctx
    panel = copy.deepcopy(panels["6E"])
    panel["provenance"] = "REAL_6E_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        f6.build_observables(panel, {}, "6E", series["6E"])
    assert ei.value.slot_id == "P5-FXEB-OD1"
